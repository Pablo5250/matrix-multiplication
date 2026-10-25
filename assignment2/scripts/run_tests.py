"""Run the correctness tests (known results, identity, zero, all methods = baseline, CSR = dense)."""
import subprocess

from common import BUILD_DIR, ROOT, tool

if __name__ == "__main__":
    subprocess.run([tool("java"), "-cp", str(BUILD_DIR), "Tests"], cwd=ROOT, check=True)
