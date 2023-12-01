"""
File:
    conpycon/console.py

Brief:
    This file contains the Console class, which clients use to
    instantiate a new console object.
"""

import sys
import yaml

from conpycon.command import Command
from conpycon.error import *
from conpycon.get_key import get_key, Key

# Default banner and prompt for a Console.
DEFAULT_BANNER = None
DEFAULT_PROMPT = '> '

MAX_CMD_LEN = 1024
MAX_HIST_LEN = 20

class Console:
    """
    Brief:
        This class defines a console instance. It loads a YAML file
        with the command hierarchy, and takes various operational parameters.

        This class offers a command loop which will continually prompt
        the client for commands.

    Raises:
        CommandError on errors parsing the command file.
    """
    def __init__(self, command_file, cmd_list,
                 banner=DEFAULT_BANNER,
                 prompt=DEFAULT_PROMPT):
        # Synthesize the symbol table.
        self.symbol_table = {}
        for cmd in cmd_list:
            self.symbol_table[cmd.__name__] = cmd

        # Parse the YAML.
        self._cmd_tree = self._parse_command_file(command_file)

        self.banner = banner
        self.prompt_str = prompt
        self.is_running = False

    def run(self):
        """
        Brief:
            This function initiates the command loop for the console.
        """
        # Display the banner.
        print(self.banner)

        self.is_running = True

        while self.is_running:
            # Prompt user for command.
            try:
                cmd_str = self._prompt()
            except KeyboardInterrupt:
                print("^C")
                break

            # Handle the command.
            print(cmd_str)

    def _prompt(self) -> str:
        """
        Brief:
            This function prompts for a single command.

        Returns:
            The command string.

        Raises:
            KeyboardInterrupt for CTRL-C
        """
        # The current command.
        cmd = ""
        # The position within the current command.
        cmd_idx = 0
        # A copy of the current command if the user begins scrolling through
        # command history.
        cmd_cpy = ""

        # Display the prompt.
        print(self.prompt_str, end='')

        # Input processing loop.
        while True:
            sys.stdout.flush()

            inp = get_key()

            # Unrecognized characters are ignored.
            if inp == None:
                continue

            # Keyboard interrupt.
            if inp == Key.CTRL_C:
                raise KeyboardInterrupt
            
            # Return.
            if inp == Key.RETURN:
                print("")
                break

            # Backspace.
            if inp == Key.BACKSPACE:
                # Bounds check.
                if cmd_idx == 0:
                    continue

                # Move cursor back one.
                print("\b", end="")

                # Print all following characters.
                for i in range(cmd_idx, len(cmd)):
                    print(cmd[i], end="")

                # Print a space at the end to clear the last character.
                print(" ", end="")

                # Return cursor to position.
                for _ in range(cmd_idx, len(cmd)):
                    print("\b", end="")
                print("\b", end="")

                # Decrement index.
                cmd_idx -= 1

                # Slice the string.
                cmd = cmd[:cmd_idx] + cmd[cmd_idx + 1:]
                continue

            # Tab Completions.
            if inp == Key.TAB:
                continue

            # Up arrow.
            if inp == Key.UP:
                continue

            # Down arrow.
            if inp == Key.DOWN:
                continue

            # Right arrow.
            if inp == Key.RIGHT:
                # Upper bounds check.
                if cmd_idx >= len(cmd):
                    continue

                print(cmd[cmd_idx], end="")
                sys.stdout.flush()
                cmd_idx += 1
                continue

            # Left arrow.
            if inp == Key.LEFT:
                # Lower bounds check.
                if cmd_idx == 0:
                    continue

                print("\b", end="")
                cmd_idx -= 1
                continue

            # Bound check for max length.
            if len(cmd) >= MAX_CMD_LEN:
                continue

            print(inp, end="")

            # Insert charccter into cmd buffer.
            cmd = cmd[:cmd_idx] + inp + cmd[cmd_idx:]
            cmd_idx += 1

            # Print all characters that follow in buffer.
            for i in range(cmd_idx, len(cmd)):
                print(cmd[i], end="")

            # Return cursor.
            for _ in range(cmd_idx, len(cmd)):
                print("\b", end="")

        return cmd

    def _parse_command_file(self, command_file: str) -> list:
        """
        Brief:
            This function parses the provided command YAML file and forms
            a tree of Command classes.

        Arguments:
            command_file: str
                The path to the YAML command file.

        Returns: Command
            A list of Command classes.

        Raises:
            OSError on error interacting with 'command_file'
        """
        try:
            yaml_data = self._load_yaml(command_file)
        except OSError:
            raise

        # Assert that the 'commands' section exists.
        if yaml_data is None or 'commands' not in yaml_data:
            raise CommandNoCommandsError(command_file)
        
        # Assert the 'commands' section contains a dictionary of data.
        command_data = yaml_data['commands']
        if not isinstance(command_data, dict):
            raise CommandInvalidTypeError('commands', 'dict', type(command_data).__name__)

        # Create Command classes for each command in 'commands' section.
        com_list = []
        for name, data in yaml_data['commands'].items():
            com = self._create_command(name, data)
            com_list.append(com)

        return com_list

    def _create_command(self, name: str, data: dict) -> Command:
        """
        Brief:
            This function creates a Command class from
            the YAML data under the command header.

        Arguments:
            name: str
                The name of the command.

            data: dict
                The YAML data

        Returns: Command
            The Command class.
        """
        # Get the command func.
        if data is None or 'func' not in data:
            raise CommandNoFuncError(name)
        
        # Assert command func is of type string.
        func_name = data['func']
        if not isinstance(func_name, str):
            raise CommandInvalidTypeError('func', 'str', type(func_name).__name__)

        # Find function within globals to attach command string to.
        if func_name in self.symbol_table and callable(self.symbol_table[func_name]):
            func = self.symbol_table[func_name]
        else:
            raise CommandFuncNotFound(name, func_name)

        com = Command(name, func)
        return com

    def _load_yaml(self, file: str) -> dict:
        """
        Brief:
            This function reads in a file and uses the yaml module
            to create a dictionary.

        Arguments:
            file: str
                The path to the YAML file.

        Returns:
            Dictionary of parsed YAML data.

        Raises:
            OSError on error opening 'file'.
        """
        # Open the command YAML file.
        try:
            with open(file, 'r', encoding='utf-8') as yf:
                file_data = ""
                for line in yf:
                    file_data += line

                yaml_data = yaml.safe_load(file_data) or {}
        except OSError:
            # Propagate to caller.
            raise

        return yaml_data
