"""
Application object for basic application information and command-line arguments and logging
"""
import logging
import os
import sys
import datetime
from dataclasses import dataclass
from importlib import metadata
from packaging.version import Version, parse
from .constants import BASE_DIR, LOG_LEVELS, LOG_FORMATS
from .arguments import Arguments

class App:
    """ Base application configuration """
    # Must match setup.py and pyproject.toml
    PROJECT_NAME = "multi-threaded-api"
    
    def __init__(self):
        self.meta = metadata.metadata(self.PROJECT_NAME)
        self.name = self.meta["Name"]
        self.version = Version(self.meta["Version"])
        self.description = self.meta["Summary"]
        self.author = self.meta["Author-email"]
        self.license = self.meta["License-Expression"]
        self.copyright = f"\u00A9{datetime.datetime.today().year} {self.author}"
        self.footer = f"{self.name} | {self.copyright}"
        self.base_dir = BASE_DIR
        self.args = Arguments(self).args
        self.log_opts = LogOptions(self.args)
        self.tls_opts = TlsOptions(self.args)
        self.cpu_cores = os.cpu_count() if os.cpu_count() is not None else 1
        
        # Setup logger
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """ Setup the application logger """
        logger = logging.getLogger(self.name)
        log_level = logging.getLevelName(self.log_opts.level.upper())
        logger.setLevel(log_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            fmt=self.log_opts.format,
            datefmt=self.log_opts.date_format
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger


class LogOptions:
    """ Logging options dataclass """
    def __init__(self, args: Arguments):
        self.date_format = "%Y-%m-%d %H:%M:%S"
        self.level = args.log_level if args.log_level in LOG_LEVELS else "info"
        self.access_log = not args.no_access_log if hasattr(args, 'no_access_log') else True

        self.format_key = args.log_format if args.log_format in LOG_FORMATS.keys() else "default"
        # if the log level is debug, force the log format to debug
        if self.level == "debug":
            log_format_key = "debug"
        self.format = LOG_FORMATS[self.format_key]

class TlsOptions:
    """ TLS options dataclass """
    def __init__(self, args: Arguments):
        self.auto = args.tls_auto if hasattr(args, 'tls_auto') else False
        self.cert = args.tls_cert if hasattr(args, 'tls_cert') else None
        self.key = args.tls_key if hasattr(args, 'tls_key') else None
        self.ca = args.tls_ca if hasattr(args, 'tls_ca') else None
        self.enabled = self.auto or (self.cert is not None and self.key is not None)