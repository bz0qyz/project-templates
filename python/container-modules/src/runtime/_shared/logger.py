import os
import json
import logging

LOG_LEVELS = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

class JsonFormatter(logging.Formatter):
    def __init__(self, base_path: str, debug: bool = False):
        super().__init__()
        self.base_path = base_path
        self.debug = debug

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": self.formatTime(record, DATE_FORMAT),
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
        }
        if self.debug:
            rel = os.path.relpath(record.pathname, self.base_path)
            entry["file"]     = rel if not rel.startswith("..") else record.pathname
            entry["line"]     = record.lineno
            entry["function"] = record.funcName
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)

class TextFormatter(logging.Formatter):
    _BASE_FMT  = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
    _DEBUG_FMT = "%(asctime)s %(levelname)-8s %(name)s: %(pathname)s:%(lineno)d %(funcName)s %(message)s"

    def __init__(self, base_path: str, debug: bool = False):
        super().__init__(
            fmt=self._DEBUG_FMT if debug else self._BASE_FMT,
            datefmt=DATE_FORMAT,
        )
        self.base_path = base_path
        self.debug = debug

    def format(self, record: logging.LogRecord) -> str:
        if self.debug:
            rel = os.path.relpath(record.pathname, self.base_path)
            record.pathname = rel if not rel.startswith("..") else record.pathname
        return super().format(record)

class AppLogger(logging.Logger):
    def __init__(self, name: str, log_format: str = "text", log_level: str = "info", base_path: str = None):
        super().__init__(name)
        self.log_level = LOG_LEVELS[log_level]
        self.base_path = base_path
        self._console_handler = logging.StreamHandler()
        self.addHandler(self._console_handler)
        self.configure(log_format=log_format, log_level=log_level)

    def configure(self, log_format: str, log_level: str = "info") -> None:
        debug = True if log_level == "debug" else False
        self.log_level = LOG_LEVELS[log_level]
        if log_format == "text":
            log_formater = TextFormatter(base_path=self.base_path, debug=debug)
        else:
            log_formater = JsonFormatter(base_path=self.base_path, debug=debug)

        self.setLevel(self.log_level)
        self._console_handler.setFormatter(log_formater)