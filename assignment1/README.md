# Assignment 1: Basic Matrix Multiplication in Python, Java and C

Big Data, Individual Assignment 1, 2026-2027

Author: Pablo Castillo Garcerá

**Question:** how do time and memory grow with the matrix size n, when the same basic algorithm
(three loops, n³ operations) is written in Python, Java and C?

**Report:** [`report/Assignment01_PabloCastilloGarcera_Report.pdf`](report/Assignment01_PabloCastilloGarcera_Report.pdf)

## Main results (AMD Ryzen 9 5900X, Windows 11)

| n | C | Java | Python |
|---:|---:|---:|---:|
| 256 | 24.8 ms | 11.8 ms | 1.20 s |
| 512 | 0.59 s | 0.14 s | 10.9 s |
| 1024 | 4.90 s | 1.73 s | 98.6 s |
| 2048 | 40.5 s | 33.5 s | skipped (more than the 20 min limit) |

Median of 5 runs. Full table: [`results/summary.md`](results/summary.md).

* The time grows like n³ in the three languages. Python is 18-190 times slower than C.
* Java is faster than C here only because the sizes are powers of two (a cache problem in C).
  With n-1 or n+1, C is 6-7 times faster and faster than Java.

## Folders

| Folder | What is inside |
|---|---|
| `python/`, `java/src/`, `c/` | The multiplication (`matmul`), the program that measures it (`bench`) and the tests |
| `data/` | `generate_inputs.py` creates the matrices A and B (same files for the 3 languages) |
| `scripts/` | Build, tests, check against NumPy, run the benchmark, make the tables and figures |
| `results/` | Raw times (`raw/times.csv`), memory and status (`raw/runs.csv`), summary tables, computer info |
| `figures/` | The figures used in the report |
| `report/` | The report (PDF), the presentation (PDF) and the link to this repository (TXT) |

All the settings (sizes, number of runs, time limit) are in [`config.json`](config.json).

## How to run it

You need Python 3.10+, a JDK 11+ (`javac`, `java`) and `gcc`.

On Windows, double-click:

* `quick_test.bat`: quick check with small sizes (about 1 minute)
* `run_all.bat`: the full experiment (about 40 minutes)

Or step by step, from this folder:

```sh
pip install -r requirements.txt
python scripts/collect_env.py        # computer and software -> results/environment.txt
python data/generate_inputs.py       # matrices A and B -> data/inputs/
python scripts/build.py              # compile C (gcc -O2) and Java
python scripts/run_tests.py          # unit tests in the 3 languages
python scripts/validate.py           # compare with NumPy -> results/validation.csv
python scripts/run_benchmarks.py     # time and memory -> results/raw/
python scripts/analyze.py            # tables and figures -> results/, figures/
python scripts/extra_power_of_two.py # extra test with n-1, n, n+1
```

The input matrices are not uploaded because they are big; `generate_inputs.py` creates exactly
the same ones again (fixed seed, checked with `data/manifest.json`).
