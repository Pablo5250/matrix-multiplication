import java.util.Arrays;

/** Correctness tests: known results, identity, zero, sizes that are not a multiple of 64, thread safety. */
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
        return Arrays.deepEquals(x, y);                      // exact comparison, no tolerance
    }

    private static double[][] identity(int n) {
        double[][] m = new double[n][n];
        for (int i = 0; i < n; i++) {
            m[i][i] = 1.0;
        }
        return m;
    }

    private static double[][] copy(double[][] m) {
        double[][] out = new double[m.length][];
        for (int i = 0; i < m.length; i++) {
            out[i] = m[i].clone();
        }
        return out;
    }

    public static void main(String[] args) {
        int block = DenseMultiply.BLOCK;
        int[] threadCounts = {1, 2, 3, 4, 8, 12, 16, 24, 32};

        // 1) Known small results, done by hand
        double[][] a2 = {{1, 2}, {3, 4}}, b2 = {{5, 6}, {7, 8}}, e2 = {{19, 22}, {43, 50}};
        double[][] a3 = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}}, b3 = {{9, 8, 7}, {6, 5, 4}, {3, 2, 1}};
        double[][] e3 = {{30, 24, 18}, {84, 69, 54}, {138, 114, 90}};
        check("sequential: known 2x2", same(DenseMultiply.blocked(a2, b2, block), e2));
        check("sequential: known 3x3", same(DenseMultiply.blocked(a3, b3, block), e3));
        for (int p : threadCounts) {                         // also more threads than rows
            check("parallel p=" + p + ": known 2x2", same(ParallelMultiply.blocked(a2, b2, block, p), e2));
            check("parallel p=" + p + ": known 3x3", same(ParallelMultiply.blocked(a3, b3, block, p), e3));
            check("parallel p=" + p + ": 1x1", same(ParallelMultiply.blocked(
                    new double[][]{{3}}, new double[][]{{4}}, block, p), new double[][]{{12}}));
        }

        // 2) Identity and zero, with sizes that are NOT a multiple of the tile (70, 130)
        for (int n : new int[]{70, 130}) {
            double[][] r = DenseMultiply.random(n, n);
            double[][] zero = new double[n][n];
            check("sequential: A x I = A (n=" + n + ")", same(DenseMultiply.blocked(r, identity(n), block), r));
            check("sequential: A x 0 = 0 (n=" + n + ")", same(DenseMultiply.blocked(r, zero, block), zero));
            for (int p : new int[]{1, 4, 24}) {
                check("parallel p=" + p + ": A x I = A (n=" + n + ")", same(ParallelMultiply.blocked(r, identity(n), block, p), r));
                check("parallel p=" + p + ": I x A = A (n=" + n + ")", same(ParallelMultiply.blocked(identity(n), r, block, p), r));
                check("parallel p=" + p + ": A x 0 = 0 (n=" + n + ")", same(ParallelMultiply.blocked(r, zero, block, p), zero));
            }
        }

        // 3) The sequential baseline and every thread count give exactly the basic i-j-k result
        for (int n : new int[]{100, 257, 512}) {
            double[][] a = DenseMultiply.random(n, 1000L + n);
            double[][] b = DenseMultiply.random(n, 2000L + n);
            double[][] base = DenseMultiply.ijk(a, b);
            check("sequential = ijk exactly (n=" + n + ")", same(DenseMultiply.blocked(a, b, block), base));
            for (int p : threadCounts) {
                check("parallel p=" + p + " = ijk exactly (n=" + n + ")", same(ParallelMultiply.blocked(a, b, block, p), base));
            }
        }

        // 4) Thread safety: many repeats, because a race condition does not fail every time
        int n = 300;
        double[][] a = DenseMultiply.random(n, 11);
        double[][] b = DenseMultiply.random(n, 22);
        double[][] aCopy = copy(a), bCopy = copy(b);
        double[][] base = DenseMultiply.blocked(a, b, block);
        for (int p : new int[]{2, 12, 24, 32}) {
            boolean allSame = true;
            for (int r = 0; r < 200; r++) {
                allSame &= same(ParallelMultiply.blocked(a, b, block, p), base);
            }
            check("parallel p=" + p + ": same result in 200 repeats", allSame);
        }
        check("the inputs A and B do not change", same(a, aCopy) && same(b, bCopy));

        // 5) The chunks cover every row exactly once, with no gaps and no overlap
        boolean cover = true;
        for (int size : new int[]{1, 7, 64, 255, 1000, 8192}) {
            for (int p : threadCounts) {
                int chunks = Math.min(size, p * ParallelMultiply.CHUNKS_PER_THREAD);
                cover &= ParallelMultiply.chunkStart(0, size, chunks) == 0;
                cover &= ParallelMultiply.chunkStart(chunks, size, chunks) == size;
                for (int id = 0; id < chunks; id++) {
                    cover &= ParallelMultiply.chunkStart(id, size, chunks) < ParallelMultiply.chunkStart(id + 1, size, chunks);
                }
            }
        }
        check("chunks cover all the rows exactly once", cover);

        System.out.println(failures == 0 ? "All tests passed" : failures + " tests FAILED");
        if (failures != 0) {
            System.exit(1);
        }
    }
}
