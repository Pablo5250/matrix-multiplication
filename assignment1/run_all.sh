#!/usr/bin/env sh
# Full study on Linux/macOS:  ./run_all.sh   (or ./run_all.sh --quick)
set -e
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
python3 run_all.py "$@"
