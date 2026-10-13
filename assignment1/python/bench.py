"""Benchmark program for the Python implementation.

Usage: python bench.py N INPUT_DIR WARMUP REPS OUT_CSV [DUMP_FILE]

The timer only covers multiply() (the kernel, including allocating C).
Reading the input files happens before, outside the timed region.
Same arguments and CSV columns as the Java and C programs.
"""
import sys
import time
from pathlib import Path

from matmul import checksum, load_matrix, multiply, save_matrix


def main():
    n, input_dir, warmup, reps, out_csv = (int(sys.argv[1]), Path(sys.argv[2]),
                                           int(sys.argv[3]), int(sys.argv[4]), sys.argv[5])
    dump = sys.argv[6] if len(sys.argv) > 6 else None

    a = load_matrix(input_dir / f"A_n{n}.bin", n)
    b = load_matrix(input_dir / f"B_n{n}.bin", n)

    with open(out_csv, "w", encoding="utf-8") as out:
        out.write("language,n,run_type,rep,time_ns,checksum\n")
        c = None
        for r in range(warmup + reps):
            c = None                             # free the previous result (like free(c) in C)
            t0 = time.perf_counter_ns()          # monotonic, nanoseconds
            c = multiply(a, b)
            t1 = time.perf_counter_ns()
            s = checksum(c)                      # consume the result
            kind = "warmup" if r < warmup else "measured"
            rep = r if r < warmup else r - warmup
            out.write(f"python,{n},{kind},{rep},{t1 - t0},{s!r}\n")
            out.flush()

    if dump:
        save_matrix(dump, c)


if __name__ == "__main__":
    main()
