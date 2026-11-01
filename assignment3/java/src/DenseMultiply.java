import java.util.Random;

/**
 * Sequential dense matrix multiplication, reused from Assignment 2.
 *
 * The only change is that the body of the blocked method is now in blockedRows, so the sequential
 * and the parallel versions run exactly the same code. Each c[i][j] adds its terms in the same
 * order (k = 0, 1, ..., n-1), so all the versions give exactly the same result.
 */
public final class DenseMultiply {

    /** Tile size: 64 x 64 doubles = 32 KB, the size of the L1 cache. */
    public static final int BLOCK = 64;

    private DenseMultiply() {
    }

    /** Basic loop order i-j-k from Assignment 1. Used only as the reference in the tests. */
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

    /** Sequential baseline: the blocked method of Assignment 2, with no threads. */
    public static double[][] blocked(double[][] a, double[][] b, int size) {
        int n = a.length;
        double[][] c = new double[n][n];
        blockedRows(a, b, c, 0, n, size);
        return c;
    }

    /** Blocked i-k-j work for the rows rowStart (included) to rowEnd (not included) of C. */
    public static void blockedRows(double[][] a, double[][] b, double[][] c, int rowStart, int rowEnd, int size) {
        int n = a.length;
        for (int ii = rowStart; ii < rowEnd; ii += size) {
            int iMax = Math.min(ii + size, rowEnd);
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
}
