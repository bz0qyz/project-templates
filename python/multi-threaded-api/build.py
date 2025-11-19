#!/usr/bin/env python3
import os
import subprocess
import tomllib
from pathlib import Path
from importlib.metadata import distribution
from PyInstaller.__main__ import run as pyinstaller_run
# ----------------------------------------------------------------------
base_path = Path(__file__).parent.resolve()
build_path = os.path.join(base_path, "build")
dist_path = os.path.join(base_path, "dist")

config = tomllib.loads(Path("pyproject.toml").read_text())
meta = config["project"]
name = meta["name"]
pkg_name = name.replace("-", "_")

build_cfg = config.get("tool", {}).get("pyinstaller", {}).get("build", {})

# Required values
entry = build_cfg.get("entrypoint", "src/__main__.py")
log_level = build_cfg.get("log_level", "INFO")
dist_info_path = distribution(name)._path

# ---- MAIN BUILD PROCESS ----

print(f"INFO: Building {name} v{meta['version']}")

opts = [
    entry , "--clean", "--log-level", log_level, "--name", name,
    "--distpath", f"{dist_path}", "--workpath", f"{build_path}",
    "--add-data", f"{os.path.join(base_path, "src", pkg_name)}.egg-info:{pkg_name}.egg-info"
    ]

# Include package data
opts += ["--add-data", f"{dist_info_path}:{Path(dist_info_path).name}"]
print("INFO: Adding data:", f"{dist_info_path}:{Path(dist_info_path).name}")

# include datas from build_cfg
datas = build_cfg.get("datas", [])
for data_entry in datas:
    src, dest = data_entry
    if dest == ".":
        dest = os.path.basename(src)
    opts += ["--add-data", f"{src}:{dest}"]
    print("INFO: Adding data:", f"{src}:{dest}")

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
