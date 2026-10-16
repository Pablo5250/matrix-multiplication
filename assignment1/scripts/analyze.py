"""Turn the raw measurements into tables and figures.

Inputs : results/raw/times.csv, results/raw/runs.csv  (written by run_benchmarks.py)
Outputs: results/summary.csv     median, IQR, ... per (language, n)
         results/summary.md      the same table in Markdown
         figures/*.png
Warm-up runs are excluded; every measured run is used (no outlier removal).
"""
import csv
import math
import statistics
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from common import FIGURES_DIR, RAW_DIR, RESULTS_DIR, input_paths, load_config, read_matrix_numpy  # noqa: E402

COLORS = {"c": "#2a78d6", "java": "#eb6834", "python": "#1baf7a"}
MARKERS = {"c": "o", "java": "s", "python": "^"}
NAMES = {"c": "C", "java": "Java", "python": "Python"}


def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def quartiles(values):
    if len(values) < 2:                      # e.g. a configuration stopped by the time budget
        return values[0], values[0]
    q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return q1, q3


def reference_checksums(sizes):
    """Sum of NumPy's A @ B for each size (used to check the programs' checksums)."""
    ref = {}
    for n in sizes:
        pa, pb = input_paths(n)
        ref[n] = float((read_matrix_numpy(pa, n) @ read_matrix_numpy(pb, n)).sum())
    return ref


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cfg = load_config()
    times = [r for r in read_csv(RAW_DIR / "times.csv") if r["run_type"] == "measured"]
    runs = read_csv(RAW_DIR / "runs.csv")
    langs = [l for l in cfg["languages"]]

    samples = defaultdict(list)
    checks = defaultdict(list)
    for r in times:
        key = (r["language"], int(r["n"]))
        samples[key].append(int(r["time_ns"]) / 1e9)
        checks[key].append(float(r["checksum"]))
    ref = reference_checksums(sorted({n for _, n in samples}))
    mem = {(r["language"], int(r["n"])): r for r in runs}

    # ---- summary table ------------------------------------------------------
    summary = []
    for (lang, n) in sorted(samples, key=lambda k: (langs.index(k[0]), k[1])):
        s = samples[(lang, n)]
        q1, q3 = quartiles(s)
        med = statistics.median(s)
        c_med = statistics.median(samples[("c", n)]) if ("c", n) in samples else math.nan
        ok = all(abs(x - ref[n]) <= cfg["rtol"] * abs(ref[n]) for x in checks[(lang, n)])
        peak = mem[(lang, n)]["peak_memory_bytes"]
        summary.append({
            "language": lang, "n": n, "measured_runs": len(s),
            "median_s": med, "q1_s": q1, "q3_s": q3, "iqr_s": q3 - q1,
            "min_s": min(s), "max_s": max(s),
            "ns_per_inner_iteration": med / n**3 * 1e9,
            "relative_to_c": med / c_med,
            "peak_memory_mib": int(peak) / 2**20 if peak else math.nan,
            "theoretical_arrays_mib": 3 * 8 * n * n / 2**20,
            "checksum_ok": ok,
        })
    with open(RESULTS_DIR / "summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)

    # ---- Markdown table (easy to read on GitHub) ----------------------------
    with open(RESULTS_DIR / "summary.md", "w", encoding="utf-8") as f:
        f.write("| Language | n | runs | median (s) | IQR (s) | peak memory (MiB) | result OK |\n")
        f.write("|---|---:|---:|---:|---:|---:|:-:|\n")
        for r in summary:
            f.write(f"| {NAMES[r['language']]} | {r['n']} | {r['measured_runs']} | {r['median_s']:.4g} | "
                    f"{r['iqr_s']:.2g} | {r['peak_memory_mib']:.1f} | {'OK' if r['checksum_ok'] else 'FAIL'} |\n")
        f.write("\n| Language | n | status | predicted total (s) |\n|---|---:|---|---:|\n")
        for r in runs:
            if r["status"] != "ok":
                f.write(f"| {NAMES[r['language']]} | {r['n']} | {r['status']} | {r['predicted_total_s'] or '-'} |\n")

    make_figures(summary, langs)
    print(open(RESULTS_DIR / "summary.md", encoding="utf-8").read())


def style(ax, xlabel, ylabel, title):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left", fontsize=12)
    ax.grid(True, which="major", color="#dddddd", linewidth=0.8)
    ax.grid(True, which="minor", color="#f0f0f0", linewidth=0.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def make_figures(summary, langs):
    FIGURES_DIR.mkdir(exist_ok=True)
    by_lang = {l: [r for r in summary if r["language"] == l] for l in langs}
    all_n = sorted({r["n"] for r in summary})

    # 1) Runtime vs n (log-log) with IQR bars and an n^3 reference line
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    for l in langs:
        rows = by_lang[l]
        if not rows:
            continue
        n = [r["n"] for r in rows]
        med = [r["median_s"] for r in rows]
        err = [[r["median_s"] - r["q1_s"] for r in rows], [r["q3_s"] - r["median_s"] for r in rows]]
        ax.errorbar(n, med, yerr=err, color=COLORS[l], marker=MARKERS[l], markersize=6,
                    linewidth=2, capsize=3, label=NAMES[l])
    c_rows = by_lang.get("c") or next(v for v in by_lang.values() if v)
    n0, t0 = c_rows[0]["n"], c_rows[0]["median_s"]
    ref_n = np.array(all_n, dtype=float)
    ax.plot(ref_n, t0 * (ref_n / n0) ** 3, linestyle="--", color="#888888", linewidth=1.2, label="grows like n³")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(all_n)
    ax.set_xticklabels([str(x) for x in all_n])
    style(ax, "matrix size n (n × n)", "median time per multiplication (s)",
          "Runtime vs matrix size (median, bars = IQR)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "runtime_loglog.png")
    plt.close(fig)

    # 2) Peak process memory vs n, with the theoretical size of the three arrays
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    for l in langs:
        rows = [r for r in by_lang[l] if not math.isnan(r["peak_memory_mib"])]
        if rows:
            ax.plot([r["n"] for r in rows], [r["peak_memory_mib"] for r in rows], color=COLORS[l],
                    marker=MARKERS[l], markersize=6, linewidth=2, label=NAMES[l])
    ax.plot(all_n, [3 * 8 * n * n / 2**20 for n in all_n], linestyle="--", color="#888888",
            linewidth=1.2, label="only the 3 matrices (8 bytes per number)")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(all_n)
    ax.set_xticklabels([str(x) for x in all_n])
    style(ax, "matrix size n (n × n)", "peak process memory (MiB)", "Peak memory of each program")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "memory.png")
    plt.close(fig)
    print("Wrote figures/runtime_loglog.png, figures/memory.png")


if __name__ == "__main__":
    main()
