"""
File:
    conpycon/console.py

Brief:
    This file contains the Console class, which clients use to
    instantiate a new console object.
"""

import yaml

from conpycon.command import Command
from conpycon.error import *

# Default banner and prompt for a Console.
DEFAULT_BANNER = None
DEFAULT_PROMPT = '> '

class Console:
    """
    Brief:
        This class defines a console instance. It loads a YAML file
        with the command hierarchy, and takes various operational parameters.

        This class offers a command loop which will continually prompt
        the client for commands.
    """
    def __init__(self, command_file,
                 banner=DEFAULT_BANNER,
                 prompt=DEFAULT_PROMPT):
        # Parse the command file.
        self._cmd_tree = self._parse_command_file(command_file)

    def _parse_command_file(self, command_file: str) -> Command:
        """
        Brief:
            This function parses the provided command YAML file and forms
            a tree of Command classes.

        Arguments:
            command_file: str
                The path to the YAML command file.

        Returns: Command
            The root node of the command tree.

        Raises:
            OSError on error interacting with 'command_file'
        """
        try:
            yaml_data = self._load_yaml(command_file)
        except OSError:
            raise

        # Find commands.
        for name, data in yaml_data.items():
            com = self._create_command(name, data)

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
        cmd_func = data['func']

        print(f"Got command {name} with func '{cmd_func}'")

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
