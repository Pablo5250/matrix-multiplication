"""Run the unit tests of the three implementations (identity, zero, known results)."""
import subprocess
import sys

from common import BUILD_DIR, EXE, ROOT, tool


def main():
    steps = [
        ("Python", [sys.executable, "-m", "unittest", "-v", "test_matmul"], ROOT / "python"),
        ("Java", [tool("java"), "-cp", str(BUILD_DIR / "java"), "MatMulTest"], ROOT),
        ("C", [str(BUILD_DIR / ("test_c" + EXE))], ROOT),
    ]
    for name, cmd, cwd in steps:
        print(f"--- {name} tests")
        subprocess.run(cmd, cwd=cwd, check=True)
    print("All unit tests passed")


if __name__ == "__main__":
    main()
