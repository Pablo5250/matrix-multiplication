import java.util.Random;

/**
 * Dense matrix multiplication: the basic version from Assignment 1 and two optimised versions.
 *
 * The three methods do the same n^3 multiply-adds, and each c[i][j] adds its terms in the same
 * order (k = 0, 1, ..., n-1), so they give exactly the same result. Only the order in which
 * the memory is read changes.
 */
public final class DenseMultiply {

    /** Tile size for the blocked version: 64 x 64 doubles = 32 KB, the size of the L1 cache. */
    public static final int BLOCK = 64;

    private DenseMultiply() {
    }

    /** Baseline, the same code as Assignment 1: loop order i-j-k. The inner loop reads B by columns. */
    public static double[][] ijk(double[][] a, double[][] b) {
        int n = a.length;
        double[][] c = new double[n][n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                for (int k = 0; k < n; k++) {
                    c[i][j] += a[i][k] * b[k][j];
                }
            }
        }
        return c;
    }

    /**
     * Optimisation 1, loop reordering i-k-j: the inner loop now walks along one row of B and
     * one row of C, so the memory is read in order instead of jumping between rows.
     */
    public static double[][] ikj(double[][] a, double[][] b) {
        int n = a.length;
        double[][] c = new double[n][n];
        for (int i = 0; i < n; i++) {
            double[] ci = c[i];
            double[] ai = a[i];
            for (int k = 0; k < n; k++) {
                double aik = ai[k];
                double[] bk = b[k];
                for (int j = 0; j < n; j++) {
                    ci[j] += aik * bk[j];
                }
            }
        }
        return c;
    }

    /**
     * Optimisation 2, blocking (tiling): the same i-k-j work, but done in small tiles of
     * size x size, so the pieces of A, B and C that are in use stay in the cache.
     */
    public static double[][] blocked(double[][] a, double[][] b, int size) {
        int n = a.length;
        double[][] c = new double[n][n];
        for (int ii = 0; ii < n; ii += size) {
            int iMax = Math.min(ii + size, n);
            for (int kk = 0; kk < n; kk += size) {
                int kMax = Math.min(kk + size, n);
                for (int jj = 0; jj < n; jj += size) {
                    int jMax = Math.min(jj + size, n);
                    for (int i = ii; i < iMax; i++) {
                        double[] ci = c[i];
                        double[] ai = a[i];
                        for (int k = kk; k < kMax; k++) {
                            double aik = ai[k];
                            double[] bk = b[k];
                            for (int j = jj; j < jMax; j++) {
                                ci[j] += aik * bk[j];
                            }
                        }
                    }
                }
            }
        }
        return c;
    }

    /** Runs one method by name: "ijk", "ikj", "blocked" (tile 64) or "blockedNN" (tile NN, e.g. blocked128). */
    public static double[][] multiply(String method, double[][] a, double[][] b) {
        switch (method) {
            case "ijk":
                return ijk(a, b);
            case "ikj":
                return ikj(a, b);
            case "blocked":
                return blocked(a, b, BLOCK);
            default:
                if (method.startsWith("blocked")) {
                    return blocked(a, b, Integer.parseInt(method.substring("blocked".length())));
                }
                throw new IllegalArgumentException("unknown dense method: " + method);
        }
    }

    /** n x n matrix of random numbers in [0, 1) with a fixed seed. */
    public static double[][] random(int n, long seed) {
        Random rnd = new Random(seed);
        double[][] m = new double[n][n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                m[i][j] = rnd.nextDouble();
            }
        }
        return m;
    }

    /** Sum of all elements, row by row (used to check and to consume the result). */
    public static double checksum(double[][] c) {
        double s = 0.0;
        for (double[] row : c) {
            for (double x : row) {
                s += x;
            }
        }
        return s;
    }

    public static long countNonZeros(double[][] c) {
        long count = 0;
        for (double[] row : c) {
            for (double x : row) {
                if (x != 0.0) {
                    count++;
                }
            }
        }
        return count;
    }
}
