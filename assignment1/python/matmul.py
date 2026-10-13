"""Basic (naive) matrix multiplication in pure Python.

Storage: a matrix is a list of rows, each row is a list of Python floats
(64-bit doubles stored as separate objects). NumPy is NOT used here.
"""
import sys
from array import array


def multiply(a, b):
    """C = A x B with the classic triple loop, loop order i-j-k. O(n^3)."""
    n = len(a)
    c = [[0.0] * n for _ in range(n)]          # output allocated inside the timed call
    for i in range(n):
        for j in range(n):
            for k in range(n):
                c[i][j] += a[i][k] * b[k][j]
    return c


def checksum(c):
    """Sum of all elements, row by row (same order in Python, Java and C)."""
    s = 0.0
    for row in c:
        for x in row:
            s += x
    return s


def load_matrix(path, n):
    """Read a raw little-endian float64 file into a list of lists."""
    values = array("d")
    with open(path, "rb") as f:
        values.frombytes(f.read())
    if sys.byteorder != "little":
        values.byteswap()
    if len(values) != n * n:
        raise ValueError(f"{path}: expected {n * n} values, got {len(values)}")
    return [values[i * n:(i + 1) * n].tolist() for i in range(n)]


def save_matrix(path, c):
    values = array("d", (x for row in c for x in row))
    if sys.byteorder != "little":
        values.byteswap()
    with open(path, "wb") as f:
        values.tofile(f)
