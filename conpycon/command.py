"""
File:
    conpycon/command.py

Brief:
    This file contains the Command class.
"""

class Command:
    """
    Brief:
        This class is created dynamically by a Console class, as it parses
        commands from the command file.

        Each command and subcommand will be processed into one of these
        classes.
    """
    def __init__(self, name: str, func):
        self.name = name
        self.func = func
        self.subcommands = []
