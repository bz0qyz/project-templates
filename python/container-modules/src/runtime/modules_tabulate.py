import logging
from tabulate import tabulate

class ModulesTabulate:
    """ Modules tabulate """
    def __init__(self, modules: dict, table_format: str = "rounded_grid"):
        self.modules = modules
        self.table_format = table_format
        self.logger = logging.getLogger("modules.tabulate")

    @staticmethod
    def _table_key_headers(keys: list) -> list:
        """ convert a list of keys to a list of header strings """
        headers = []
        for key in keys:
            key_parts = key.split("_")
            new_key_parts = []
            for part in key_parts:
                new_key_parts.append(part.strip().capitalize())
            headers.append(' '.join(new_key_parts))

        return headers

    def show_module_summary(self, module_name: str = None) -> str:
        """ Show module summary table """
        keys = ["name", "version", "description", "enabled", "default_disabled"]
        values = []
        show_modules = {}

        if not module_name:
            show_modules = self.modules
        else:
            if not isinstance(module_name, str):
                raise ValueError(f"Invalid module name: {module_name}")

            if module_name not in self.modules.keys():
                self.logger.error(f"Module name '{module_name}' is not a valid module name")
                self.logger.info(f"Modules '{', '.join(self.modules.keys())}'")
                return None

            show_modules[module_name] = self.modules[module_name]

        for module in show_modules.values():
            module_values = []
            for key in keys:
                module_values.append(f"{getattr(module, key, None)}")

            values.append(module_values)

        return tabulate(values, headers=self._table_key_headers(keys), tablefmt=self.table_format)

    def show_module_args(self, module_name: str) -> str:
        """ Show module information in a table """
        keys = ["dest", "flags", "envvar", "help", "required", "type", "default"]
        keys_max_width = [None, None, 30, 60, None, None, None]
        values = []

        if not module_name or not isinstance(module_name, str):
            raise ValueError(f"Invalid module name: {module_name}")

        if module_name not in self.modules:
            self.logger.error(f"Module name '{module_name}' is not a valid module name")
            self.logger.info(f"Modules '{', '.join(self.modules.keys())}'")
            return None

        module = self.modules[module_name]
        for arg in module.arguments:
            arg_values = []
            for key in keys:
                value = getattr(arg, key, None)
                if isinstance(value, list):
                    value = ", ".join(value)
                elif isinstance(value, str):
                    value = value.split("ENV:")[0]
                    value = value.split("Default:")[0]
                elif isinstance(value, type):
                    value = value.__name__

                arg_values.append(f"{value}")
            values.append(arg_values)

        return tabulate(values, headers=self._table_key_headers(keys), tablefmt=self.table_format, maxcolwidths=keys_max_width)