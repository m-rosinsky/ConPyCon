"""
File:
    conpycon/console.py

Brief:
    This file contains the Console class, which clients use to
    instantiate a new console object.
"""

import shlex
import sys
import yaml

from conpycon.command_tree import CommandNode
from conpycon.exceptions import *
from conpycon.get_key import get_key, Key

# Default banner and prompt for a Console.
DEFAULT_BANNER = ''
DEFAULT_PROMPT = '> '
DEFAULT_EXIT = ''

# Prompt and history lengths.
MAX_CMD_LEN = 1024
MAX_HIST_LEN = 20

# YAML section names.
SECTION_COMMANDS = 'commands'
SECTION_ACTION = 'action'
SECTION_SUBCOMMANDS = 'subcommands'

def _lcp(l: list) -> str:
    """
    Brief:
        This is a helper function to find the longest common prefix
        of a list of strings.
    """
    if not l:
        return ""
    
    min_l = min(len(s) for s in l)

    for i in range(min_l):
        if not all(s[i] == l[0][i] for s in l):
            return l[0][:i]
        
    return l[0][:min_l]

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
    def __init__(self, command_file, actions,
                 banner=DEFAULT_BANNER,
                 prompt=DEFAULT_PROMPT,
                 exit_msg=DEFAULT_EXIT):
        # Synthesize the symbol table.
        self.symbol_table = {}
        for action in actions:
            self.symbol_table[action.__name__] = action

        # The _parsers object is an array of argparse parsers for each
        # top-level command specified in the YAML. This will be populated
        # in the _parse_yaml function.
        self._parsers = []

        # Parse the YAML.
        # This returns a CommandNode that is a tree of strings used in
        # autocompletion, since argparse does not allow its subparsers
        # to be accessed directly.
        self._root_node = self._parse_yaml(command_file)

        # Console variables.
        self.banner = banner
        self.prompt_str = prompt
        self.exit_msg = exit_msg
        self.is_running = False

        # Console history.
        self.history = []

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
            if cmd_str is not None:
                cmd_str = cmd_str.strip()

            # Check for empty command.
            if len(cmd_str) == 0:
                continue

            # If this command matches the last entered command, don't
            # push to history.
            if len(self.history) == 0 or self.history[0] != cmd_str:
                self.history.insert(0, cmd_str)
                if len(self.history) > MAX_HIST_LEN:
                    self.history.pop()

            # Split the string.
            try:
                cmd_parse = shlex.split(cmd_str)
            except ValueError:
                continue

            # Special case for exit commands.
            if cmd_parse[0].upper() in ["EXIT", "QUIT", "Q"]:
                break

            # Dispatch parse.
            try:
                self._dispatch(cmd_parse)
            except DispatchError as e:
                print(f"[\033[31mError\033[0m] {e}")

        # Exit.
        print(self.exit_msg)

    def _parse_yaml(self, file: str) -> CommandNode:
        """
        Brief:
            This function parses the command YAML file and returns
            a root Command class node.

            The root node is a blank command used to house all
            root-level commands as subcommands.

            This function also builds out the argparse tree.

        Raises:
            YAMLError on errors opening/reading the YAML file.

            CommandError on invalid formatting of the YAML file.
        """
        # Load YAML data.
        try:
            yaml_data = self._load_yaml(file)
        except OSError:
            raise YAMLError
        
        # Get 'commands' section
        if yaml_data is None or SECTION_COMMANDS not in yaml_data:
            raise CommandNoCommandsError
        
        # Type checking.
        command_section = yaml_data[SECTION_COMMANDS]
        if not isinstance(command_section, dict):
            raise CommandInvalidTypeError(SECTION_COMMANDS, 'dict', type(command_section).__name__)
        
        # Create an empty root node for the command tree. The children of
        # the blank root node hold the top level commands.
        root_node = CommandNode("")

        # For each command in the command section of the YAML, create a
        # parser, and an entry in the command tree.
        for cmd_name, cmd_data in command_section.items():
            cmd_node, cmd_parser = self._parse_command(cmd_name, cmd_data)
            self._parsers.append(cmd_parser)
            root_node.add_child(cmd_node)

        # Return the root node.
        return root_node

    def _parse_command(self,
                       cmd_name: str,
                       cmd_data: dict) -> (CommandNode, argparse.ArgumentParser):
        """
        Brief:
            This function creates a node for the command tree and a parser
            for a command in the YAML.

        Arguments:
            cmd_name: str
                The name of the command
            cmd_data: dict
                The command YAML data.

        Returns: (CommandNode, argparse.ArgumentParser)
            A tuple of the node and argparse parser for the command.
        """
        # Create the command node.
        cmd_node = CommandNode(cmd_name)

        # Create the argument parser.
        cmd_parser = argparse.ArgumentParser(
            prog=cmd_name,
            add_help=False,
        )
        cmd_parser.add_argument(
            '-h',
            '--help',
            action='help',
            default=argparse.SUPPRESS,
            help='Show this help message',
        )
        cmd_usage = cmd_parser.format_usage().split(':')[1].strip()
        cmd_parser.usage = cmd_usage

        # Assert there is an 'action' section, and that it is a str.
        if cmd_data is None or SECTION_ACTION not in cmd_data:
            raise CommandNoActionError(cmd_name)

        cmd_action = cmd_data[SECTION_ACTION]
        if not isinstance(cmd_action, str):
            raise CommandInvalidTypeError(SECTION_ACTION, 'str', type(cmd_action).__name__)
        
        action = self.symbol_table.get(cmd_action)
        if action is None:
            raise CommandActionNotFound(cmd_name, cmd_action)

        cmd_parser.set_defaults(action=action)
        return (cmd_node, cmd_parser)

    def _dispatch(self, cmd_parse: list):
        """
        Brief:
            This function dispatches an action for a given parse of a command.

        Arguments:
            cmd_parse: list
                The parsed command.

        Raises:
            DispatchError on errors.
        """
        # Check that the command name exists.
        cmd_parser = None
        for cmd in self._parsers:
            if cmd.prog == cmd_parse[0]:
                cmd_parser = cmd

        if cmd_parser is None:
            raise DispatchNotFoundError(cmd_parse[0])
        
        # Call the parser.
        try:
            args = cmd_parser.parse_args(cmd_parse[1:])
        except SystemExit:
            print(f"[\033[31mError\033[0m] {cmd_parser.error_msg}")
            print(f"[\033[36mUsage\033[0m] {cmd_parser.usage}")
            print("[\033[36mPositionals\033[0m]", end="")
            for arg in cmd_parser._action_groups:
                print(arg._group_actions)
                for a in arg._group_actions.option_strings:
                    print(a)
            return
        
        # Call the action.
        args.action()

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

        # History index tracks which historical command we are searching.
        # -1 for "not searching".
        hist_idx = -1

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
                parse = shlex.split(cmd)
                if len(cmd) > 0 and cmd[len(cmd) - 1] == " " and cmd_idx == len(cmd):
                    parse.append("")
                
                # Check for empty command.
                if parse is None or len(parse) == 0:
                    continue

                # Node for the tree structure.
                cur_node = self._root_node

                for token in parse:
                    match_nodes = [c for c in cur_node.children if c.name.startswith(token)]

                    # Check for no matches.
                    if not match_nodes:
                        break

                    # Traverse tree.
                    cur_node = match_nodes[0]

                # If there are no matches returned, do nothing.
                if not match_nodes:
                    continue

                # If there is only one match returned, we can autofill.
                if len(match_nodes) == 1:
                    parse[len(parse) - 1] = match_nodes[0].name
                    for _ in range(cmd_idx):
                        print("\b", end="")
                    cmd = shlex.join(parse) + " "
                    cmd_idx = len(cmd)
                    print(cmd, end="")
                    continue

                # If there are multiple matches, list them.
                print("")
                for node in match_nodes:
                    print(node.name, end="\t")

                # Find the longest common prefix and auto-fill.
                match_names = [node.name for node in match_nodes]
                fill = _lcp(match_names)
                if len(fill) > 0:
                    parse[len(parse) - 1] = fill
                    cmd = shlex.join(parse)
                cmd_idx = len(cmd)
                print(f"\n{self.prompt_str}{cmd}", end="")
                continue

            # Up arrow.
            if inp == Key.UP:
                # Upper bounds check.
                if hist_idx + 1 >= len(self.history):
                    continue

                hist_idx += 1

                # Create a copy of the current command buffer if this
                # is the first up arrow press.
                if hist_idx == 0:
                    cmd_cpy = cmd

                # Put cursor at end of line.
                for _ in range(cmd_idx, len(cmd)):
                    print(" ", end="")

                # Blank the line and return cursor to beginning.
                for _ in range(len(cmd)):
                    print("\b", end="")
                    print(" ", end="")
                    print("\b", end="")

                # Retreive historical command.
                cmd = self.history[hist_idx]
                cmd_idx = len(cmd)

                # Print command.
                print(cmd, end="")
                continue

            # Down arrow.
            if inp == Key.DOWN:
                # Lower bounds check.
                if hist_idx == -1:
                    continue

                hist_idx -= 1

                # Put cursor at end of line.
                for _ in range(cmd_idx, len(cmd)):
                    print(" ", end="")

                # Blank the line and return cursor to beginning.
                for _ in range(len(cmd)):
                    print("\b", end="")
                    print(" ", end="")
                    print("\b", end="")

                # Get either the saved command, or historical command.
                if hist_idx == -1:
                    cmd = cmd_cpy
                else:
                    cmd = self.history[hist_idx]

                cmd_idx = len(cmd)
                
                # Print command.
                print(cmd, end="")
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