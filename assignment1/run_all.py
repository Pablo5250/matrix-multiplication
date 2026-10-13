"""Run the whole study in order. Usage:
    python run_all.py            full study (sizes from config.json)
    python run_all.py --quick    quick check with small sizes (a few seconds/minutes)
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
quick = ["--quick"] if "--quick" in sys.argv else []

STEPS = [
    ("1/7 Environment", ["scripts/collect_env.py"]),
    ("2/7 Generate shared input matrices", ["data/generate_inputs.py"]),
    ("3/7 Build C and Java", ["scripts/build.py"]),
    ("4/7 Unit tests", ["scripts/run_tests.py"]),
    ("5/7 Validation against NumPy", ["scripts/validate.py"]),
    ("6/7 Benchmarks (time + memory)", ["scripts/run_benchmarks.py", *quick]),
    ("7/7 Tables and figures", ["scripts/analyze.py"]),
]

for title, args in STEPS:
    print(f"\n===== {title} =====", flush=True)
    result = subprocess.run([sys.executable, str(ROOT / args[0]), *args[1:]], cwd=ROOT)
    if result.returncode != 0:
        sys.exit(f"\nSTOPPED: step '{title}' failed (see the message above).")
print("\nDone. Results in results/ and figures/.")
