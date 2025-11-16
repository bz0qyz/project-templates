import argparse
import os
import textwrap
import ipaddress
from typing import Any
from .constants import LOG_LEVELS, LOG_FORMATS

class Arguments(argparse.ArgumentParser):
    """ Application Argument Parser """
    def __init__(self, app):
        super().__init__(
            description=f"{app.name} v{app.version}.",
            epilog=textwrap.dedent(f"""\
            -----------------------------------------------------------------------------------------
            {app.meta.description} | {app.meta.copyright} | {app.meta.license}\n
            """),
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        self.add_argument('-V', '--version',
                            action="version", version=f"{app.name} v{app.version}", help='Show version and exit..'
                            )
        # Run options
        self.add_argument('-ll', '--log-level',
            metavar='info', type=str, default='info', dest="log_level",
            help=f"Set the logging level (default: %(default)s) (choices: %(choices)s). env: LOG_LEVEL",
            action=EnvDefault, envvar="LOG_LEVEL", choices=LOG_LEVELS
        )
        self.add_argument('-lf', '--log-format',
            metavar='default', type=str, default='default', dest="log_format",
            help=f'Set the logging format (default: %(default)s). (choices: %(choices)s). env: LOG_FORMAT',
            action=EnvDefault, envvar="LOG_LEVEL", choices=LOG_FORMATS.keys()
        )
        self.add_argument('--no-access-log',
            metavar="True|False",
            default=False,
            dest="no_access_log", type=bool,
            help=f'Disable the HTTP Access log (default: %(default)s). env: NO_ACCESS_LOG',
            action=EnvDefault, envvar="TLS_AUTOGEN"
        )
        # Server options
        self.add_argument('-l', '--listen',
            metavar="0.0.0.0", type=self.ip_addr, default="0.0.0.0", dest="http_host",
            help=f'API HTTP listener host (default: %(default)s). env: HTTP_LISTEN_ADDR',
            action=EnvDefault, envvar="HTTP_LISTEN_ADDR"
        )
        self.add_argument('-P', '--port',
            metavar="3000",
            default=3000,
            dest="http_port", type=int,
            help='API HTTP Port (default: %(default)s). env: HTTP_LISTEN_PORT',
            action=EnvDefault, envvar="HTTP_LISTEN_PORT"
        )
        self.add_argument('--tls-auto',
                            metavar="True|False",
                            default=False,
                            dest="tls_auto", type=bool,
                            help=f'Enable TLS with a generated self-signed certificate (default: %(default)s). env: TLS_AUTOGEN',
                            action=EnvDefault, envvar="TLS_AUTOGEN")
        self.add_argument('--tls-key',
                            metavar="/path/to/tls/key.pem",
                            default=None,
                            dest="tls_key",
                            help="The full path to a TLS key file (default: %(default)s). env: TLS_KEY_FILE",
                            action=EnvDefault, envvar="TLS_KEY_FILE")
        self.add_argument('--tls-cert',
                            metavar="/path/to/tls/crt.pem",
                            default=None,
                            dest="tls_cert",
                            help="The full path to a TLS certificate file (default: %(default)s). env: TLS_CERT_FILE",
                            action=EnvDefault, envvar="TLS_CERT_FILE")
        self.add_argument('--tls-ca',
                            metavar="/path/to/tls/ca.pem",
                            default=None,
                            dest="tls_ca",
                            help="The full path to a TLS CA certificate file (default: %(default)s). env: TLS_CA_FILE",
                            action=EnvDefault, envvar="TLS_CA_FILE")
        self.add_argument('--data-dir',
                            metavar=f"/data",
                            default=None,
                            help='The path for storing persistent data (default: %(default)s). If empty, state will not persist. env: DATA_DIR',
                            type=str, action=EnvDefault, envvar="DATA_DIR"
                            )
        # Set the app arguments property object
        self.args = self.parse_args()

    @staticmethod
    def ip_addr(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
        """ Argparse type for IP addresses """
        if isinstance(value, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
            # Already an ipaddress object (e.g. from a default you set as such)
            return value

        if value.lower() == "localhost":
            value = "127.0.0.1"
        try:
            return ipaddress.ip_address(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"{value} is not a valid IP address")


class EnvDefault(argparse.Action):
    """
    Argparse Action that uses an environment variable as the default value.
    It respects the argument's ``type=`` conversion and does **not** apply it
    twice.  It also knows how to coerce common textual representations of
    booleans (e.g. "yes"/"no", "1"/"0").
    """

    def __init__(
        self,
        option_strings,
        dest,
        *,
        envvar: str | None = None,
        required: bool = False,
        default: Any = None,
        **kwargs,
    ):
        """
        Parameters
        ----------
        option_strings : list[str]
            Passed straight from argparse (e.g. ['-l', '--listen']).
        dest : str
            Destination attribute name (also from argparse).
        envvar : str | None
            Name of the environment variable that should supply the default.
        required : bool
            Whether the argument is required *if* the env‑var is missing.
        default : Any
            The normal argparse default (used when envvar is not set).
        kwargs :
            Any other kwargs that argparse expects (e.g. ``help=``).
        """
        self.envvar = envvar

        # If the env‑var exists, use its value as the *default* for argparse.
        # Otherwise keep the user‑supplied default.
        if envvar and envvar in os.environ:
            # Defer type conversion – we just store the raw string.
            # ``boolify`` is only applied for boolean‑like arguments.
            raw = os.environ[envvar]
            default = self._maybe_boolify(raw)
            required = False          # env‑var satisfies the requirement

        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            required=required,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Helper: turn common textual booleans into real bools.
    # ------------------------------------------------------------------
    @staticmethod
    def _maybe_boolify(value: str) -> Any:
        """Return a proper bool if the string looks like one, else the original."""
        lowered = value.lower()
        if lowered in {"true", "t", "yes", "y", "1"}:
            return True
        if lowered in {"false", "f", "no", "n", "0"}:
            return False
        return value

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)