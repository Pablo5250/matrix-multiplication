"""Correctness tests for the Python implementation (run: python -m unittest)."""
import random
import unittest

from matmul import checksum, multiply


def identity(n):
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def zeros(n):
    return [[0.0] * n for _ in range(n)]


class TestMultiply(unittest.TestCase):
    def test_known_2x2(self):
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[5.0, 6.0], [7.0, 8.0]]
        self.assertEqual(multiply(a, b), [[19.0, 22.0], [43.0, 50.0]])

    def test_known_3x3(self):
        a = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]
        b = [[9.0, 8.0, 7.0], [6.0, 5.0, 4.0], [3.0, 2.0, 1.0]]
        expected = [[30.0, 24.0, 18.0], [84.0, 69.0, 54.0], [138.0, 114.0, 90.0]]
        self.assertEqual(multiply(a, b), expected)

    def test_identity(self):
        rnd = random.Random(1)
        a = [[rnd.random() for _ in range(7)] for _ in range(7)]
        self.assertEqual(multiply(a, identity(7)), a)
        self.assertEqual(multiply(identity(7), a), a)

    def test_zero(self):
        rnd = random.Random(2)
        a = [[rnd.random() for _ in range(5)] for _ in range(5)]
        self.assertEqual(multiply(a, zeros(5)), zeros(5))

    def test_one_by_one(self):
        self.assertEqual(multiply([[3.0]], [[4.0]]), [[12.0]])

    def test_checksum(self):
        self.assertEqual(checksum([[1.0, 2.0], [3.0, 4.0]]), 10.0)


if __name__ == "__main__":
    unittest.main()
