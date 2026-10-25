# Assignment 2: Optimised and Sparse Matrix Multiplication (Java)

Big Data, Individual Assignment 2, 2026-2027

Author: Pablo Castillo Garcerá

**Questions:** (A) how much faster is dense multiplication with a better loop order or with blocks?
(B) when most numbers are zero, when is a sparse format (CSR) better than a dense one?

**Report:** [`report/Assignment02_PabloCastilloGarcera_Report.pdf`](report/Assignment02_PabloCastilloGarcera_Report.pdf)

## Methods

| Method | What changes | Code |
|---|---|---|
| baseline i-j-k | nothing, the Java code of Assignment 1 | `DenseMultiply.ijk` |
| i-k-j | the two inner loops are swapped (reads B row by row) | `DenseMultiply.ikj` |
| blocked | i-k-j done in 64 × 64 tiles that stay in the cache | `DenseMultiply.blocked` |
| CSR | only the nonzeros are saved and multiplied (own code, no library) | `CsrMatrix.multiply` |

## Main results (AMD Ryzen 9 5900X, Windows 11, OpenJDK 25)

| n | baseline i-j-k | i-k-j | blocked |
|---:|---:|---:|---:|
| 1024 | 1.91 s | 0.14 s | 0.18 s |
| 2048 | 37.2 s | 2.92 s | 1.56 s |
| 4096 | skipped (> 20 min) | 48.8 s | 11.5 s |
| 8192 | skipped | skipped | 100 s |

* Blocking is 23.8 times faster than the baseline at n = 2048, and the only dense method that reached n = 8192.
* At n = 2048, CSR is faster than dense up to 25 % nonzeros; at 50 % dense is faster.
  At 0.1 % nonzeros CSR is about 2,800 times faster.
* The result is denser than the inputs: 1 % nonzeros in A and B give 18.5 % in C.
* At 0.1 % nonzeros, dense stopped at n = 8192 (time limit) and CSR reached n = 32768.

Full tables: [`results/summary.md`](results/summary.md).

## Folders

| Folder | What is inside |
|---|---|
| `java/src/` | `DenseMultiply` (3 dense methods), `CsrMatrix` (CSR format), `Bench` (measures one configuration), `Tests` |
| `scripts/` | Build, tests, run the benchmark (time, memory, limits), make the tables and figures |
| `results/` | Raw times (`raw/times.csv`), memory and status (`raw/runs.csv`), summary tables, computer info |
| `figures/` | The figures used in the report |
| `report/` | The report (PDF) and the link to this repository (TXT) |

All the settings (sizes, densities, seeds, number of runs, limits) are in [`config.json`](config.json).

## How to run it

You need Python 3.10+ and a JDK 11+ (`javac`, `java`).

On Windows, double-click:

* `quick_test.bat`: quick check with small sizes (about 1 minute)
* `run_all.bat`: the full experiment (about 45 minutes)

Or step by step, from this folder:

```sh
pip install -r requirements.txt
python scripts/collect_env.py      # computer and software -> results/environment.txt
python scripts/build.py            # compile the Java code
python scripts/run_tests.py        # correctness tests
python scripts/run_benchmarks.py   # time and memory -> results/raw/
python scripts/analyze.py          # tables and figures -> results/, figures/
```

One configuration can also be run alone, for example:

```sh
java -Xmx8g -cp build Bench dense blocked 2048 3 5 out.csv
java -Xmx8g -cp build Bench sparse csr 2048 1 3 5 out.csv
```
