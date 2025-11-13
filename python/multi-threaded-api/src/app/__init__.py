"""
Application object for basic application information and command-line arguments and logging
"""
import logging
import os
import sys
from packaging.version import Version, parse
from .config import AppConfig
from .arguments import Arguments

class App:
    """ Base application configuration """
    def __init__(self):
        self.config = AppConfig
        self.name = self.config.name
        self.version = Version(self.config.version)
        self.args = Arguments(self).args
        

