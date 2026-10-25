"""Run every configuration of the study and measure time and memory.

Experiments (all settings in config.json):
  part_a          dense methods ijk / ikj / blocked, growing n
  block_size      blocked with tiles 32, 64, 128, 256 at one n
  part_b_density  CSR vs dense (blocked) at one n, growing density
  part_b_size     CSR vs dense (blocked) at one density, growing n

Each configuration is ONE new Java process (warm-up runs + measured runs). While it runs, this script
reads the PEAK MEMORY of the process from the operating system every 10 ms (psutil: peak working set
on Windows, RSS elsewhere). Budgets are declared in config.json before running: a configuration whose
predicted time (previous size x (n / previous n)^3) or dense memory (3 x 8n^2 bytes) is over the budget
is not started ("skipped_predicted_over_budget"); a running one that goes over is killed ("timeout" or
"memory_limit"). No times are invented.

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


def groups(cfg, quick):
    """List of (experiment, part, method, [(n, density_pct), ...]) in the order they run."""
    q = cfg["quick"]
    a_sizes = q["part_a_sizes"] if quick else cfg["part_a"]["sizes"]
    bs_n = q["block_size_n"] if quick else cfg["block_size_test"]["n"]
    bd_n = q["part_b_density_n"] if quick else cfg["part_b_density"]["n"]
    bd_dens = q["part_b_densities_pct"] if quick else cfg["part_b_density"]["densities_pct"]
    bsz_sizes = q["part_b_sizes"] if quick else cfg["part_b_size"]["sizes"]
    bsz_d = cfg["part_b_size"]["density_pct"]
    out = []
    for m in cfg["part_a"]["methods"]:
        out.append(("part_a", "dense", m, [(n, 100.0) for n in a_sizes]))
    for m in cfg["block_size_test"]["methods"]:
        out.append(("block_size", "dense", m, [(bs_n, 100.0)]))
    for m in cfg["part_b_density"]["methods"]:
        out.append(("part_b_density", "sparse", m, [(bd_n, d) for d in bd_dens]))
    for m in cfg["part_b_size"]["methods"]:
        out.append(("part_b_size", "sparse", m, [(n, bsz_d) for n in bsz_sizes]))
    return out


def peak_bytes(proc):
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
    warmup, reps = cfg["warmup_runs"], cfg["measured_runs"]
    budget = cfg["time_budget_seconds_per_configuration"]
    mem_budget = cfg["memory_budget_mb"] * 1024 * 1024
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    runs, files = [], []
    for experiment, part, method, points in groups(cfg, quick):
        previous = None          # (n, median seconds) of the last finished point, for the time prediction
        stop = False
        for n, dens in points:
            row = {"experiment": experiment, "part": part, "method": method, "n": n, "density_pct": dens,
                   "warmup_runs": warmup, "measured_runs": reps, "time_budget_s": budget,
                   "memory_budget_mb": cfg["memory_budget_mb"], "memory_metric": MEMORY_METRIC,
                   "predicted_total_s": "", "peak_memory_bytes": "", "wall_s": ""}
            if previous and previous[0] != n:
                pred = previous[1] * (n / previous[0]) ** 3 * (warmup + reps)
                row["predicted_total_s"] = f"{pred:.1f}"
                stop = stop or pred > budget
            if method != "csr" and 3 * 8 * n * n > mem_budget:
                stop = True
            label = f"{experiment:15s} {method:10s} n={n:6d} d={dens:g}%"
            if stop:
                row["status"] = "skipped_predicted_over_budget"
                runs.append(row)
                print(f"{label}  skipped (predicted over budget)")
                continue

            out_csv = RAW_DIR / f"times_{experiment}_{method}_n{n}_d{dens:g}.csv"
            args = [part, method, str(n)] + ([] if part == "dense" else [str(dens)])
            cmd = java_command(cfg) + args + [str(warmup), str(reps), str(out_csv)]
            print(f"{label}  running ...", flush=True)
            status, peak, wall = run_one(cmd, budget, mem_budget, RAW_DIR / f"log_{out_csv.stem}.txt")
            row.update(status=status, peak_memory_bytes=peak, wall_s=f"{wall:.2f}")
            runs.append(row)
            print(f"{'':45s}  {status}, wall {wall:.1f} s, peak memory {peak / 2**20:.0f} MiB", flush=True)
            if status in ("ok", "timeout", "memory_limit") and out_csv.exists():
                files.append((experiment, out_csv))
            if status == "ok":
                with open(out_csv, encoding="utf-8") as f:
                    t = [int(r["time_ns"]) for r in csv.DictReader(f) if r["run_type"] == "measured"]
                previous = (n, statistics.median(t) / 1e9)
            else:
                stop = True
            time.sleep(2)

    fields = ["experiment", "part", "method", "n", "density_pct", "status", "warmup_runs", "measured_runs",
              "wall_s", "predicted_total_s", "peak_memory_bytes", "memory_metric", "time_budget_s", "memory_budget_mb"]
    with open(RAW_DIR / "runs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(runs)

    # One file with every raw measurement (the per-configuration files are not kept in git)
    with open(RAW_DIR / "times.csv", "w", newline="", encoding="utf-8") as out:
        out.write("experiment,part,method,n,density_pct,run_type,rep,time_ns,checksum,nnz_a,nnz_b,nnz_c\n")
        for experiment, path in files:
            with open(path, encoding="utf-8") as f:
                next(f)
                for line in f:
                    out.write(f"{experiment},{line}")
    print("Wrote results/raw/runs.csv and results/raw/times.csv")


if __name__ == "__main__":
    main()
