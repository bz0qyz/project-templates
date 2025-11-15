import argparse
import os
from .constants import LOG_LEVELS, LOG_FORMATS

class Arguments(argparse.ArgumentParser):
    """ Application Argument Parser """
    def __init__(self, app):
        super().__init__(
            description=f"{app.name} v{app.version}.",
            epilog=f"{app.description} - {app.author}"
        )
        self.add_argument('-V', '--version',
                            action="version", version=f"{app.version}", help='Show version and exit..'
                            )
        # Run options
        self.add_argument('-ll', '--log-level',
            metavar='info', type=str, default='info', dest="log_level",
            help=f'Set the log level. Options: {', '.join(LOG_LEVELS)}. env: LOG_LEVEL',
            action=EnvDefault, envvar="LOG_LEVEL", choices=LOG_LEVELS
        )
        self.add_argument('-lf', '--log-format',
            metavar='default', type=str, default='default', dest="log_format",
            help=f'Set the log format. Options: {', '.join(LOG_FORMATS.keys())}. env: LOG_FORMAT',
            action=EnvDefault, envvar="LOG_LEVEL", choices=LOG_FORMATS.keys()
        )
        self.add_argument('--no-access-log',
            metavar="True|False",
            default=False,
            dest="no_access_log", type=bool,
            help='Disable the HTTP Access log.\nDefault: False. env: NO_ACCESS_LOG',
            action=EnvDefault, envvar="TLS_AUTOGEN"
        )
        self.add_argument('-p', '--port',
            metavar="3000",
            default=3000,
            dest="http_port", type=int,
            help='API HTTP Port',
            action=EnvDefault, envvar="HTTP_PORT"
        )
        self.add_argument('--tls-auto',
                            metavar="True|False",
                            default=False,
                            dest="tls_auto", type=bool,
                            help='Enable TLS with a generated self-signed certificate.\nDefault: False. env: TLS_AUTOGEN',
                            action=EnvDefault, envvar="TLS_AUTOGEN")
        self.add_argument('--tls-key',
                            metavar="/path/to/tls/key.pem",
                            default=None,
                            dest="tls_key",
                            help="The full path to a TLS key file. env: TLS_KEY_FILE",
                            action=EnvDefault, envvar="TLS_KEY_FILE")
        self.add_argument('--tls-cert',
                            metavar="/path/to/tls/crt.pem",
                            default=None,
                            dest="tls_cert",
                            help="The full path to a TLS certificate file. env: TLS_CERT_FILE",
                            action=EnvDefault, envvar="TLS_CERT_FILE")
        self.add_argument('--tls-ca',
                            metavar="/path/to/tls/ca.pem",
                            default=None,
                            dest="tls_ca",
                            help="The full path to a TLS CA certificate file. env: TLS_CA_FILE",
                            action=EnvDefault, envvar="TLS_CA_FILE")
        self.add_argument('--data-dir',
                            metavar=f"/data",
                            default=None,
                            help='The path for storing persistent data. If empty, state will not persist. env: DATA_DIR',
                            type=str, action=EnvDefault, envvar="DATA_DIR"
                            )
        # Set the app arguments property object
        self.args = self.parse_args()




class EnvDefault(argparse.Action):
    """ Argparse Action that uses ENV Vars for default values """
    def __init__(self, envvar, required=False, default=None, **kwargs):
        if envvar and envvar in os.environ:
            default = self.boolify(os.environ[envvar])
            required = False

        super().__init__(default=default,
                                         required=required,
                                         **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)

    @staticmethod
    def boolify(s):
        if isinstance(s, bool):
            return s
        if s.lower() in ['true', 't', 'yes', 'y', '1']:
            return True
        if s.lower() in ['false', 'f', 'no', 'n', '0']:
            return False
        return s