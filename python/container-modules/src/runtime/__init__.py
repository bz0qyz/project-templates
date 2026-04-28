import os
import sys
import logging
import platform
import importlib
from importlib import metadata
from packaging.version import Version
from pathlib import Path
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

        self.modules = self.load_modules(modules_dir=os.path.join(self.base_path, "modules"))

        # Initialize the app arguments, including arguments from each module
        self.args = Arguments(
            app_name=self.name,
            app_description=self.description,
            app_version=self.version,
            log_levels=LOG_LEVELS,
            modules=self.modules
        ).args


        # Initialize the app logger
        self.debug = True if self.args and hasattr(self.args, "log_level") and self.args.log_level == "debug" else False
        self.logger = AppLogger(
            name=self.name,
            log_format=self.args.log_format,
            log_level=self.args.log_level
        )

        for log in self.init_logs:
            getattr(self.logger, log[0])(log[1])
        self.init_logs = []

    def __str__(self):
        return f"{self.name} ver {self.version}"

    def load_modules(self, modules_dir: str) -> dict:
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

        loaded = {}

        for name in sorted(os.listdir(modules_dir)):
            if name.startswith("_"):
                continue

            module_path = os.path.join(modules_dir, name)

            if not os.path.isdir(module_path):
                continue
            if not os.path.isfile(os.path.join(module_path, "__init__.py")) or not os.path.isfile(os.path.join(module_path, "__main__.py")):
                continue

            import_path = f"{package_name}.{name}"  # e.g. "modules.my_module"
            main_path = f"{package_name}.{name}.__main__"

            try:
                loaded[name] = {}
                loaded[name]["module"] = importlib.import_module(import_path).module
                loaded[name]["main"] = importlib.import_module(main_path)
                self.init_logs.append(("info", f"Loaded: {import_path}"))
            except Exception as e:
                self.init_logs.append(("error", f"Failed to load {import_path}: {e}"))
                self.init_logs.append(("error", f"{e}"))

        return loaded
