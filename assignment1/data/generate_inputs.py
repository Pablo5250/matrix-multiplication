"""Generate the shared input matrices A and B for every matrix size.

All three languages read exactly the same files, so they multiply the same
numbers. Format: raw float64, little-endian, row-major, no header
(n*n*8 bytes per matrix). The files are not committed to git because they can
be regenerated with this script (same seed -> same bytes, checked with SHA-256).
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from common import DATA_DIR, input_paths, load_config  # noqa: E402


def generate(n, seed, low, high):
    # One independent random stream per size: seed + n (PCG64 generator).
    rng = np.random.default_rng(seed + n)
    a = rng.uniform(low, high, size=(n, n))
    b = rng.uniform(low, high, size=(n, n))
    return a, b


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    cfg = load_config()
    sizes = sorted(set(cfg["sizes"]) | set(cfg["validation_sizes"]))
    low, high = cfg["value_range"]
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generator": "numpy.random.default_rng (PCG64), uniform",
        "numpy_version": np.__version__,
        "seed_rule": f"seed = {cfg['seed']} + n",
        "value_range": [low, high],
        "dtype": "float64 little-endian, row-major, no header",
        "files": {},
    }
    for n in sizes:
        pa, pb = input_paths(n)
        if not (pa.exists() and pb.exists()):
            a, b = generate(n, cfg["seed"], low, high)
            a.astype("<f8").tofile(pa)
            b.astype("<f8").tofile(pb)
        manifest["files"][pa.name] = sha256(pa)
        manifest["files"][pb.name] = sha256(pb)
        print(f"n={n:5d}  {pa.name}, {pb.name}")

    with open(DATA_DIR.parent / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("Wrote data/manifest.json")


if __name__ == "__main__":
    main()
