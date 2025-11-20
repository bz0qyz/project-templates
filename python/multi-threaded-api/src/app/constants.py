from __future__ import annotations
from pathlib import Path

""" CONSTANTS """
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVELS = ("debug", "info", "warning", "error")
LOG_FORMATS =("default", "minimal", "debug", "json")