import argparse
import logging
from runtime._shared import (EnvDefault)

class AppModule:
    def __init__(self, name: str, version: str, description: str = None, disabled: bool = False):
        self.name = name
        self.version = version
        self.description = description if description else f"{name} module"
        self.disabled = disabled
        self.logger = None

    def __str__(self):
        return f"{self.name} module v{self.version}"

    def register_args(self, parser: argparse.ArgumentParser):
        args = parser.add_argument_group(f"{self.name} options")

    def shutdown(self):
        if self.logger:
            self.logger.info(f"Closing module")
        pass

    def set_logger(self, app_logger: logging.Logger):
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(app_logger.level)
        for handler in app_logger.handlers:
            self.logger.addHandler(handler)
        self.logger.propagate = False

