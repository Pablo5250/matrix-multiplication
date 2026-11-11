"""Turn the raw measurements into tables and figures.

Inputs : results/raw/times.csv, results/raw/runs.csv (written by run_benchmarks.py)
Outputs: results/summary.csv, results/summary.md, figures/*.png
Warm-up runs are excluded; every measured run is used (no outlier removal).

Metrics: speedup S(p) = Tseq(n) / Tp(n) and efficiency E(p) = S(p) / p, where Tseq is the median time of the
sequential baseline and Tp the median time of the parallel method with p threads, at the same n.
"""
import csv
import statistics
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from common import FIGURES_DIR, RAW_DIR, RESULTS_DIR  # noqa: E402

PHYSICAL_CORES, LOGICAL_PROCESSORS = 12, 24
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]    # fixed order, checked for colour blindness
INK, MUTED, GRID = "#1b2430", "#52514e", "#e6e4de"
plt.rcParams.update({"font.size": 11, "axes.edgecolor": "#c9c7c0", "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED})


def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def quartiles(v):
    if len(v) < 2:
        return v[0], v[0]
    q1, _, q3 = statistics.quantiles(v, n=4, method="inclusive")
    return q1, q3


def style(ax, xlabel, ylabel, title):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left", fontsize=12, color=INK)
    ax.grid(True, which="major", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / name, dpi=150)
    plt.close(fig)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    runs = {(r["method"], int(r["n"]), int(r["threads"])): r for r in read_csv(RAW_DIR / "runs.csv")}
    meas, checks = defaultdict(list), defaultdict(set)
    for r in read_csv(RAW_DIR / "times.csv"):
        key = (r["method"], int(r["n"]), int(r["threads"]))
        if r["run_type"] == "measured":
            meas[key].append(int(r["time_ns"]) / 1e9)
            checks[key].add(r["checksum"])

    summary = []
    for key in sorted(meas):
        method, n, p = key
        s = meas[key]
        q1, q3 = quartiles(s)
        seq = statistics.median(meas[("sequential", n, 1)])
        median = statistics.median(s)
        speedup = seq / median
        run = runs[key]
        summary.append({
            "method": method, "n": n, "threads": p, "runs": len(s), "median_s": median, "q1_s": q1, "q3_s": q3,
            "iqr_s": q3 - q1, "min_s": min(s), "max_s": max(s), "speedup": speedup, "efficiency": speedup / p,
            "data_storage_mib": 3 * 8 * n * n / 2**20, "peak_memory_mib": int(run["peak_memory_bytes"]) / 2**20,
            "cpu_use": float(run["cpu_s"]) / float(run["wall_s"]),
            "same_result_as_sequential": checks[key] == checks[("sequential", n, 1)],
        })
    RESULTS_DIR.mkdir(exist_ok=True)
    with open(RESULTS_DIR / "summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)

    with open(RESULTS_DIR / "summary.md", "w", encoding="utf-8") as f:
        f.write("| method | n | threads | runs | median (s) | IQR (s) | speedup | efficiency | peak memory (MiB) | CPU use (cores) | same result |\n")
        f.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:-:|\n")
        for r in summary:
            f.write(f"| {r['method']} | {r['n']} | {r['threads']} | {r['runs']} | {r['median_s']:.4g} | {r['iqr_s']:.2g} | "
                    f"{r['speedup']:.2f} | {r['efficiency']:.2f} | {r['peak_memory_mib']:.0f} | {r['cpu_use']:.1f} | "
                    f"{'yes' if r['same_result_as_sequential'] else 'NO'} |\n")
        skipped = [r for r in runs.values() if r["status"] != "ok"]
        if skipped:
            f.write("\n| method | n | threads | status | predicted total (s) |\n|---|---:|---:|---|---:|\n")
            for r in skipped:
                f.write(f"| {r['method']} | {r['n']} | {r['threads']} | {r['status']} | {r['predicted_total_s'] or '-'} |\n")

    make_figures(summary)
    print(open(RESULTS_DIR / "summary.md", encoding="utf-8").read())


def parallel_rows(summary, n):
    return sorted((r for r in summary if r["method"] == "parallel" and r["n"] == n), key=lambda r: r["threads"])


def shown_sizes(summary):
    """At most four sizes in each figure, so the lines can be told apart."""
    sizes = sorted({r["n"] for r in summary})
    wanted = [256, 1024, 2048, 8192]
    return [n for n in wanted if n in sizes] or sizes[:4]


def lines(ax, summary, field):
    ends = []
    for k, n in enumerate(shown_sizes(summary)):
        rows = parallel_rows(summary, n)
        xs, ys = [r["threads"] for r in rows], [r[field] for r in rows]
        ax.plot(xs, ys, marker="o", markersize=5, linewidth=2, color=SERIES[k], label=f"n = {n}")
        ends.append((xs[-1], ys[-1], f"n = {n}"))
    return ends


def end_labels(ax, ends, min_gap=0.055):
    """Name each line at its right end; labels that would touch are pushed apart (in axes units)."""
    to_axes = ax.transAxes.inverted()
    placed = sorted(((to_axes.transform(ax.transData.transform((x, y)))[1], x, y, text) for x, y, text in ends))
    last = -1.0
    for pos, x, y, text in placed:
        pos = max(pos, last + min_gap)
        last = pos
        ax.annotate(text, (x, y), xycoords="data", xytext=(8, pos), textcoords=("offset points", "axes fraction"),
                    va="center", fontsize=9, color=INK)


def legend_below(ax):
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, frameon=False, fontsize=9, ncol=len(labels), loc="upper center",
              bbox_to_anchor=(0.5, -0.17))


def hardware_lines(ax, top):
    for x, text in ((PHYSICAL_CORES, "12 cores"), (LOGICAL_PROCESSORS, "24 logical")):
        ax.axvline(x, color=MUTED, linewidth=1, linestyle=":")
        ax.text(x + 0.3, top, text, fontsize=9, color=MUTED, va="top")


def make_figures(summary):
    FIGURES_DIR.mkdir(exist_ok=True)
    threads = sorted({r["threads"] for r in summary})
    right = max(threads) + 4.5

    # 1) Speedup with the perfect line
    fig, ax = plt.subplots(figsize=(7, 4.8))
    ax.plot([1, PHYSICAL_CORES], [1, PHYSICAL_CORES], color=MUTED, linewidth=1.2, linestyle="--", label="perfect speedup")
    ends = lines(ax, summary, "speedup")
    ax.set_xticks(threads)
    ax.set_xlim(0, right)
    ax.set_ylim(0, max(PHYSICAL_CORES, max(r["speedup"] for r in summary)) + 1)
    style(ax, "threads p", "speedup S(p)", "Speedup: how many times faster than the sequential version")
    hardware_lines(ax, ax.get_ylim()[1])
    end_labels(ax, ends)
    legend_below(ax)
    save(fig, "speedup.png")

    # 2) Efficiency
    fig, ax = plt.subplots(figsize=(7, 4.8))
    ax.axhline(1, color=MUTED, linewidth=1.2, linestyle="--", label="perfect efficiency")
    ends = lines(ax, summary, "efficiency")
    ax.set_xticks(threads)
    ax.set_xlim(0, right)
    ax.set_ylim(0, max(1.15, max(r["efficiency"] for r in summary) + 0.1))
    style(ax, "threads p", "efficiency E(p)", "Efficiency: how much of each thread is really used")
    hardware_lines(ax, ax.get_ylim()[1])
    end_labels(ax, ends)
    legend_below(ax)
    save(fig, "efficiency.png")

    # 3) Time against threads
    fig, ax = plt.subplots(figsize=(7, 4.8))
    ends = lines(ax, summary, "median_s")
    ax.set_yscale("log")
    ax.set_xticks(threads)
    ax.set_xlim(0, right)
    style(ax, "threads p", "median time (s), log scale", "Time of the parallel method")
    hardware_lines(ax, ax.get_ylim()[1])
    end_labels(ax, ends)
    legend_below(ax)
    save(fig, "time.png")

    # 4) One thread: the cost of the threads themselves
    sizes = sorted({r["n"] for r in summary})
    seq = {r["n"]: r["median_s"] for r in summary if r["method"] == "sequential"}
    one = {r["n"]: r["median_s"] for r in summary if r["method"] == "parallel" and r["threads"] == 1}
    extra = [100 * (one[n] / seq[n] - 1) for n in sizes]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    bars = ax.bar([str(n) for n in sizes], extra, color=SERIES[0], width=0.55)
    for b, v in zip(bars, extra):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:+.1f}%", ha="center", va="bottom" if v >= 0 else "top",
                fontsize=10, color=INK)
    ax.axhline(0, color=MUTED, linewidth=1)
    ax.margins(y=0.2)
    style(ax, "matrix size n", "extra time (%)", "Parallel method with 1 thread, compared with the sequential version")
    ax.grid(False, axis="x")
    save(fig, "overhead_one_thread.png")

    # 5) Memory against threads
    fig, ax = plt.subplots(figsize=(7, 4.8))
    ends = lines(ax, summary, "peak_memory_mib")
    ax.set_yscale("log")
    ax.set_xticks(threads)
    ax.set_xlim(0, right)
    style(ax, "threads p", "peak memory (MiB), log scale", "Peak memory of the Java process")
    end_labels(ax, ends)
    legend_below(ax)
    save(fig, "memory.png")


if __name__ == "__main__":
    main()
