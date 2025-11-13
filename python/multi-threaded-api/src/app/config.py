import datetime
from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    """ Application Basic Information """
    name = "API template"
    version = "0.0.1"
    description = "A simple Multi-threaded API with a queue"
    author = "bz0qyz <bz0qyz@github.com>"
    owner = "Code Monkeys"
    tagline = "making tool development a little easier"
    copyright = f"\u00A9{datetime.datetime.today().year} {owner}"
    footer = f"{name} | {copyright}"
    
    """ CONSTANTS """
    LOG_LEVELS = ("debug", "info", "warning", "error")
