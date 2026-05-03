import os
import sys
import logging
import platform
import importlib
from importlib import metadata
from packaging.version import Version
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
        self.packaged = False
        self.init_logs = []
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            self.packaged = True
            self.base_path = sys._MEIPASS

        # Get the project URL from metadata
        for k, v in meta.items():
            if k.lower() == "project-url" and v.startswith("home,"):
                self.homepage = v.split(",")[1].strip()
            if k.lower() == "project-url" and v.startswith("project,"):
                self.project_url = v.split(",")[1].strip()

        # Initialize the app logger
        self.logger = AppLogger(name=self.name)
        logging.root = self.logger
        logging.Logger.root = self.logger
        logging.Logger.manager = logging.Manager(self.logger)

        self.modules = self.import_modules(modules_dir=os.path.join(self.base_path, "modules"))

        # Initialize the app arguments, including arguments from each module
        self.args = Arguments(
            app_name=self.name,
            app_description=self.description,
            app_version=self.version,
            log_levels=LOG_LEVELS,
            modules=self.modules
        ).args


        # Set logging level and format
        self.logger.configure(log_level=self.args.log_level, log_format=self.args.log_format)
        self.debug = self.logger.debug

        # Initialize the modules
        self.init_modules()

        # Show any logs that happened during init and before the logger was configured
        for log in self.init_logs:
            getattr(self.logger, log[0])(log[1])
        self.init_logs = []

    def __str__(self):
        return f"{self.name} version {self.version}"

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
            # Verify that the module was not enabled by arg or ENV var
            module_enable_arg = f"enable_module_{name.replace('-', '_')}"
            is_enabled = getattr(self.args, module_enable_arg) if hasattr(self.args, module_enable_arg) else None
            module_disable_arg = f"disable_module_{name.replace('-', '_')}"
            is_disabled = getattr(self.args, module_disable_arg) if hasattr(self.args, module_disable_arg) else None

            # If enable argument is False and the module is enabled, disable it
            if not is_enabled and module.enabled and is_disabled is None:
                if module.default_disabled != is_enabled:
                    self.logger.warning(f"Disabling module: '{module.name}'. Module was disabled at runtime.")
                module.enabled = False

            # If disable argument is True and the module is enabled, disable it
            elif is_disabled and module.enabled and is_enabled is None:
                if module.default_disabled != is_disabled:
                    self.logger.warning(f"Disabling module: '{module.name}'. Module was disabled at runtime.")
                module.enabled = False

            # If enable argument is True and the module is disabled, enable it
            elif is_enabled and not module.enabled and is_disabled is None:
                if module.default_disabled == is_enabled:
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
                modules[name] = module

            except Exception as e:
                self.init_logs.append(("error", f"Failed to load {import_path}: {e}"))


        return modules
