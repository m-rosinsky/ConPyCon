"""
File:
    conpycon/error.py

Brief:
    This file contains error types for conpycon.
"""

""" Command Errors """

class CommandError(BaseException):
    """
    Brief:
        This base exception for command related errors.
    """
    pass

class CommandInvalidTypeError(CommandError):
    """
    Brief:
        This error is raised if an incorrect datatype is provided for a
        section of the command file.
    """
    def __init__(self, name: str, good_type: str, bad_type: str):
        self.message = f"Section '{name}' expects type '{good_type}'. Received type '{bad_type}'"
        super().__init__(self.message)

class CommandNoCommandsError(CommandError):
    """
    Brief:
        This error is raised if there is no 'commands' section in the
        command file.
    """
    def __init__(self, fname: str):
        self.message = f"Command file '{fname}' does not contain a 'commands' section"
        super().__init__(self.message)

class CommandNoFuncError(CommandError):
    """
    Brief:
        This error is raised if there is no 'func' section in a command.
    """
    def __init__(self, name: str):
        self.message = f"Command '{name}' does not contain a 'func' parameter"
        super().__init__(self.message)

class CommandFuncNotFound(CommandError):
    """
    Brief:
        This error is raised if the function specified in the 'func' section
        does not exist.
    """
    def __init__(self, cmd_name: str, func_name: str):
        self.message = f"In command '{cmd_name}': func '{func_name}' does not exist"
        super().__init__(self.message)
