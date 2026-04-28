import argparse
from runtime._shared import EnvDefault

class Arguments:
    """ Application Arguments parser """
    def __init__(self, app_name, app_description, app_version, log_levels: dict, modules: dict):
        parser = argparse.ArgumentParser(description=f"{app_description} v{app_version}")
        parser.add_argument("--version",
                            help="Show program version and exit.",
                            action="store_true"
                            )
        parser.add_argument('--log-level',
                            metavar='info', type=str, default='info', dest="log_level",
                            help=f'Set the log level. Levels: {', '.join(log_levels.keys())}. env: LOG_LEVEL',
                            action=EnvDefault, envvar="LOG_LEVEL", choices=log_levels.keys()
                            )
        parser.add_argument('--log-format',
                            metavar='json', type=str, default='json', dest="log_format",
                            help=f'Set the log format. Formats: json, text. env: LOG_FORMAT',
                            action=EnvDefault, envvar="LOG_FORMAT", choices=['text', 'json']
                            )
        control_group = parser.add_argument_group("module control options")

        for module_name, module in modules.items():
            if "module" in module and hasattr(module["module"], 'register_args'):
                name = module["module"].name
                disabled = module["module"].disabled
                envvar = f"DISABLE_MODULE_{name.upper()}"
                control_group.add_argument(
                    f'--disable-{name}',
                    metavar="True|False",
                    default=disabled,
                    dest=f"disable_module_{name}",
                    type=str,
                    help=f'Disable the {name} module. Default: {disabled}. ENV: {envvar}',
                    action=EnvDefault,
                    envvar=envvar
                )
                module["module"].register_args(parser)

        # Set the app arguments property object
        self.args = parser.parse_known_args()

        # If arguments are found that are not valid, argparse returns a tuple
        if isinstance(self.args, tuple):
            self.args = self.args[0]

        for arg in vars(self.args):
            # Set boolean strings to bool type
            bset = {"true": True, "1": True, "false": False, "0": False}
            value = getattr(self.args, arg)
            if type(value) not in  [str, int, bool]:
                continue
            if str(value).lower() in bset.keys():
                setattr(self.args, arg, bset[str(value).lower()])

    def __repr__(self):
        return self.args

