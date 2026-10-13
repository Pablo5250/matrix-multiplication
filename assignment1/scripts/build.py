"""Compile the C and Java programs into build/ using the flags in config.json."""
import shutil
import subprocess
import sys

from common import BUILD_DIR, EXE, ROOT, load_config, tool


def run(cmd):
    print("  $", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def main():
    cfg = load_config()
    BUILD_DIR.mkdir(exist_ok=True)

    cc = cfg["c_compiler"]
    if shutil.which(cc) is None:
        sys.exit(f"ERROR: C compiler '{cc}' not found in PATH (see README: Requirements).")
    c_dir = ROOT / "c"
    print("Building C ...")
    run([cc, *cfg["c_flags"], "-o", BUILD_DIR / ("bench_c" + EXE), c_dir / "bench.c", c_dir / "matmul.c"])
    run([cc, *cfg["c_flags"], "-o", BUILD_DIR / ("test_c" + EXE), c_dir / "test_matmul.c", c_dir / "matmul.c"])

    javac = tool("javac")
    if shutil.which(javac) is None:
        sys.exit("ERROR: 'javac' not found in PATH or JAVA_HOME (install a JDK, see README).")
    print("Building Java ...")
    java_out = BUILD_DIR / "java"
    java_out.mkdir(exist_ok=True)
    run([javac, "-encoding", "UTF-8", "-d", java_out, *sorted((ROOT / "java" / "src").glob("*.java"))])
    print("Build OK")


if __name__ == "__main__":
    main()
