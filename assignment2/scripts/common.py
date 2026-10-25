"""Small helpers shared by all the scripts (paths, config, how to start Java)."""
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # .../assignment2
RESULTS_DIR = ROOT / "results"
RAW_DIR = RESULTS_DIR / "raw"
FIGURES_DIR = ROOT / "figures"
BUILD_DIR = ROOT / "build"
EXE = ".exe" if sys.platform == "win32" else ""


def tool(name):
    """Full path of a program: first from PATH, then from JAVA_HOME/bin (for java, javac)."""
    found = shutil.which(name)
    if found is None and os.environ.get("JAVA_HOME"):
        candidate = Path(os.environ["JAVA_HOME"]) / "bin" / (name + EXE)
        found = str(candidate) if candidate.exists() else None
    return found or name


def load_config():
    with open(ROOT / "config.json", encoding="utf-8") as f:
        return json.load(f)


def java_command(cfg):
    return [tool("java"), *cfg["java_options"], "-cp", str(BUILD_DIR), "Bench"]
