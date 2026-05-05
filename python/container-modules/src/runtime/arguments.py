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
        parser.add_argument('--module',
                            metavar='module-name', type=str, default=None, dest='show_module_info',
                            help='Show the details for a specific module name',
                            )
        parser.add_argument('--table-format',
                            metavar='rounded_grid', type=str, default="rounded_grid", dest='table_format',
                            help='Set the tabulate format for modules help. See https://pypi.org/project/tabulate for options. Default: rounded_grid.',
                            )
        parser.add_argument('-cf', '--config-file',
                            metavar='/path/to/config.json', type=str, default=None,
                            help='Use a configuration file for argument values. Values override args and ENV vars. ENV: CONFIG_FILE',
                            action=EnvDefault, envvar="CONFIG_FILE"
                            )
        parser.add_argument('--async',
                            metavar='True|False', type=str, default=True, dest="async_enabled",
                            help=f'Run each module asynchronously. Default True. ENV: ASYNC_ENABLED',
                            action=EnvDefault, envvar="ASYNC_ENABLED"
                            )
        parser.add_argument('--async-workers',
                            metavar='8', type=int, default=8, dest="async_workers",
                            help=f'Set the number of workers. Only valid if --async is True. ENV: ASYNC_WORKERS',
                            action=EnvDefault, envvar="ASYNC_WORKERS"
                            )
        parser.add_argument('--async-worker-timeout',
                            metavar='60', type=int, default=60, dest="async_worker_timeout",
                            help=f'Set the timeout for async workers. Only valid if --async is True. ENV: ASYNC_WORKER_TIMEOUT',
                            action=EnvDefault, envvar="ASYNC_WORKER_TIMEOUT"
                            )
        parser.add_argument('--oneshot', '--cron',
                            default=True, type=str, dest="one_shot",
                            help='Run one time and exit. If not set, the app will run continuously at the interval set by --interval-minutes. ENV: ONESHOT or CRON',
                            action=EnvDefault,
                            envvar=["ONESHOT", "CRON"]
                            )
        parser.add_argument('-i', '--interval-minutes',
                            metavar="15",
                            default=10,
                            dest="run_interval", type=int,
                            help='Run Interval. Only valid if --oneshot is not set. ENV: RUN_INTERVAL',
                            action=EnvDefault, envvar="RUN_INTERVAL"
                            )
        log_group = parser.add_argument_group("logging options")
        log_group.add_argument('--log-level',
                               metavar='info', type=str, default='info', dest="log_level",
                               help=f'Set the log level. Levels: {', '.join(log_levels.keys())}. ENV: LOG_LEVEL',
                               action=EnvDefault, envvar="LOG_LEVEL", choices=log_levels.keys()
                               )
        log_group.add_argument('--log-format',
                               metavar='text', type=str, default='text', dest="log_format",
                               help=f'Set the log format. Formats: json, text. ENV: LOG_FORMAT',
                               action=EnvDefault, envvar="LOG_FORMAT", choices=['text', 'json']
                               )
        log_group.add_argument("--dev-log",
                               help="development mode. Add file paths to debug logging.",
                               action="store_true", dest="dev_log"
                               )
        # Add an argument group for control of each module
        control_group = parser.add_argument_group("module control options")

        # Load arguments from each module
        # Add a control argument for enabling or disabling each module based on the module's default_disabled property
        for module_name, module in modules.items():
            if module and hasattr(module, 'arguments'):
                prefix = module.control_arg_prefix
                env_var = module.control_env_name
                control_group.add_argument(
                    f'--{prefix}-{module.name}',
                    metavar="True|False",
                    default=False,
                    dest=f"{module.control_arg_dest}",
                    type=str,
                    help=f"{prefix.capitalize()} the '{module.name}' module. Default: False. ENV: {env_var}",
                    action=EnvDefault,
                    envvar=env_var
                )
                args_group = parser.add_argument_group(f"{module.name} options")
                for arg in module.arguments:
                    arg.add_to_parser(args_group)

        # Set the app arguments property object
        self.args = parser.parse_known_args()

        # If arguments are found that are not valid, argparse returns a tuple
        if isinstance(self.args, tuple):
            self.args = self.args[0]

        # Convert str boolean values into booleans
        for arg in vars(self.args):
            # Set boolean strings to bool type
            bset = {"true": True, "1": True, "false": False, "0": False}
            value = getattr(self.args, arg)
            if type(value) not in  [str, bool]:
                continue
            if str(value).lower() in bset.keys():
                setattr(self.args, arg, bset[str(value).lower()])

    def __repr__(self):
        return self.args

