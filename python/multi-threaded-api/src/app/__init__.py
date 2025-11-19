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
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
from .arguments import Arguments
init_log: list[tuple[int, str]] = [] 

class App:
    """ Base application configuration """
    # Must match pyproject.toml
    PROJECT_NAME = "template-api"
    
    def __init__(self, num_queues: int = 1) -> None:
        # Set applcation defalts
        print(metadata.distribution(self.PROJECT_NAME)._path)

        # Calculate number of fastAPI workers
        num_queues = num_queues
        num_cpu_cores = os.cpu_count() if os.cpu_count() is not None else 1
        num_workers = (num_cpu_cores - num_queues) if (num_cpu_cores - num_queues) > 0 else 1

        # initialize application metadata
        self.meta = AppMetadata(self.PROJECT_NAME)
        init_log.append((INFO, f"Initializing application: {self.name} v{self.version} [license: {self.meta.license}]"))
        self.base_dir = BASE_DIR
        init_log.append((DEBUG, f"Base directory set to: {self.base_dir}"))
        
        # initialize application arguments
        self.args = Arguments(self).args
        
        # initialize TLS options
        self.tls_opts = TlsOptions(self.args)
        init_log.append((DEBUG, f"Logging: Level: {self.args.log_level}"))
        init_log.append((DEBUG, f"HTTP: TLS/SSL Enabled: {self.tls_opts.enabled}"))

        # initialize logging options
        self.log_opts = LogOptions(self.args)
        init_log.append((INFO, f"HTTP: Access Log Enabled: {self.log_opts.access_log}"))
        init_log.append((DEBUG, f"HTTP: Reload on changes: {self.log_opts.debug}"))

        # initialize uvicorn and FastAPI options
        self.uvc_opts = UvicornOptions(args=self.args, log_opts=self.log_opts, tls_opts=self.tls_opts, workers=num_workers)
        self.api_opts = FastAPIOptions(meta=self.meta, log_opts=self.log_opts)
        init_log.append((DEBUG, f"Using {num_workers} HTTP worker(s) for {num_cpu_cores} CPU core(s) and {num_queues} worker queue(s)."))
        
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

class AppMetadata:
    """ Application metadata dataclass """
    def __init__(self, project_name: str) -> None:
        meta = metadata.metadata(project_name)
        self.name = meta["Name"]
        self.version = Version(meta["Version"])
        self.description = meta["Summary"]
        self.author = meta["Author-email"]
        self.license = meta["License-Expression"]
        self.copyright = f"\u00A9 {datetime.datetime.today().year} {self.author}"
        self.footer = f"{self.name} | {self.copyright}"

      
class LogOptions:
    """ Logging options dataclass """
    def __init__(self, args: Arguments) -> None:
        self.debug = False
        self.date_format = "%Y-%m-%d %H:%M:%S"
        self.level = args.log_level if args.log_level in LOG_LEVELS else "info"
        self.access_log = not args.no_access_log if hasattr(args, 'no_access_log') else True

        self.format_key = args.log_format if args.log_format in LOG_FORMATS.keys() else "default"
        # if the log level is debug, force the log format to debug
        if self.level == "debug":
            self.debug = True
            log_format_key = "debug"
        self.format = LOG_FORMATS[self.format_key]

class TlsOptions:
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

class UvicornOptions:
    """ uvicorn options dataclass """
    def __init__(self, args: Arguments, log_opts: LogOptions, tls_opts: TlsOptions, workers: int = 1) -> None:
        self.host = str(args.http_host) if hasattr(args, 'http_host') else "0.0.0.0"
        self.port = args.http_port if hasattr(args, 'http_port') else 3000
        self.proxy_headers=True
        self.log_level = log_opts.level
        self.access_log = log_opts.access_log
        self.reload = log_opts.debug
        self.workers = workers
        self.ssl_keyfile=tls_opts.key
        self.ssl_certfile=tls_opts.cert
        self.ssl_ca_certs=tls_opts.ca

    @property
    def docs_url(self) -> str:
        """ Return the full URL for the server """
        proto = "https" if self.ssl_certfile and self.ssl_keyfile else "http"
        return f"{proto}://{self.host}:{self.port}/docs"

class FastAPIOptions:
    """ FastAPI options dataclass """
    def __init__(self, meta: AppMetadata, log_opts: LogOptions) -> None:
        self.title = meta.name
        self.description = meta.description
        self.version = str(meta.version)
        self.reload = log_opts.debug