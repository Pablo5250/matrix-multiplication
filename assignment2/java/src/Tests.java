import java.util.Arrays;

/** Correctness tests for all the methods (no external library needed). Run: java Tests */
public final class Tests {
    private static int failures = 0;

    private Tests() {
    }

    private static void check(String name, boolean ok) {
        System.out.println((ok ? "PASS  " : "FAIL  ") + name);
        if (!ok) {
            failures++;
        }
    }

    private static boolean same(double[][] x, double[][] y) {
        return Arrays.deepEquals(x, y);
    }

    private static double[][] identity(int n) {
        double[][] m = new double[n][n];
        for (int i = 0; i < n; i++) {
            m[i][i] = 1.0;
        }
        return m;
    }

    public static void main(String[] args) {
        String[] methods = {"ijk", "ikj", "blocked"};

        // 1) Known small results, done by hand
        double[][] a2 = {{1, 2}, {3, 4}};
        double[][] b2 = {{5, 6}, {7, 8}};
        double[][] e2 = {{19, 22}, {43, 50}};
        double[][] a3 = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};
        double[][] b3 = {{9, 8, 7}, {6, 5, 4}, {3, 2, 1}};
        double[][] e3 = {{30, 24, 18}, {84, 69, 54}, {138, 114, 90}};
        for (String m : methods) {
            check(m + ": known 2x2", same(DenseMultiply.multiply(m, a2, b2), e2));
            check(m + ": known 3x3", same(DenseMultiply.multiply(m, a3, b3), e3));
            check(m + ": 1x1", same(DenseMultiply.multiply(m, new double[][]{{3}}, new double[][]{{4}}),
                    new double[][]{{12}}));
        }
        check("csr: known 2x2", same(CsrMatrix.multiply(CsrMatrix.fromDense(a2), CsrMatrix.fromDense(b2)).toDense(), e2));
        check("csr: known 3x3", same(CsrMatrix.multiply(CsrMatrix.fromDense(a3), CsrMatrix.fromDense(b3)).toDense(), e3));

        // 2) Identity and zero, with sizes that are NOT a multiple of the 64 block (70, 130)
        for (int n : new int[]{7, 70, 130}) {
            double[][] r = DenseMultiply.random(n, n);
            double[][] zero = new double[n][n];
            for (String m : methods) {
                check(m + ": A x I = A (n=" + n + ")", same(DenseMultiply.multiply(m, r, identity(n)), r));
                check(m + ": I x A = A (n=" + n + ")", same(DenseMultiply.multiply(m, identity(n), r), r));
                check(m + ": A x 0 = 0 (n=" + n + ")", same(DenseMultiply.multiply(m, r, zero), zero));
            }
            CsrMatrix cr = CsrMatrix.fromDense(r);
            check("csr: A x I = A (n=" + n + ")", same(CsrMatrix.multiply(cr, CsrMatrix.fromDense(identity(n))).toDense(), r));
            check("csr: A x 0 = 0 (n=" + n + ")", CsrMatrix.multiply(cr, CsrMatrix.fromDense(zero)).nnz() == 0);
        }

        // 3) The optimised methods give exactly the same numbers as the baseline (same order of additions)
        for (int n : new int[]{100, 257}) {
            double[][] a = DenseMultiply.random(n, 1000 + n);
            double[][] b = DenseMultiply.random(n, 2000 + n);
            double[][] base = DenseMultiply.ijk(a, b);
            check("ikj = ijk exactly (n=" + n + ")", same(DenseMultiply.ikj(a, b), base));
            check("blocked = ijk exactly (n=" + n + ")", same(DenseMultiply.blocked(a, b, DenseMultiply.BLOCK), base));
            check("blocked, tile 16 = ijk exactly (n=" + n + ")", same(DenseMultiply.blocked(a, b, 16), base));
        }

        // 4) Sparse: CSR x CSR = dense baseline on the same matrices, for several densities
        for (double d : new double[]{0.001, 0.01, 0.1, 0.5, 1.0}) {
            int n = 200;
            CsrMatrix a = CsrMatrix.random(n, d, 11);
            CsrMatrix b = CsrMatrix.random(n, d, 12);
            double[][] base = DenseMultiply.ijk(a.toDense(), b.toDense());
            CsrMatrix c = CsrMatrix.multiply(a, b);
            check("csr x csr = ijk exactly (density " + d * 100 + "%)", same(c.toDense(), base));
            check("csr nnz(C) = nonzeros of dense C (density " + d * 100 + "%)", c.nnz() == DenseMultiply.countNonZeros(base));
        }

        // 5) CSR format: dense -> CSR -> dense gives back the same matrix; the density is close to the target
        CsrMatrix s = CsrMatrix.random(300, 0.05, 99);
        check("csr: toDense -> fromDense round trip", same(CsrMatrix.fromDense(s.toDense()).toDense(), s.toDense()));
        double realDensity = s.nnz() / (300.0 * 300.0);
        check("csr: random density close to 5% (got " + String.format(java.util.Locale.ROOT, "%.3f", realDensity * 100) + "%)",
                Math.abs(realDensity - 0.05) < 0.005);
        check("csr: same seed -> same matrix", same(CsrMatrix.random(300, 0.05, 99).toDense(), s.toDense()));

        if (failures > 0) {
            System.out.println(failures + " test(s) failed");
            System.exit(1);
        }
        System.out.println("All tests passed");
    }
}
