"""
File:
    conpycon/command.py

Brief:
    This file contains the Command class.
"""

import argparse

class CommandNode:
    """
    Brief:
        This class defines a node in a command tree, which contains the
        command name and its associated subcommands as children.
    """
    def __init__(self, name: str):
        self.name = name
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def find(self, name):
        """
        Brief:
            This function finds the first child with a given name and returns
            its class. It will return the first subchild in the tree using
            a depth-first approach.
        """
        q = [self]
        while q:
            cur = q[0]
            q = q[1:]

            if cur.name == name:
                return cur
            
            for child in cur.children[::-1]:
                q.insert(0, child)

        return None
    