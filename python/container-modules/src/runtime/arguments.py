import argparse
from runtime._shared import EnvDefault

class Arguments:
    """ Application Arguments parser """
    def __init__(self, app_name, app_description, app_version, log_levels: dict, modules: dict):
        parser = argparse.ArgumentParser(description=f"{app_description} v{app_version}")
        parser.add_argument("--version",
                            help="Show application version and exit.",
                            action="store_true", dest="show_version"
                            )
        parser.add_argument("--modules",
                            help="Show application modules and exit.",
                            action="store_true", dest="show_modules"
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
        parser.add_argument('--async',
                            metavar='True|False', type=str, default=False, dest="async_enabled",
                            help=f'Run each module asynchronously. env: ASYNC_ENABLED',
                            action=EnvDefault, envvar="ASYNC_ENABLED"
                            )
        parser.add_argument('--async-workers',
                            metavar='4', type=int, default=4, dest="async_workers",
                            help=f'Set the number of workers. Only valid if --async is True. env: ASYNC_WORKERS',
                            action=EnvDefault, envvar="ASYNC_WORKERS"
                            )
        parser.add_argument('--async-worker-timeout',
                            metavar='60', type=int, default=60, dest="async_worker_timeout",
                            help=f'Set the timeout for async workers. Only valid if --async is True. env: ASYNC_WORKER_TIMEOUT',
                            action=EnvDefault, envvar="ASYNC_WORKER_TIMEOUT"
                            )
        control_group = parser.add_argument_group("module control options")

        for module_name, module in modules.items():
            if module and hasattr(module, 'arguments'):
                disabled = module.default_disabled
                if disabled:
                    prefix = "enable"
                else:
                    prefix = "disable"

                env_var = f"{prefix.upper()}_MODULE_{module_name.upper().replace('-', '_')}"
                control_group.add_argument(
                    f'--{prefix}-{module_name}',
                    metavar="True|False",
                    default=False,
                    dest=f"{prefix}_module_{module_name.replace('-', '_')}",
                    type=str,
                    help=f"{prefix.capitalize()} the '{module_name}' module. Default: False. ENV: {env_var}",
                    action=EnvDefault,
                    envvar=env_var
                )
                args_group = parser.add_argument_group(f"{module_name} options")
                for arg in module.arguments:
                    arg.add_to_parser(args_group)

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

