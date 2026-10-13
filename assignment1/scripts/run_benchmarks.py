"""Run the benchmark of every (language, n) configuration and measure memory.

Each configuration is ONE new process that does the warm-up runs and the
measured runs. While it runs, this script asks the operating system for the
process's PEAK MEMORY every 10 ms (psutil):
  * Windows: peak working set (peak_wset = PeakWorkingSetSize)
  * Linux / macOS: resident set size (rss), the maximum of the samples
This is the memory of the whole process (interpreter / JVM / C runtime +
matrices), not only the arrays.

Budgets (config.json) are declared before running:
  * a configuration is not started if its predicted time (from the previous
    size, assuming n^3 growth) is over the time budget -> status "skipped_predicted_over_budget"
  * a running configuration is killed when it exceeds the time budget ("timeout")
    or the memory budget ("memory_limit"). No invented times are written.

Usage: python run_benchmarks.py [--quick]
"""
import csv
import statistics
import subprocess
import sys
import time

import psutil

from common import DATA_DIR, RAW_DIR, command_for, load_config

POLL_SECONDS = 0.01
MEMORY_METRIC = ("peak working set (psutil peak_wset)" if sys.platform == "win32"
                 else "max sampled RSS (psutil rss)")


def peak_bytes(proc):
    """Peak memory of a running process so far, as reported by the OS."""
    try:
        mi = proc.memory_info()
        return max(mi.rss, getattr(mi, "peak_wset", 0))
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0


def run_one(cmd, time_budget, mem_budget_bytes, log_path):
    """Start cmd, enforce the budgets, return (status, peak_bytes, wall_s)."""
    t0 = time.monotonic()
    peak, status = 0, None
    with open(log_path, "w", encoding="utf-8") as log:
        p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        proc = psutil.Process(p.pid)
        while p.poll() is None:
            peak = max(peak, peak_bytes(proc))
            if peak > mem_budget_bytes:
                status = "memory_limit"
                p.kill()
            elif time.monotonic() - t0 > time_budget:
                status = "timeout"
                p.kill()
            time.sleep(POLL_SECONDS)
    wall = time.monotonic() - t0
    status = status or ("ok" if p.returncode == 0 else f"error_{p.returncode}")
    if status.startswith("error"):
        print(open(log_path, encoding="utf-8").read())
    return status, peak, wall


def main():
    quick = "--quick" in sys.argv
    cfg = load_config()
    sizes = cfg["quick_sizes"] if quick else cfg["sizes"]
    reps = cfg["measured_runs"]
    budget = cfg["time_budget_seconds_per_configuration"]
    mem_budget = cfg["memory_budget_mb"] * 1024 * 1024
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    runs = []
    for lang in cfg["languages"]:
        warmup = cfg["warmup_runs"][lang]
        previous = None                     # (n, median seconds) of the last completed size
        stop = False
        for n in sorted(sizes):
            row = {"language": lang, "n": n, "warmup_runs": warmup, "measured_runs": reps,
                   "time_budget_s": budget, "memory_budget_mb": cfg["memory_budget_mb"],
                   "theoretical_array_bytes": 3 * 8 * n * n, "memory_metric": MEMORY_METRIC,
                   "predicted_total_s": "", "peak_memory_bytes": "", "wall_s": ""}
            if previous:
                pred = previous[1] * (n / previous[0]) ** 3 * (warmup + reps)
                row["predicted_total_s"] = f"{pred:.1f}"
                if pred > budget:
                    stop = True
            if 3 * 8 * n * n > mem_budget:
                stop = True
            if stop:
                row["status"] = "skipped_predicted_over_budget"
                runs.append(row)
                print(f"{lang:6s} n={n:5d}  skipped (predicted over budget)")
                continue

            out_csv = RAW_DIR / f"times_{lang}_n{n}.csv"
            cmd = command_for(lang, cfg) + [str(n), str(DATA_DIR), str(warmup), str(reps), str(out_csv)]
            print(f"{lang:6s} n={n:5d}  running {warmup} warm-up + {reps} measured ...", flush=True)
            status, peak, wall = run_one(cmd, budget, mem_budget, RAW_DIR / f"log_{lang}_n{n}.txt")
            row.update(status=status, peak_memory_bytes=peak, wall_s=f"{wall:.2f}")
            runs.append(row)
            print(f"{'':6s} {'':7s}  {status}, wall {wall:.1f} s, peak memory {peak / 2**20:.1f} MiB")

            if status == "ok":
                with open(out_csv, encoding="utf-8") as f:
                    times = [int(r["time_ns"]) for r in csv.DictReader(f) if r["run_type"] == "measured"]
                previous = (n, statistics.median(times) / 1e9)
            else:
                stop = True                  # larger sizes would fail too
            time.sleep(2)                    # short pause between configurations

    fields = ["language", "n", "status", "warmup_runs", "measured_runs", "wall_s", "predicted_total_s",
              "peak_memory_bytes", "memory_metric", "theoretical_array_bytes", "time_budget_s", "memory_budget_mb"]
    with open(RAW_DIR / "runs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(runs)

    # Merge every per-configuration CSV into one file with all raw measurements.
    with open(RAW_DIR / "times.csv", "w", newline="", encoding="utf-8") as out:
        out.write("language,n,run_type,rep,time_ns,checksum\n")
        for r in runs:
            path = RAW_DIR / f"times_{r['language']}_n{r['n']}.csv"
            # A configuration killed by a budget keeps the runs it completed before
            # the limit (they are real measurements; the summary shows how many).
            if r["status"] in ("ok", "timeout", "memory_limit") and path.exists():
                with open(path, encoding="utf-8") as f:
                    next(f)
                    out.writelines(f.readlines())
    print("Wrote results/raw/runs.csv and results/raw/times.csv")


if __name__ == "__main__":
    main()
