"""Compile the Java code into build/."""
import shutil
import subprocess
import sys

from common import BUILD_DIR, ROOT, tool


def main():
    javac = tool("javac")
    if shutil.which(javac) is None:
        sys.exit("ERROR: 'javac' not found in PATH or JAVA_HOME (install a JDK, see README).")
    BUILD_DIR.mkdir(exist_ok=True)
    cmd = [javac, "-encoding", "UTF-8", "-d", str(BUILD_DIR), *map(str, sorted((ROOT / "java" / "src").glob("*.java")))]
    print("  $", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("Build OK")


if __name__ == "__main__":
    main()
