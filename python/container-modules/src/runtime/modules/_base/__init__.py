import argparse
import logging
from typing import Any
from dataclasses import dataclass, field
from runtime._shared import (EnvDefault)


class AppModuleBase:
    """" Module Base class """
    immutable_properties = ("name", "version", "description", "enabled", "default_disabled", "_no_load")

    @dataclass
    class Argument:
        flags: list[str]  # e.g. ["--port"] or ["-v", "--verbose"]
        help: str = ""
        default: Any = None
        type: Any = str
        required: bool = False
        action: str = None
        choices: list = None
        metavar: str = None
        dest: str = None
        envvar: str = None

        def add_to_parser(self, parser: argparse.ArgumentParser|argparse._ArgumentGroup):
            """Register this argument on the given parser."""
            if self.envvar and not 'ENV:' in self.envvar:
                self.help = f"{self.help} ENV: {self.envvar}"
            kwargs = {k: v for k, v in {
                "help": self.help,
                "default": self.default,
                "type": self.type,
                "required": self.required,
                "action": self.action,
                "choices": self.choices,
                "metavar": self.metavar,
                "dest": self.dest,
                "envvar": self.envvar,
            }.items() if v is not None}

            parser.add_argument(*self.flags, **kwargs)
    class Arguments:
        def add(self, name, value) -> None:
            if hasattr(self, name):
                raise AttributeError(f"Argument '{name}' already exists.")
            setattr(self, name, value)

    def __init__(self, name: str, version: str, description: str = None, enabled: bool = True, default_disabled: bool = False):
        self.name = name
        self.version = version
        self.description = description if description else f"{name} module"
        # Enabled/Disable the module from being used
        self.enabled = enabled
        # If the module is disabled on init, then set it to not be loaded
        self._no_load = not self.enabled #if self.enabled else False
        # Determine if the module should be enabled by default or require user to explicitly enable it.
        # By argument or ENV Variable
        self.default_disabled = default_disabled
        # Save a list of arguments to be loaded by the parent app
        self.arguments = []
        # Initialize the module logger
        self.logger = logging.getLogger(self.name)
        # Create an empty arguments object
        self.args = self.Arguments()
        # Add special hook functions
        self._post_init_hooks = []
        self._before_hooks = []
        self._after_hooks = []

    def __str__(self):
        return f"{self.name} module v{self.version}"

    @property
    def load_disabled(self):
        return self._no_load

    @property
    def control_arg_prefix(self):
        """ Determine prefix for control arguments """
        return "enable" if self.default_disabled else "disable"

    @property
    def control_arg_dest(self):
        """ Determine prefix for control arguments """
        return f"{self.control_arg_prefix}_module_{self.name.replace('-', '_')}"

    @property
    def control_env_name(self) -> str:
        return f"{self.control_arg_prefix.upper()}_MODULE_{self.name.upper().replace('-', '_')}"


    def post_init(self, fn):
        self._post_init_hooks.append(fn)
        return fn

    def before_run(self, fn):
        self._before_hooks.append(fn)
        return fn

    def after_run(self, fn):
        self._after_hooks.append(fn)
        return fn

    def shutdown(self):
        pass

    def add_argument(self, *args, **kwargs) -> None:
        self.arguments.append(self.Argument(*args, **kwargs))

    def init(self, **kwargs: dict) -> bool:
        """
        Initialize the module with optional keyword arguments.
        This can be used to pass in shared resources like database connections, clients, etc.
        """
        for key, value in kwargs.items():
            if key not in self.immutable_properties:
                setattr(self, key, value)

        # Run post init hooks
        for fn in self._post_init_hooks:
            fn()

        return self.enabled

    def register_args(self):
        pass

    def main(self, *args, **kwargs) -> bool:
        pass

    def run(self, *args, **kwargs):
        for fn in self._before_hooks:
            fn()
        result = self.main(*args, **kwargs)
        for fn in self._after_hooks:
            fn(result)
        return result

