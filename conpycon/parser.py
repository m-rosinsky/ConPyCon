"""
File:
    conpycon/parser.py

Brief:
    This file contains a module for parsing commands.

    Each command registered in the console has its own parser class which
    is called when the respective command is entered.

    It is meant to function as a modified version of Python's argparse
    library with various functionality tweaks to fit a console program
    better than a command line program.
"""

from enum import Enum
from typing import Type

################################################################################
#                               Constants                                      #
################################################################################

# Indent for messages.
_IDT = '  '

COLOR_DICT = {
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[36m',
}

################################################################################
#                               Exceptions                                     #
################################################################################

class DuplicateArgumentError(Exception):
    """
    Argument already exists within a command.
    """
    def __init__(self, name: str, cmd_name: str):
        self.msg = f"Argument with name '{name}' already exists in command '{cmd_name}'"
        super().__init__(self.msg)

################################################################################
#                               Arguments                                      #
################################################################################

class ArgumentType(Enum):
    """
    Brief:
        This class enumerates the different types of arguments that
        are supported by the command parser.
    """
    POSITIONAL = 1
    OPTIONAL = 2
    FLAG = 3

class Argument:
    """
    Brief:
        This class defines a positional argument for a command.
    """
    def __init__(self,
                 arg_type: ArgumentType,
                 name: str,
                 type: Type,
                 help: str,
                 metaname: str=None):
        self.arg_type = arg_type
        self.name = name
        self.metaname = metaname
        self.type = type
        self.help = help

################################################################################
#                               Namespace                                      #
################################################################################

class Namespace:
    """
    Brief:
        This is a class for holding attributes of a parsed command.
    """
    def __init__(self, **kwargs):
        for name in kwargs:
            setattr(self, name, kwargs[name])

    def __eq__(self, other):
        if not isinstance(other, Namespace):
            return NotImplemented
        
    def __contains__(self, key):
        return key in self.__dict__

################################################################################
#                                 Parser                                       #
################################################################################

class CommandParser:
    """
    Brief:
        This class is the main parser for a command.
    """
    def __init__(self,
                 name: str,
                 description: str=None,
                 epilog: str=None):
        # The name of the command.
        self.name = name
        self.description = description or ''
        self.epilog = epilog or ''

        # The subcommands for this command, which is a list of CommandParser
        # objects.
        self.subcommands = []

        # The arguments for the command.
        self.positionals = []
        self.optionals = []
        self.flags = []

    def add_positional(self,
                       name: str,
                       type: Type,
                       help: str):
        """
        Brief:
            This funciton adds a positional to the command parser.

            Positionals are mandatory arguments that follow
            a specific order.

        Arguments:
            name: str
                The name for the argument.

            type: Type
                The type of argument (i.e. str, int).

            help: str
                The help message for the argument.

        Raises:
            DuplicateArgumentError if positional already exists.
        """
        # Assert the argument does not already exist within the command.
        for positional in self.positionals:
            if positional.name == name:
                raise DuplicateArgumentError(name, self.name)
            
        # Add the positional.
        positional = Argument(ArgumentType.POSITIONAL, name, type, help)
        self.positionals.append(positional)

    def add_optional(self,
                     name: str,
                     type: Type,
                     help: str):
        """
        Brief:
            This function adds an optional to the command parser.

            Optionals are optional arguments that may appear
            in any order and take a variable number of parameters with them.

            Optionals are always prefixed with a double dash ('--'), even
            if they are single letters.
        
        Arguments:
            name: str
                The name for the argument.

            type: Type
                The type for the parameter (i.e. str, int)

            help: str
                The help message for the argument.

        Raises:
            DuplicateArgumentError if optional already exists.
        """
        # Assert argument does not already exist within other optionals.
        for optional in self.optionals:
            if optional.name == name:
                raise DuplicateArgumentError(name, self.name)
            
        # Add the optional.
        optional = Argument(ArgumentType.OPTIONAL, name, type, help)
        self.optionals.append(optional)

    def add_flag(self,
                 name: str,
                 metaname: str,
                 help: str):
        """
        Brief:
            This function adds a flag to the command parser.

            Flags are optional arguments that may appear in any order
            and take no parameters. Flags operate on the basis of existing
            or not.

        Arguments:
            name: str
                The name of the flag. This must be a single letter.

            metaname: str
                The name of the flag that will appear in the namespace
                after parsing.

            help: str
                The help message for the argument.
        """
        # Assert flag does not already exist within other flags.
        for flag in self.flags:
            if flag.name == name or flag.metaname == metaname:
                raise DuplicateArgumentError(name, self.name)
        
        # Add the flag.
        flag = Argument(ArgumentType.FLAG,
                        name=name,
                        type=None,
                        help=help)
        self.flags.append(flag)

    def get_usage(self) -> str:
        """
        Brief:
            This function generates the usage string for help messages.

        Returns: str
            The usage string.
        """
        usage_str = f"{self.name}"

        for positional in self.positionals:
            usage_str += f' {positional.name}'
        for optional in self.optionals:
            usage_str += f' [--{optional.name} [{optional.type.__name__}]]'
        for flag in self.flags:
            usage_str += f' [-{flag.name}]'

        return usage_str

    def print_help(self, color: str=None):
        """
        Brief:
            This function prints a help message for the command parser.
        """
        color_str = COLOR_DICT.get(color) or '\033[0m'

        # Print Description.
        print(f"{color_str}{self.name}\033[0m: {self.description}\n")

        # Print usage.
        print(f"[{color_str}Usage\033[0m]: {self.get_usage()}\n")

        # Print the positionals.
        if len(self.positionals) > 0:
            print(f"[{color_str}Positional Arguments\033[0m]:")
            for positional in self.positionals:
                print(f"{_IDT}{positional.name}\t\t{positional.help}")
            print("")

        # Print the optionals.
        if len(self.optionals) > 0:
            print(f"[{color_str}Optional Arguments\033[0m]:")
            for optional in self.optionals:
                print(f"{_IDT}--{optional.name}\t\t{optional.help}")
            print("")

        # Print the flags.
        if len(self.flags) > 0:
            print(f"[{color_str}Flags\033[0m]:")
            for flag in self.flags:
                print(f"{_IDT}--{flag.name}\t\t{flag.help}")
            print("")

        # Print the epilog.
        if self.epilog:
            print(f"{self.epilog}")
