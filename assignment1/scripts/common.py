"""Small helpers shared by all the scripts (paths, config, reading matrices)."""
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # .../assignment1
DATA_DIR = ROOT / "data" / "inputs"
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


def input_paths(n):
    """Paths of the shared A and B matrices for size n."""
    return DATA_DIR / f"A_n{n}.bin", DATA_DIR / f"B_n{n}.bin"


def read_matrix_numpy(path, n):
    """Read a raw little-endian float64 n x n matrix (row-major) with NumPy."""
    import numpy as np
    return np.fromfile(path, dtype="<f8").reshape(n, n)


def command_for(language, cfg):
    """Command line that starts the benchmark program of one language."""
    if language == "c":
        return [str(BUILD_DIR / ("bench_c" + EXE))]
    if language == "java":
        return [tool("java"), *cfg["java_options"], "-cp", str(BUILD_DIR / "java"), "Bench"]
    if language == "python":
        # bench.py only needs the standard library. Use the base interpreter so that,
        # inside a Windows virtual environment, we measure python.exe itself and not
        # the small launcher process that a venv puts in front of it.
        python = getattr(sys, "_base_executable", None) or sys.executable
        return [python, str(ROOT / "python" / "bench.py")]
    raise ValueError(language)
