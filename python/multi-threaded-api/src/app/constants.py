from __future__ import annotations
from pathlib import Path

""" CONSTANTS """
BASE_DIR: Path = Path(__file__).resolve().parent.parent
LOG_LEVELS = ("debug", "info", "warning", "error")
LOG_FORMATS = {
    "default": "%(asctime)s - %(levelname)-8s: %(message)s",
    "minimal": "%(levelname)-8s: %(message)s",
    "debug": "%(levelname)-8s: %(name)s (%(module)s:%(lineno)d ): %(message)s",
    "json": '{"ts": "%(asctime)s", "lvl": "%(levelname)s", "logger": "%(name)s", "msg": "%(message)s"}',
}