import os
import sys
import json
import logging
import platform
import importlib
from importlib import metadata
from packaging.version import Version
from types import NoneType
from tabulate import tabulate
from .arguments import Arguments
from ._shared import (AppLogger, LOG_LEVELS)


class App:
    """ Base application configuration """
    # Must match pyproject.toml [project] name
    PROJECT_NAME = "container-modules"

    def __init__(self):
        meta = metadata.metadata(self.PROJECT_NAME)
        self.name = meta["Name"]
        self.version = Version(meta["Version"])
        self.description = meta["Summary"]
        self.author = meta["Author-email"]
        self.homepage = None
        self.project_url = None
        self.system = f"{platform.system()}".lower()
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.modules_path = os.path.join(self.base_path, "modules")
        self.packaged = False
        self.init_logs = []
        # If the app is packaged (pyinstaller) set the base_path correctly
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            self.packaged = True
            self.base_path = sys._MEIPASS
            self.modules_path = os.path.join(self.base_path, "runtime", "modules")

        # Get the project URL from metadata
        for k, v in meta.items():
            if k.lower() == "project-url" and v.startswith("home,"):
                self.homepage = v.split(",")[1].strip()
            if k.lower() == "project-url" and v.startswith("project,"):
                self.project_url = v.split(",")[1].strip()

        # Initialize the app logger
        self.logger = AppLogger(name=self.name, base_path=self.base_path)
        logging.root = self.logger
        logging.Logger.root = self.logger
        logging.Logger.manager = logging.Manager(self.logger)

        self.modules = self.import_modules(modules_dir=self.modules_path)

        # Initialize the app arguments, including arguments from each module
        self.args = Arguments(
            app_name=self.name,
            app_description=self.description,
            app_version=self.version,
            log_levels=LOG_LEVELS,
            modules=self.modules
        ).args

        # Use a configuration file if one is specified. Save the values into self.args.
        if hasattr(self.args, "config_file") and self.args.config_file and isinstance(self.args.config_file, str):
            self.args.config_file = os.path.realpath(self.args.config_file)
            if not os.path.isfile(self.args.config_file):
                self.logger.warning(f"Configuration file not found: '{self.args.config_file}'")
                return

            self.logger.info(f"Using configuration file: {self.args.config_file}")
            with open(self.args.config_file) as config_file:
                try:
                    config = json.load(config_file)
                except json.decoder.JSONDecodeError as e:
                    self.logger.error(f"Failed to load configuration file: {e}")
                    return
            for arg_name in config:
                if hasattr(self.args, arg_name) and config[arg_name] is not None:
                    # get the variable type for each arg and matching config var
                    arg_type = type(getattr(self.args, arg_name))
                    config_type = type(config[arg_name])
                    # If the types also match (or NoneType) replace the arg value with the config value
                    if arg_type == config_type or arg_type is NoneType:
                        setattr(self.args, arg_name, config[arg_name])

        # Set logging level and format
        self.logger.configure(log_level=self.args.log_level, log_format=self.args.log_format,
                              dev_log=self.args.dev_log)
        self.debug = self.logger.debug

        # Initialize the modules
        self.init_modules()

        # Show any logs that happened during init and before the logger was configured
        for log in self.init_logs:
            getattr(self.logger, log[0])(log[1])
        self.init_logs = []

    def __str__(self):
        return f"{self.name} version {self.version}"

    @property
    def num_enabled_modules(self):
        """ Number of modules with the enabled attribute set to True """
        ct = 0
        for module in self.modules.values():
            if module.enabled:
                ct += 1
        return ct

    def show_modules(self):
        """ Show modules in a table """
        print(f"{self}") # Prints app name and version (__str__)
        print("Modules:")
        tab_modules = []
        for name, module in self.modules.items():
            tab_modules.append(
                [module.name, module.version, module.description, module.enabled, module.default_disabled])
        print(tabulate(tab_modules, headers=["Module Name", "Version", "Description", "Enabled", "Default Disabled"],
                       tablefmt="rounded_outline"))

    def init_modules(self):
        """ Initialize the modules with app arguments """
        for name, module in self.modules.items():
            # Module Control arguments:
            # Enable or disable the module if it was modified by arg or ENV var
            module_control = (module.control_arg_dest, getattr(self.args, module.control_arg_dest, False))
            if isinstance(module_control, tuple) and module_control[1]:
                if module_control[0].startswith("disable"):
                    if module.enabled:
                        if module.default_disabled != module_control[1]:
                            self.logger.warning(f"Disabling module: '{module.name}'. Module was disabled at runtime.")
                        module.enabled = False

                elif module_control[0].startswith("enable"):
                    if not module.enabled:
                        if module.default_disabled == module_control[1]:
                            self.logger.info(f"Enabling module: '{module.name}'. Module was enabled at runtime.")
                        module.enabled = True

            # Don't initialize the module if it is disabled
            if not module.enabled:
                continue

            self.logger.debug(f"Initializing module: '{module.name}' -> '{module.description}'")
            self.init_module_args(module)
            # Create module attributes from the app
            # This can be called in __main__ to add additional attributes
            if not hasattr(module, 'init'):
                continue
            try:
                initialized = module.init(**{})
                if not initialized:
                    self.logger.warning(f"Module '{name}' failed to initialize and will be disabled.")
                    module.enabled = False
            except Exception as e:
                self.logger.error(f"Exception loading module '{name}': {e}")
                module.enabled = False

    def init_module_args(self, module):
        """ Pass the module's argument values into the module """
        for arg in module.arguments:
            if arg.dest and hasattr(self.args, arg.dest):
                module.args.add(arg.dest, getattr(self.args, arg.dest))
                continue
            for flag in arg.flags:
                if flag.startswith("--"):
                    arg_name = flag[2:].replace("-", "_")
                    if not hasattr(self.args, arg_name):
                        continue
                    module.args.add(arg_name, getattr(self.args, arg_name))

    def import_modules(self, modules_dir: str) -> dict:
        """
        Discovers and imports all valid subpackages in the given directory.
        modules_dir can be an absolute or relative filesystem path.
        """
        modules_dir = os.path.abspath(modules_dir)

        # Add the parent of modules_dir to sys.path so imports resolve correctly
        parent_dir = os.path.dirname(modules_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # The importable package name is just the final directory name
        package_name = os.path.basename(modules_dir)

        modules = {}

        for name in sorted(os.listdir(modules_dir)):
            if name.startswith("_"):
                continue

            module_path = os.path.join(modules_dir, name)

            if not os.path.isdir(module_path) or not os.path.isfile(os.path.join(module_path, "__init__.py")):
                continue

            # Import the module
            import_path = f"{package_name}.{name}"  # e.g. "modules.my_module"
            try:
                module = importlib.import_module(import_path).module
                # Set the module to disabled if it's default_disabled is True
                if module.load_disabled:
                    continue
                if module.enabled and module.default_disabled:
                    module.enabled = False
                modules[module.name] = module

            except Exception as e:
                self.init_logs.append(("error", f"Failed to load {import_path}: {e}"))


        return modules
