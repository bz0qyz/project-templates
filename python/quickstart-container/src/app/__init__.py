"""
Application object for basic application information and command-line arguments and logging
"""
import os
import datetime
import logging
import logging.config
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
from dataclasses import dataclass
from importlib import metadata
from packaging.version import Version, parse
from .config import LOGGING_CONFIG
from .constants import BASE_DIR, LOG_LEVELS, LOG_FORMATS, DATE_FORMAT
from .arguments import Arguments
init_log: list[tuple[int, str]] = [] 

class App:
    """ Base application configuration """
    # Must match pyproject.toml
    PROJECT_NAME = "quickstart-container"
    
    def __init__(self) -> None:
        # Set applcation defalts
        # print(metadata.distribution(self.PROJECT_NAME)._path)

        # initialize application metadata
        self.meta = AppMetadata(self.PROJECT_NAME, static_dir=f"{BASE_DIR}/static")
        init_log.append((INFO, f"Initializing application: {self.meta.name} v{self.meta.version} [license: {self.meta.license}]"))
        self.base_dir = BASE_DIR
        init_log.append((DEBUG, f"Base directory set to: {self.base_dir}"))
        
        # initialize application arguments
        self.args = Arguments(self).args
        
        # initialize logging options
        self.logger_config = LoggerConfig(self.args, logger_name=self.meta.name)

        # Setup logger
        self.logger = self._setup_logger()

        # Flush init log messages
        for lvl, txt in init_log:
            self.logger.log(lvl, txt)
        init_log.clear()

    @property
    def name(self) -> str:
        """ Application name """
        return self.meta.name
    @property
    def version(self) -> Version:
        """ Application version """
        return self.meta.version

    def _setup_logger(self) -> logging.Logger:
        """ Setup the application logger """
        log_level = logging.getLevelName(self.logger_config.level.upper())

        # customize the logging configuration
        logging_config = LOGGING_CONFIG.copy()

        logging_config["loggers"][self.logger_config.name] = logging_config["loggers"]["app"]
        del(logging_config["loggers"]["app"])

        for key, config in logging_config["loggers"].items():
            config["level"] = self.logger_config.level.upper()
        
        logging_config["root"]["level"] = self.logger_config.level.upper()
        logging_config["handlers"]["default"]["formatter"] = self.logger_config.format
        logging_config["handlers"]["default"]["level"] = self.logger_config.level.upper()
        logging.config.dictConfig(logging_config)

        logger = logging.getLogger(self.logger_config.name)
        logger.setLevel(self.logger_config.level.upper())

        return logger

class AppMetadata:
    """ Application metadata dataclass """
    def __init__(self, project_name: str, static_dir: str) -> None:
        meta = metadata.metadata(project_name)
        self.name = meta["Name"]
        self.version = Version(meta["Version"])
        self.description = meta["Summary"]
        self.author = meta["Author-email"]
        self.license = meta["License-Expression"]
        self.static_dir = static_dir
        self.copyright = f"\u00A9 {datetime.datetime.today().year} {self.author}"
        self.footer = f"{self.name} | {self.copyright}"

      
class LoggerConfig:
    """ Logging options dataclass """
    def __init__(self, args: Arguments, logger_name: str) -> None:
        self.name = logger_name
        self.debug = False
        self.level = args.log_level if args.log_level in LOG_LEVELS else "info"
        self.format = args.log_format if args.log_format in LOG_FORMATS else "default"
        # if the log level is debug, force the log format to debug
        if self.level == "debug":
            self.debug = True
            # self.format = "debug"

