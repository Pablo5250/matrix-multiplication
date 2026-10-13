# Assignment 1 — Basic Matrix Multiplication in Python, Java and C

Big Data · Grado en Ciencia e Ingeniería de Datos · ULPGC · 2026-2027
Author: Pablo Castillo Garcerá

**Research question.** How does the matrix size *n* affect the runtime and the memory use of the
same naive triple-loop matrix multiplication written in Python, Java and C, on one machine?

**Report:** [`report/Assignment01_CastilloGarcera_Report.pdf`](report/Assignment01_CastilloGarcera_Report.pdf)

## Main results (AMD Ryzen 9 5900X, Windows 11)

| n | C | Java | Python |
|---:|---:|---:|---:|
| 256 | 24.8 ms | 11.8 ms | 1.20 s |
| 512 | 0.59 s | 0.14 s | 10.9 s |
| 1024 | 4.90 s | 1.73 s | 98.6 s |
| 2048 | 40.5 s | 33.5 s | skipped (predicted 4,733 s > 1,200 s budget) |

Median of 5 measured runs. Full table: [`results/summary.md`](results/summary.md).

* Time grows close to n³ in the three languages; Python is 18-190 times slower than C.
* Java is faster than C at these sizes because they are powers of two: in C the column accesses of B
  fall into the same cache sets. At n-1 and n+1 C is 6-7 times faster than at n and faster than Java
  (`scripts/extra_power_of_two.py`, [`results/extra_power_of_two.csv`](results/extra_power_of_two.csv)).

## What is compared

| | Python | Java | C |
|---|---|---|---|
| Algorithm | triple loop, order i-j-k | triple loop, order i-j-k | triple loop, order i-j-k |
| Work | n³ multiply-adds | n³ multiply-adds | n³ multiply-adds |
| Numeric type | `float` (64-bit double) | `double` | `double` |
| Storage | list of lists of float objects | `double[][]` (array of row arrays) | one contiguous `double*` block, row-major |
| Runs on | CPython interpreter | JVM (JIT compiler) | native code (`gcc -O2`) |
| Timer | `time.perf_counter_ns()` | `System.nanoTime()` | `QueryPerformanceCounter` (Windows) / `clock_gettime(CLOCK_MONOTONIC)` |

No optimised library is used inside the compared code. NumPy is used only to generate the inputs and
as the reference result for the correctness check.

## Measurement protocol

* **Same inputs:** `data/generate_inputs.py` writes A and B for every size (NumPy PCG64, seed = 42 + n,
  uniform values in [0, 1), float64 little-endian, row-major, no header). All three programs read
  these files, so they multiply exactly the same numbers. `data/manifest.json` stores the SHA-256 of every file.
* **Timer boundary:** only the call to `multiply()`. It includes allocating the output matrix C and
  excludes reading the input files.
* **Runs:** each (language, n) is one new process with `warmup_runs` warm-up multiplications
  (C 1, Java 3, Python 1) followed by 5 measured ones. Warm-ups are kept in the raw CSV but marked
  `warmup` and excluded from the analysis.
* **Result is used:** after every run the checksum (sum of all elements of C) is computed and saved,
  and compared with NumPy's result.
* **Memory:** peak memory of the whole benchmark process, read from the operating system every
  10 ms with `psutil`. Windows: peak working set (`peak_wset`); Linux/macOS: largest sampled RSS. It includes the interpreter/JVM, so it is
  compared with the theoretical size of the three matrices, 3 · 8n² bytes.
* **Budgets (declared before running):** 1200 s per configuration and 4096 MB. A size whose predicted
  time (previous median × (n/n_prev)³ × runs) exceeds the budget is not started and is reported as
  `skipped_predicted_over_budget`; a run that goes over a budget is killed and reported as `timeout`
  or `memory_limit`. No times are invented.
* **Statistics:** median and interquartile range (IQR) of the 5 measured runs; all raw values are kept.

All the settings are in [`config.json`](config.json).

## Correctness

* Unit tests in each language: known 2×2 and 3×3 products, A·I = A, I·A = A, A·0 = 0, 1×1 case.
* Cross-check (`scripts/validate.py`): for n = 16, 64, 128 every program writes its full C, which is
  compared with NumPy `A @ B` using `np.allclose(rtol=1e-9, atol=1e-12)`. The inputs are positive,
  so the expected relative rounding error is about n · 1.1·10⁻¹⁶ (< 10⁻¹³ for these sizes); 10⁻⁹ is a
  safe margin that would still catch any real bug. The script also checks whether the three
  languages give bit-identical results (they should, because they add in the same order).

## Requirements

* Python 3.10+ (CPython) with `pip`
* JDK 11+ (`javac` and `java` in PATH, or the `JAVA_HOME` variable set)
* A C compiler: `gcc` in PATH (on Windows, e.g. MinGW-w64 from MSYS2 or WinLibs)

`pip install -r requirements.txt` installs numpy, psutil, matplotlib and python-docx (versions used: see `results/environment.txt`). Tested with Python 3.14.3, OpenJDK 25.0.1 and gcc 16.2.0 (WinLibs).

## How to run

Windows:

```bat
quick_test.bat      :: small sizes only, about one minute
run_all.bat         :: full study
```

Linux/macOS:

```sh
./run_all.sh --quick
./run_all.sh
```

Or step by step (any OS), from this folder:

```sh
python scripts/collect_env.py        # hardware and software -> results/environment.*
python data/generate_inputs.py       # shared input matrices -> data/inputs/
python scripts/build.py              # gcc -O2 -std=c11 and javac -> build/
python scripts/run_tests.py          # unit tests of the three implementations
python scripts/validate.py           # comparison with NumPy -> results/validation.csv
python scripts/run_benchmarks.py     # time + memory -> results/raw/
python scripts/analyze.py            # tables and figures -> results/, figures/
python scripts/extra_power_of_two.py # extra experiment: n-1, n, n+1 for C and Java
python report/build_report.py        # report .docx from the results (needs python-docx)
```

PDF: `soffice --headless --convert-to pdf --outdir report report/Assignment01_CastilloGarcera_Report.docx`

Each benchmark program can also be run alone, with the same arguments in the three languages:

```sh
build/bench_c   N data/inputs WARMUP REPS out.csv
java -Xmx4g -cp build/java Bench N data/inputs WARMUP REPS out.csv
python python/bench.py N data/inputs WARMUP REPS out.csv
```

## Outputs

| File | Content |
|---|---|
| `results/raw/times.csv` | every run: language, n, run_type (warmup/measured), rep, time_ns, checksum |
| `results/raw/runs.csv` | one row per configuration: status, peak memory, budgets, predicted time |
| `results/summary.csv`, `results/summary.md` | median, IQR, min, max, ns per inner iteration, ratio to C, memory |
| `results/slopes.csv` | fitted exponent *b* in time ≈ a · nᵇ (sizes ≥ 256) |
| `results/validation.csv` | errors against NumPy and the bit-identical check |
| `results/environment.txt` | CPU, cores, RAM, OS, Python, Java, gcc versions and flags |
| `results/extra_power_of_two.csv` | extra experiment: C and Java at n-1, n, n+1 |
| `figures/*.png` | runtime (log-log), time per inner iteration, peak memory, power-of-two experiment |

## Repository layout

```
assignment1/
├── config.json            all experiment settings
├── run_all.py / .bat / .sh
├── data/generate_inputs.py
├── python/                matmul.py, bench.py, test_matmul.py
├── java/src/              MatMul.java, Bench.java, MatMulTest.java
├── c/                     matmul.c/.h, bench.c, test_matmul.c
├── scripts/               build, tests, validation, benchmark runner, analysis, environment
├── results/               raw CSVs and summaries
├── figures/               plots used in the report
└── report/                build_report.py, text.py and the report (.docx, .pdf)
```
