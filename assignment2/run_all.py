"""Run the whole study in order. Usage:
    python run_all.py            full study (about 45 minutes)
    python run_all.py --quick    quick check with small sizes (about 1 minute)
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
quick = ["--quick"] if "--quick" in sys.argv else []

STEPS = [
    ("1/5 Environment", ["scripts/collect_env.py"]),
    ("2/5 Build Java", ["scripts/build.py"]),
    ("3/5 Tests", ["scripts/run_tests.py"]),
    ("4/5 Benchmarks (time + memory)", ["scripts/run_benchmarks.py", *quick]),
    ("5/5 Tables and figures", ["scripts/analyze.py"]),
]

for title, args in STEPS:
    print(f"\n===== {title} =====", flush=True)
    result = subprocess.run([sys.executable, str(ROOT / args[0]), *args[1:]], cwd=ROOT)
    if result.returncode != 0:
        sys.exit(f"\nSTOPPED: step '{title}' failed (see the message above).")
print("\nDone. Results in results/ and figures/.")
