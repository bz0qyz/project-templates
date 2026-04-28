import os
import argparse
from .logger import (AppLogger, LOG_LEVELS)

class EnvDefault(argparse.Action):
    """ Argparse Action that uses ENV Vars for default values """
    def __init__(self, envvar, required=False, default=None, **kwargs):
        bset = {"true": True, "1": True, "false": False, "0": False}
        if envvar:
            # If passed a string, convert to a list
            if isinstance(envvar, str):
                envvar = [envvar]
            # Check for env vars for default values
            for varname in envvar:
                # Allow env var defaults
                if varname in os.environ:
                    # Convert boolean strings to bool
                    if os.environ[varname].lower() in bset.keys() and "type" in kwargs and kwargs["type"] in [bool, str]:
                        default = bset[os.environ[varname].lower()]
                    else:
                        default = os.environ[varname]
                    required = False
                    break

        super().__init__(default=default, required=required, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)