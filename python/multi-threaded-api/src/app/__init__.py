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
from .config import LOGGING_CONFIG
from .constants import BASE_DIR, LOG_LEVELS, LOG_FORMATS, DATE_FORMAT
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
from .arguments import Arguments
init_log: list[tuple[int, str]] = [] 

class App:
    """ Base application configuration """
    # Must match pyproject.toml
    PROJECT_NAME = "template-api"
    
    def __init__(self) -> None:
        # Set applcation defalts
        # print(metadata.distribution(self.PROJECT_NAME)._path)

        # Calculate number of fastAPI workers
        num_cpu_cores = os.cpu_count() if os.cpu_count() is not None else 1
        num_workers = (num_cpu_cores - 1)

        # initialize application metadata
        self.meta = AppMetadata(self.PROJECT_NAME, static_dir=f"{BASE_DIR}/static")
        init_log.append((INFO, f"Initializing application: {self.meta.name} v{self.meta.version} [license: {self.meta.license}]"))
        self.base_dir = BASE_DIR
        init_log.append((DEBUG, f"Base directory set to: {self.base_dir}"))
        
        # initialize application arguments
        self.args = Arguments(self).args
        
        # initialize TLS options
        self.tls_config = TlsConfig(self.args)
        init_log.append((DEBUG, f"Logging: Level: {self.args.log_level}"))
        init_log.append((DEBUG, f"HTTP: TLS/SSL Enabled: {self.tls_config.enabled}"))

        # initialize logging options
        self.logger_config = LoggerConfig(self.args, logger_name=self.meta.name)
        init_log.append((INFO, f"HTTP: Access Log Enabled: {self.logger_config.access_log}"))
        init_log.append((DEBUG, f"HTTP: Reload on changes: {self.logger_config.debug}"))

        # initialize uvicorn and FastAPI options
        self.uvc_config = UvicornConfig(args=self.args, logger_config=self.logger_config, tls_config=self.tls_config, workers=num_workers)
        self.api_config = FastAPIConfig(meta=self.meta, logger_config=self.logger_config)
        init_log.append((DEBUG, f"Using {num_workers} HTTP worker(s) for {num_cpu_cores} CPU core(s)."))
        
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

        logging_config["loggers"][self.logger_config.name] = logging_config["loggers"]["api"]
        del(logging_config["loggers"]["api"])

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
        self.access_log = not args.no_access_log if hasattr(args, 'no_access_log') else True
        self.format = args.log_format if args.log_format in LOG_FORMATS else "default"
        # if the log level is debug, force the log format to debug
        if self.level == "debug":
            self.debug = True
            # self.format = "debug"

class TlsConfig:
    """ TLS options dataclass """
    def __init__(self, args: Arguments) -> None:
        self.auto = args.tls_auto if hasattr(args, 'tls_auto') else False
        self.cert = args.tls_cert if hasattr(args, 'tls_cert') else None
        self.key = args.tls_key if hasattr(args, 'tls_key') else None
        self.ca = args.tls_ca if hasattr(args, 'tls_ca') else None
        self.enabled = self.auto or (self.cert is not None and self.key is not None)
    
    @property
    def protocol(self) -> str:
        """ Return the protocol based on TLS settings """
        return "https" if self.enabled else "http"
    
    def __bool__(self) -> bool:
        return self.enabled

class UvicornConfig:
    """ uvicorn options dataclass """
    def __init__(self, args: Arguments, logger_config: LoggerConfig, tls_config: TlsConfig, workers: int = 1) -> None:
        self.host = str(args.http_host) if hasattr(args, 'http_host') else "0.0.0.0"
        self.port = args.http_port if hasattr(args, 'http_port') else 3000
        self.proxy_headers=True
        self.log_level = logger_config.level
        self.access_log = logger_config.access_log
        self.reload = logger_config.debug
        self.workers = workers
        self.ssl_keyfile=tls_config.key
        self.ssl_certfile=tls_config.cert
        self.ssl_ca_certs=tls_config.ca

    @property
    def docs_url(self) -> str:
        """ Return the full URL for the server """
        proto = "https" if self.ssl_certfile and self.ssl_keyfile else "http"
        return f"{proto}://{self.host}:{self.port}/docs"

class FastAPIConfig:
    """ FastAPI options dataclass """
    def __init__(self, meta: AppMetadata, logger_config: LoggerConfig) -> None:
        self.title = meta.name
        self.summary = meta.description
        self.version = str(meta.version)
        self.reload = logger_config.debug