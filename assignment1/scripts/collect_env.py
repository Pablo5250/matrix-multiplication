"""Record the hardware and software environment into results/environment.txt."""
import platform
import shutil
import subprocess
import sys

import psutil

from common import RESULTS_DIR, load_config, tool


def first_lines(cmd, n=1):
    """Run a command and return the first n lines of its output (stdout or stderr)."""
    if shutil.which(cmd[0]) is None:
        return "not found"
    r = subprocess.run(cmd, capture_output=True, text=True)
    text = (r.stdout or r.stderr).strip().splitlines()
    return " | ".join(line.strip() for line in text[:n] if "JAVA_TOOL_OPTIONS" not in line)


def cpu_name():
    if sys.platform == "win32":
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "(Get-CimInstance Win32_Processor).Name"], capture_output=True, text=True)
        return r.stdout.strip() or platform.processor()
    if sys.platform.startswith("linux"):
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    return platform.processor()


def main():
    cfg = load_config()
    import matplotlib
    import numpy
    freq = psutil.cpu_freq()
    env = {
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "machine": platform.machine(),
        "cpu": cpu_name(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_processors": psutil.cpu_count(logical=True),
        "cpu_max_mhz": round(freq.max) if freq else None,
        "ram_gb": round(psutil.virtual_memory().total / 1e9, 1),
        "python": f"{platform.python_implementation()} {platform.python_version()}",
        "numpy": numpy.__version__, "psutil": psutil.__version__, "matplotlib": matplotlib.__version__,
        "java_runtime": first_lines([tool("java"), "-version"], 3),
        "javac": first_lines([tool("javac"), "-version"]),
        "java_options": cfg["java_options"],
        "c_compiler": first_lines([cfg["c_compiler"], "--version"]),
        "c_flags": cfg["c_flags"],
        "threads": "all three implementations are single-threaded (no parallel code, no BLAS in the kernels)",
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    with open(RESULTS_DIR / "environment.txt", "w", encoding="utf-8") as f:
        for k, v in env.items():
            f.write(f"{k:20s}: {v}\n")
    for k, v in env.items():
        print(f"{k:20s}: {v}")


if __name__ == "__main__":
    main()
