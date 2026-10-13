"""Extra experiment (separate from the main comparison): power-of-two sizes.

Question: is C slower than Java at n = 256, 512, 1024 because these sizes are
powers of two? In C the rows of B are exactly 8n bytes apart (a power of two),
so the column b[0][j], b[1][j], ... falls into the same few cache sets. In Java
every row is a separate object with a header, so the distance is not a power of two.

We run the same C and Java programs at n-1, n and n+1 and compare the
time per inner iteration (median time / n^3). Same protocol as the main study.
Output: results/extra_power_of_two.csv and figures/extra_power_of_two.png

Usage: python scripts/extra_power_of_two.py
"""
import csv
import statistics
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from common import DATA_DIR, FIGURES_DIR, RESULTS_DIR, command_for, input_paths, load_config  # noqa: E402

CENTERS = [256, 512, 1024]
LANGS = ["c", "java"]


def main():
    cfg = load_config()
    reps = cfg["measured_runs"]
    tmp = Path(tempfile.mkdtemp())
    rows = []
    for center in CENTERS:
        for n in (center - 1, center, center + 1):
            pa, pb = input_paths(n)
            if not pa.exists():                      # same generator and seed rule as the main study
                rng = np.random.default_rng(cfg["seed"] + n)
                rng.uniform(*cfg["value_range"], size=(n, n)).astype("<f8").tofile(pa)
                rng.uniform(*cfg["value_range"], size=(n, n)).astype("<f8").tofile(pb)
            for lang in LANGS:
                out = tmp / f"{lang}_{n}.csv"
                cmd = command_for(lang, cfg) + [str(n), str(DATA_DIR), str(cfg["warmup_runs"][lang]), str(reps), str(out)]
                subprocess.run(cmd, check=True)
                with open(out, encoding="utf-8") as f:
                    times = [int(r["time_ns"]) / 1e9 for r in csv.DictReader(f) if r["run_type"] == "measured"]
                med = statistics.median(times)
                rows.append({"language": lang, "n": n, "measured_runs": len(times), "median_s": med,
                             "ns_per_inner_iteration": med / n**3 * 1e9,
                             "all_times_s": " ".join(f"{t:.6f}" for t in times)})
                print(f"{lang:5s} n={n:5d}  median {med:.4f} s  {med / n**3 * 1e9:.2f} ns/iter")

    with open(RESULTS_DIR / "extra_power_of_two.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # Grouped bars: for each centre size, n-1 / n / n+1 for C and Java
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    labels, ticks, x = [], [], 0.0
    colors = {"c": "#2a78d6", "java": "#eb6834"}
    for center in CENTERS:
        for lang in LANGS:
            for d in (-1, 0, 1):
                r = next(r for r in rows if r["language"] == lang and r["n"] == center + d)
                ax.bar(x, r["ns_per_inner_iteration"], color=colors[lang], alpha=1.0 if d == 0 else 0.45,
                       edgecolor="#333333" if d == 0 else "none")
                labels.append(str(center + d))
                ticks.append(x)
                x += 1
            x += 0.5                         # gap between languages
        x += 0.5                             # bigger gap between size groups
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, rotation=90, fontsize=8)
    ax.set_ylabel("ns per inner iteration (median time / n³)")
    ax.set_title("Power-of-two sizes (dark bars) vs neighbours n-1, n+1", loc="left", fontsize=12)
    ax.bar(0, 0, color=colors["c"], label="C")
    ax.bar(0, 0, color=colors["java"], label="Java")
    ax.legend(frameon=False)
    ax.grid(True, axis="y", color="#dddddd", linewidth=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "extra_power_of_two.png")
    print("Wrote results/extra_power_of_two.csv and figures/extra_power_of_two.png")


if __name__ == "__main__":
    main()
