"""Run every configuration of the study and measure time, memory and CPU use.

Each configuration (size n, method, thread count p) is ONE new Java process: warm-up runs + measured runs.
The sequential baseline runs first, then the parallel method with each thread count (see config.json).

While a process runs, this script reads from the operating system every 10 ms its PEAK MEMORY (psutil:
peak working set on Windows, RSS elsewhere) and its CPU TIME. Budgets are declared in config.json before
running: a configuration whose predicted time (same method and threads at the previous size x
(n / previous n)^3) is over the budget is not started ("skipped_predicted_over_budget"); a running one
that goes over is killed ("timeout" or "memory_limit"). No times are invented.

Usage: python run_benchmarks.py [--quick]
"""
import csv
import statistics
import subprocess
import sys
import time

import psutil

from common import RAW_DIR, java_command, load_config

POLL_SECONDS = 0.01
MEMORY_METRIC = ("peak working set (psutil peak_wset)" if sys.platform == "win32"
                 else "max sampled RSS (psutil rss)")


def peak_bytes(proc):
    try:
        mi = proc.memory_info()
        return max(mi.rss, getattr(mi, "peak_wset", 0))
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0


def cpu_seconds(proc, last):
    try:
        t = proc.cpu_times()
        return t.user + t.system
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return last


def run_one(cmd, time_budget, mem_budget_bytes, log_path):
    """Start cmd, enforce the budgets, return (status, peak_bytes, wall_s, cpu_s)."""
    t0 = time.monotonic()
    peak, cpu, status = 0, 0.0, None
    with open(log_path, "w", encoding="utf-8") as log:
        p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        proc = psutil.Process(p.pid)
        while p.poll() is None:
            peak = max(peak, peak_bytes(proc))
            cpu = cpu_seconds(proc, cpu)
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
    return status, peak, wall, cpu


def main():
    quick = "--quick" in sys.argv
    cfg = load_config()
    reps = cfg["measured_runs"]
    budget = cfg["time_budget_seconds_per_configuration"]
    mem_budget = cfg["memory_budget_mb"] * 1024 * 1024
    sizes = cfg["quick"]["sizes"] if quick else cfg["sizes"]
    threads = cfg["quick"]["thread_counts"] if quick else cfg["thread_counts"]
    configurations = [("sequential", 1)] + [("parallel", p) for p in threads]
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    runs, files = [], []
    previous = {}            # (method, p) -> (n, median seconds) of the last finished size, for the prediction
    stopped = set()
    for n in sizes:
        warmup = cfg["warmup_runs_small_sizes"].get(str(n), cfg["warmup_runs"])   # small sizes finish too fast to warm up
        for method, p in configurations:
            key = (method, p)
            row = {"method": method, "n": n, "threads": p, "warmup_runs": warmup, "measured_runs": reps,
                   "time_budget_s": budget, "memory_budget_mb": cfg["memory_budget_mb"],
                   "memory_metric": MEMORY_METRIC, "predicted_total_s": "", "peak_memory_bytes": "",
                   "wall_s": "", "cpu_s": ""}
            if key in previous:
                pred = previous[key][1] * (n / previous[key][0]) ** 3 * (warmup + reps)
                row["predicted_total_s"] = f"{pred:.1f}"
                if pred > budget:
                    stopped.add(key)
            label = f"{method:10s} n={n:6d} p={p:3d}"
            if key in stopped:
                row["status"] = "skipped_predicted_over_budget"
                runs.append(row)
                print(f"{label}  skipped (predicted over budget)")
                continue

            out_csv = RAW_DIR / f"times_{method}_n{n}_p{p}.csv"
            cmd = java_command(cfg) + [method, str(n), str(p), str(warmup), str(reps), str(out_csv)]
            print(f"{label}  running ...", flush=True)
            status, peak, wall, cpu = run_one(cmd, budget, mem_budget, RAW_DIR / f"log_{out_csv.stem}.txt")
            row.update(status=status, peak_memory_bytes=peak, wall_s=f"{wall:.2f}", cpu_s=f"{cpu:.2f}")
            runs.append(row)
            print(f"{'':28s}  {status}, wall {wall:.1f} s, cpu {cpu:.1f} s, peak memory {peak / 2**20:.0f} MiB", flush=True)
            if status in ("ok", "timeout", "memory_limit") and out_csv.exists():
                files.append(out_csv)
            if status == "ok":
                with open(out_csv, encoding="utf-8") as f:
                    t = [int(r["time_ns"]) for r in csv.DictReader(f) if r["run_type"] == "measured"]
                previous[key] = (n, statistics.median(t) / 1e9)
            else:
                stopped.add(key)
            time.sleep(2)

    fields = ["method", "n", "threads", "status", "warmup_runs", "measured_runs", "wall_s", "cpu_s",
              "predicted_total_s", "peak_memory_bytes", "memory_metric", "time_budget_s", "memory_budget_mb"]
    with open(RAW_DIR / "runs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(runs)

    # One file with every raw measurement (the per-configuration files are not kept in git)
    with open(RAW_DIR / "times.csv", "w", newline="", encoding="utf-8") as out:
        out.write("method,n,threads,numeric_type,run_type,rep,time_ns,checksum\n")
        for path in files:
            with open(path, encoding="utf-8") as f:
                next(f)
                out.writelines(f)
    print(f"Wrote {RAW_DIR / 'runs.csv'} and {RAW_DIR / 'times.csv'}")


if __name__ == "__main__":
    main()
