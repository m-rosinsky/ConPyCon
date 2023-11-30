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

class CommandNoFuncError(CommandError):
    """
    Brief:
        This error is raised if a command does not have a 'name' field.
    """
    def __init__(self, name: str):
        self.message = f"Command '{name}' does not contain a 'func' parameter"
        super().__init__(self.message)
