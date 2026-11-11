# Assignment 3: Parallel Matrix Multiplication (Java)

Big Data, Individual Assignment 3, 2026-2027

Author: Pablo Castillo Garcerá

**Question:** how does the number of threads change the time of a dense matrix multiplication, and when does
running it in parallel really help?

## Methods

| Method | What it does | Code |
|---|---|---|
| sequential | the blocked method (tiles of 64 x 64) of Assignment 2, with no threads | `DenseMultiply.blocked` |
| parallel | the same code, but the rows of C are cut into chunks (4 per thread) and plain Java threads take the next free chunk | `ParallelMultiply.blocked` |

Both versions run the same method for each band of 64 rows (`DenseMultiply.blockedRows`), so the only difference
is the threads. A and B are only read and each row of C belongs to one chunk, so no two threads write the same
number. The result is exactly the same with any number of threads. The optional vectorisation part was not done.

## Main results (AMD Ryzen 9 5900X: 12 cores, 24 logical processors; Windows 11; OpenJDK 25)

Speedup S(p) = Tseq / Tp and efficiency E(p) = S(p) / p, with the median of 5 measured runs.

| n | sequential | 1 thread | 12 threads | 24 threads | best speedup |
|---:|---:|---:|---:|---:|---:|
| 256 | 2.1 ms | 2.8 ms | 0.79 ms | 1.5 ms | 2.7 (12 threads) |
| 1024 | 0.143 s | 0.149 s | 0.020 s | 0.019 s | 7.8 (32 threads) |
| 2048 | 1.32 s | 1.19 s | 0.166 s | 0.136 s | 9.8 (32 threads) |
| 8192 | 112 s | 113 s | 15.9 s | 11.1 s | 10.5 (32 threads) |

Full tables: [`results/summary.md`](results/summary.md).

## Folders

| Folder | What is inside |
|---|---|
| `java/src/` | `DenseMultiply` (sequential), `ParallelMultiply` (threads), `Bench` (measures one configuration), `Tests` (87 tests) |
| `scripts/` | Build, tests, run the benchmark (time, memory, CPU use, limits), make the tables and figures |
| `results/` | Raw times (`raw/times.csv`), memory, CPU time and status (`raw/runs.csv`), summary tables, computer info |
| `figures/` | Time, speedup, efficiency, one-thread overhead and memory |

All the settings (sizes, thread counts, seeds, runs, limits, Java options) are in [`config.json`](config.json).

## How to run it

You need Python 3.10+ and a JDK 11+ (`javac`, `java`). Close other programs first: the benchmark uses all the
cores, so other work changes the times.

On Windows, double-click:

* `quick_test.bat`: quick check with small sizes (about 2 minutes)
* `run_all.bat`: the full study (about 1 hour 10 minutes)

Or step by step, from this folder:

```sh
pip install -r requirements.txt
python scripts/collect_env.py      # computer and software -> results/environment.txt
python scripts/build.py            # compile the Java code
python scripts/run_tests.py        # correctness and thread-safety tests
python scripts/run_benchmarks.py   # time, memory and CPU use -> results/raw/
python scripts/analyze.py          # tables and figures -> results/, figures/
```

One configuration can also be run alone (method, n, threads, warm-up runs, measured runs, output file):

```sh
java -Xmx8g -XX:ParallelGCThreads=1 -XX:ConcGCThreads=1 -cp build Bench parallel 2048 12 3 5 out.csv
java -Xmx8g -XX:ParallelGCThreads=1 -XX:ConcGCThreads=1 -cp build Bench sequential 2048 1 3 5 out.csv
```

The Java options limit the garbage collector to one thread, so the thread count of each configuration is the
real one.
