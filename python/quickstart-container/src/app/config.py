import logging
import json

class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Build a plain dict – you can add any extra fields you like
        payload = {
            "ts": self.formatTime(record, self.datefmt),
            "lvl": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Unpack the tuple – guard against malformed records
        try:
            client_addr, method, path, http_version, status_code = record.args
        except Exception:  # fallback – keep whatever we have
            client_addr = method = path = http_version = status_code = None

        # Add extra fields if they exist and replace the msg field
        if method is not None and path is not None:
            payload["msg"] = f"{method} {path}"
        if status_code is not None:
            payload["status_code"] = status_code
        if client_addr is not None:
            payload["client_addr"] = client_addr
        if http_version is not None:
            payload["http_version"] = f"HTTP/{http_version}"

        return json.dumps(payload, ensure_ascii=False)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "minimal": {
            "format": "%(levelname)-8s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": False,
        },
        "default": {
            "format": "%(asctime)s - %(levelname)-8s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": False,
        },
        "debug": {
            "format": "%(levelname)-8s: %(name)s (%(module)s:%(lineno)d): %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": False,
        },
        "json": {
            "()": JsonLogFormatter,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
    },
    "loggers": {
        "app": {"handlers": ["default"], "level": "INFO", "propagate": False },
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False },
        "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
    },
    "root": {
        "level": "INFO",
        "handlers": ["default"],
    },
}