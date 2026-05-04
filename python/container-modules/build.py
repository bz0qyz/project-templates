#!/usr/bin/env python3
import os
import sys
import argparse
import tomllib
from pathlib import Path
from importlib.metadata import distribution
from PyInstaller.__main__ import run as pyinstaller_run
# ----------------------------------------------------------------------
base_path = Path(__file__).parent.resolve()
default_entrypoint = "src/__main__.py"
parser = argparse.ArgumentParser(description=f"pyinstaller builder")
parser.add_argument('-s', '--source-path',
                    metavar='/path/to/src', type=str, default=base_path,
                    help=f'Directory containing the source code to build. Default: {base_path}'
                    )
parser.add_argument('-b', '--build-path',
                    metavar='/path/to/build', type=str, default=base_path,
                    help=f'Directory where the build and dist folders will be created. Default: {base_path}'
                    )
parser.add_argument('-e', '--entrypoint',
                    metavar=default_entrypoint, type=str, default=default_entrypoint,
                    help=f'Directory containing the source code to build. Default: {default_entrypoint}'
                    )
parser.add_argument('-d', '--add-data',
                    metavar='/relative/path/to/data', type=str, default=[], action='append',
                    help=f'Files or Directories to add to the package. Default: None'
                    )
parser.add_argument('-l', '--log-level',
                    dest="log_level", default="INFO",
                    help='Logging level. Default: INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
                    )

args = parser.parse_args()
if not os.path.exists(args.source_path):
    print(f"[ERROR] Source path: '{args.source_path}' doesn't exist. Unable tp proceed.")
    sys.exit(1)

if not os.path.exists(os.path.join(args.source_path, "pyproject.toml")):
    print(f"[ERROR] project file ('pyproject.toml') not found is source: '{args.source_path}'. Unable tp proceed.")
    sys.exit(1)

if not os.path.exists(args.build_path):
    os.makedirs(args.build_path)

# Change into the source path directory
os.chdir(args.source_path)
build_path = os.path.join(args.build_path, "build")
dist_path = os.path.join(args.build_path, "dist")

# Load project metadata from pyinstaller.toml
config = tomllib.loads(Path("pyproject.toml").read_text())
meta = config["project"]
name = meta["name"]
pkg_name = name.replace("-", "_")

build_cfg = config.get("tool", {}).get("pyinstaller", {}).get("build", {})

# Required values
entry = build_cfg.get("entrypoint", args.entrypoint)
log_level = build_cfg.get("log_level", "INFO")
dist_info_path = distribution(name)._path

# ---- MAIN BUILD PROCESS ----
print(f"INFO: Building {name} v{meta['version']}")
# "--add-data", f"{os.path.join(base_path, "src", pkg_name)}.egg-info:{pkg_name}.egg-info",
opts = [
    entry , "--clean", "--log-level", args.log_level, "--name", name, '--noconfirm',
    "--distpath", f"{dist_path}", "--workpath", f"{build_path}",
    "--copy-metadata", name,
    "--add-data", f"{dist_info_path}:{Path(dist_info_path).name}"
    ]

# include datas from build_cfg
datas = build_cfg.get("datas", [])
for data_entry in datas:
    src, dest = data_entry
    if dest == ".":
        dest = os.path.basename(src)
    opts += ["--add-data", f"{src}:{dest}"]
    print("INFO: Adding data:", f"{src}:{dest}")

# Include package datas from args
for data_entry in args.add_data:
    datas.append(data_entry)

# Flags
if build_cfg.get("onefile", True):
    opts.append("--onefile")

if not build_cfg.get("console", False):
    opts.append("--noconsole")

icon = build_cfg.get("icon")
if icon and Path(icon).exists():
    opts += ["--icon", icon]

print("----------------------------------------")
print("INFO: Running PyInstaller with options:")
print("----------------------------------------")
for opt in opts:
    ln = "" if opt.startswith("--") else "\n"
    print("  ", opt, end=ln)
print("\n----------------------------------------")

try:
    pyinstaller_run(opts)
    # Rename output file to a generic name for the Containerfile to use
    os.rename(os.path.join(dist_path, name), os.path.join(dist_path, "app.bin"))
except Exception as e:
    print("[ERROR] Build failed:", e)
    exit(1)

print("\nINFO: Build complete – see ./dist\n")
