"""Turn the raw measurements into tables and figures.

Inputs : results/raw/times.csv, results/raw/runs.csv (written by run_benchmarks.py)
Outputs: results/summary.csv, results/summary.md, figures/*.png
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

from common import FIGURES_DIR, RAW_DIR, RESULTS_DIR  # noqa: E402

COLORS = {"ijk": "#52514e", "ikj": "#2a78d6", "blocked": "#eb6834", "csr": "#1baf7a"}
NAMES = {"ijk": "baseline i-j-k", "ikj": "loop order i-k-j", "blocked": "blocked (tiles 64)", "csr": "sparse CSR"}
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
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / name, dpi=150)
    plt.close(fig)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    times = read_csv(RAW_DIR / "times.csv")
    runs = {(r["experiment"], r["method"], int(r["n"]), float(r["density_pct"])): r for r in read_csv(RAW_DIR / "runs.csv")}

    meas, conv, nnz, checks = defaultdict(list), defaultdict(list), {}, defaultdict(set)
    for r in times:
        key = (r["experiment"], r["method"], int(r["n"]), float(r["density_pct"]))
        if r["run_type"] == "measured":
            meas[key].append(int(r["time_ns"]) / 1e9)
            nnz[key] = (int(r["nnz_a"]), int(r["nnz_b"]), int(r["nnz_c"]))
            checks[key].add(float(r["checksum"]))
        elif r["run_type"] == "conversion":
            conv[key].append(int(r["time_ns"]) / 1e9)

    summary = []
    for key in sorted(meas, key=lambda k: (k[0], k[1], k[2], k[3])):
        exp, method, n, d = key
        s = meas[key]
        q1, q3 = quartiles(s)
        a, b, c = nnz[key]
        dense = method != "csr"
        storage = 3 * 8 * n * n if dense else 12 * (a + b + c) + 3 * 4 * (n + 1)
        peak = runs[key]["peak_memory_bytes"]
        base = meas.get(("part_a", "ijk", n, d))
        summary.append({
            "experiment": exp, "method": method, "n": n, "density_pct": d, "runs": len(s),
            "median_s": statistics.median(s), "q1_s": q1, "q3_s": q3, "iqr_s": q3 - q1, "min_s": min(s), "max_s": max(s),
            "speedup_vs_ijk": statistics.median(base) / statistics.median(s) if exp == "part_a" and base else "",
            "nnz_a": a, "nnz_b": b, "nnz_c": c, "density_c_pct": 100 * c / (n * n),
            "conversion_median_s": statistics.median(conv[key]) if conv.get(key) else "",
            "data_storage_mib": storage / 2**20,
            "peak_memory_mib": int(peak) / 2**20 if peak else math.nan,
            "same_result_in_all_runs": len(checks[key]) == 1,
        })
    RESULTS_DIR.mkdir(exist_ok=True)
    with open(RESULTS_DIR / "summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)

    # CSR and dense must give the same result on the same sparse inputs (checksum compare)
    same = []
    for r in summary:
        if r["method"] == "csr":
            other = (r["experiment"], "blocked", r["n"], r["density_pct"])
            if other in checks:
                same.append((r["experiment"], r["n"], r["density_pct"], checks[other] == checks[(r["experiment"], "csr", r["n"], r["density_pct"])]))

    with open(RESULTS_DIR / "summary.md", "w", encoding="utf-8") as f:
        f.write("| experiment | method | n | density % | runs | median (s) | IQR (s) | x faster than ijk | nnz(C) | density C % | conversion (s) | peak memory (MiB) |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for r in summary:
            sp = f"{r['speedup_vs_ijk']:.1f}" if r["speedup_vs_ijk"] != "" else "-"
            cv = f"{r['conversion_median_s']:.4f}" if r["conversion_median_s"] != "" else "-"
            f.write(f"| {r['experiment']} | {r['method']} | {r['n']} | {r['density_pct']:g} | {r['runs']} | {r['median_s']:.4g} | "
                    f"{r['iqr_s']:.2g} | {sp} | {r['nnz_c']} | {r['density_c_pct']:.3g} | {cv} | {r['peak_memory_mib']:.0f} |\n")
        f.write("\n| experiment | method | n | density % | status | predicted total (s) |\n|---|---|---:|---:|---|---:|\n")
        for r in runs.values():
            if r["status"] != "ok":
                f.write(f"| {r['experiment']} | {r['method']} | {r['n']} | {float(r['density_pct']):g} | {r['status']} | {r['predicted_total_s'] or '-'} |\n")
        f.write("\n| experiment | n | density % | CSR result = dense result |\n|---|---:|---:|:-:|\n")
        for exp, n, d, ok in same:
            f.write(f"| {exp} | {n} | {d:g} | {'yes' if ok else 'NO'} |\n")

    make_figures(summary)
    print(open(RESULTS_DIR / "summary.md", encoding="utf-8").read())


def rows_of(summary, exp, method):
    return sorted((r for r in summary if r["experiment"] == exp and r["method"] == method),
                  key=lambda r: (r["n"], r["density_pct"]))


def make_figures(summary):
    FIGURES_DIR.mkdir(exist_ok=True)

    # 1) Part A: time vs n (log-log) for the three dense methods
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sizes = sorted({r["n"] for r in summary if r["experiment"] == "part_a"})
    for m in ("ijk", "ikj", "blocked"):
        rows = rows_of(summary, "part_a", m)
        if rows:
            ax.plot([r["n"] for r in rows], [r["median_s"] for r in rows], marker="o", linewidth=2,
                    color=COLORS[m], label=NAMES[m])
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(n) for n in sizes])
    style(ax, "matrix size n (n × n)", "median time (s), log scale", "Part A: time of the three dense methods")
    ax.legend(frameon=False)
    save(fig, "a_time.png")

    # 2) Part A: how many times faster than the baseline (bars with values)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    base_sizes = [r["n"] for r in rows_of(summary, "part_a", "ijk")]
    w = 0.38
    for k, m in enumerate(("ikj", "blocked")):
        rows = [r for r in rows_of(summary, "part_a", m) if r["n"] in base_sizes]
        xs = [base_sizes.index(r["n"]) + (k - 0.5) * (w + 0.02) for r in rows]
        ys = [r["speedup_vs_ijk"] for r in rows]
        ax.bar(xs, ys, width=w, color=COLORS[m], label=NAMES[m])
        for x, y in zip(xs, ys):
            ax.text(x, y + 0.3, f"×{y:.1f}", ha="center", va="bottom", fontsize=10, color=INK)
    ax.set_xticks(range(len(base_sizes)))
    ax.set_xticklabels([f"n = {n}" for n in base_sizes])
    style(ax, "", "times faster than the baseline", "Part A: speed-up over the baseline i-j-k")
    ax.grid(False, axis="x")
    ax.legend(frameon=False)
    save(fig, "a_speedup.png")

    # 3) Block size test
    rows = sorted((r for r in summary if r["experiment"] == "block_size"), key=lambda r: int(r["method"][7:]))
    if rows:
        fig, ax = plt.subplots(figsize=(7, 4))
        labels = [r["method"][7:] for r in rows]
        bars = ax.bar(labels, [r["median_s"] for r in rows], color=COLORS["blocked"], width=0.55)
        for b, r in zip(bars, rows):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{r['median_s']:.2f} s", ha="center",
                    va="bottom", fontsize=10, color=INK)
        style(ax, "tile size (tile × tile numbers)", "median time (s)", f"Blocked method: tile size at n = {rows[0]['n']}")
        ax.grid(False, axis="x")
        save(fig, "a_tile_size.png")

    # 4) Part B: time vs density at fixed n
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for m in ("blocked", "csr"):
        rows = rows_of(summary, "part_b_density", m)
        if rows:
            ax.plot([r["density_pct"] for r in rows], [r["median_s"] for r in rows], marker="o", linewidth=2,
                    color=COLORS[m], label=NAMES[m] if m == "csr" else "dense (blocked)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    dens = [r["density_pct"] for r in rows_of(summary, "part_b_density", "csr")]
    ax.set_xticks(dens)
    ax.set_xticklabels([f"{d:g}%" for d in dens])
    n_b = rows_of(summary, "part_b_density", "csr")[0]["n"] if dens else ""
    style(ax, "density of A and B (% of numbers that are not zero), log scale", "median time (s), log scale",
          f"Part B: sparse vs dense at n = {n_b}")
    ax.legend(frameon=False)
    save(fig, "b_density.png")

    # 5) Part B: time vs n at fixed density
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for m in ("blocked", "csr"):
        rows = rows_of(summary, "part_b_size", m)
        if rows:
            ax.plot([r["n"] for r in rows], [r["median_s"] for r in rows], marker="o", linewidth=2,
                    color=COLORS[m], label=NAMES[m] if m == "csr" else "dense (blocked)")
    bsizes = sorted({r["n"] for r in summary if r["experiment"] == "part_b_size"})
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(bsizes)
    ax.set_xticklabels([str(n) for n in bsizes])
    d_b = rows_of(summary, "part_b_size", "csr")[0]["density_pct"] if bsizes else ""
    style(ax, "matrix size n (n × n)", "median time (s), log scale", f"Part B: sparse vs dense at density {d_b:g}%")
    ax.legend(frameon=False)
    save(fig, "b_size.png")

    # 6) Memory: peak memory of the process vs n at fixed density
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for m in ("blocked", "csr"):
        rows = rows_of(summary, "part_b_size", m)
        if rows:
            ax.plot([r["n"] for r in rows], [r["peak_memory_mib"] for r in rows], marker="o", linewidth=2,
                    color=COLORS[m], label=(NAMES[m] if m == "csr" else "dense (blocked)") + ", measured peak")
            ax.plot([r["n"] for r in rows], [r["data_storage_mib"] for r in rows], linestyle="--", linewidth=1.5,
                    color=COLORS[m], label=(NAMES[m] if m == "csr" else "dense") + ", only the data (A, B, C)")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(bsizes)
    ax.set_xticklabels([str(n) for n in bsizes])
    style(ax, "matrix size n (n × n)", "memory (MiB), log scale", f"Memory at density {d_b:g}%")
    ax.legend(frameon=False, fontsize=9)
    save(fig, "b_memory.png")
    print("Wrote figures/a_time.png, a_speedup.png, a_tile_size.png, b_density.png, b_size.png, b_memory.png")


if __name__ == "__main__":
    main()
