"""Cross-check the three implementations against a trusted reference (NumPy).

For each validation size, every program multiplies the shared A and B once and
writes its full result C. We compare C with numpy's A @ B using
np.allclose(rtol, atol) from config.json, and also check whether the three
languages give bit-identical results (they use the same summation order).
NumPy is only the reference here; it is not one of the compared implementations.
"""
import csv
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from common import DATA_DIR, RESULTS_DIR, command_for, input_paths, load_config, read_matrix_numpy


def main():
    cfg = load_config()
    rtol, atol = cfg["rtol"], cfg["atol"]
    rows, ok_all = [], True
    tmp = Path(tempfile.mkdtemp())

    for n in cfg["validation_sizes"]:
        pa, pb = input_paths(n)
        reference = read_matrix_numpy(pa, n) @ read_matrix_numpy(pb, n)
        results = {}
        for lang in cfg["languages"]:
            dump = tmp / f"C_{lang}_{n}.bin"
            cmd = command_for(lang, cfg) + [str(n), str(DATA_DIR), "0", "1", str(tmp / "t.csv"), str(dump)]
            subprocess.run(cmd, check=True)
            c = read_matrix_numpy(dump, n)
            results[lang] = c
            abs_err = np.abs(c - reference)
            rel_err = abs_err / np.maximum(np.abs(reference), np.finfo(float).tiny)
            ok = bool(np.allclose(c, reference, rtol=rtol, atol=atol))
            ok_all &= ok
            rows.append({"n": n, "language": lang, "max_abs_error": f"{abs_err.max():.3e}",
                         "max_rel_error": f"{rel_err.max():.3e}", "rtol": rtol, "atol": atol,
                         "passed": ok})
            print(f"n={n:4d} {lang:6s} max|err|={abs_err.max():.2e} max rel={rel_err.max():.2e} -> {'OK' if ok else 'FAIL'}")
        langs = list(results)
        identical = all(np.array_equal(results[langs[0]], results[x]) for x in langs[1:])
        print(f"n={n:4d} languages bit-identical to each other: {identical}")
        for r in rows:
            if r["n"] == n:
                r["bit_identical_across_languages"] = identical

    RESULTS_DIR.mkdir(exist_ok=True)
    with open(RESULTS_DIR / "validation.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("Wrote results/validation.csv")
    if not ok_all:
        raise SystemExit("VALIDATION FAILED")


if __name__ == "__main__":
    main()
