import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.DoubleBuffer;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Basic (naive) matrix multiplication in Java.
 * Storage: double[][] = an array of row arrays (each row is a separate object on the heap).
 */
public class MatMul {

    /** C = A x B with the classic triple loop, loop order i-j-k. O(n^3). */
    public static double[][] multiply(double[][] a, double[][] b) {
        int n = a.length;
        double[][] c = new double[n][n];          // output allocated inside the timed call
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                for (int k = 0; k < n; k++) {
                    c[i][j] += a[i][k] * b[k][j];
                }
            }
        }
        return c;
    }

    /** Sum of all elements, row by row (same order in Python, Java and C). */
    public static double checksum(double[][] c) {
        double s = 0.0;
        for (double[] row : c) {
            for (double x : row) {
                s += x;
            }
        }
        return s;
    }

    /** Read a raw little-endian float64 file into double[n][n]. */
    public static double[][] load(Path path, int n) throws IOException {
        byte[] bytes = Files.readAllBytes(path);
        if (bytes.length != 8L * n * n) {
            throw new IOException(path + ": expected " + (8L * n * n) + " bytes, got " + bytes.length);
        }
        DoubleBuffer buf = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).asDoubleBuffer();
        double[][] m = new double[n][n];
        for (int i = 0; i < n; i++) {
            buf.get(m[i]);
        }
        return m;
    }

    public static void save(Path path, double[][] c) throws IOException {
        int n = c.length;
        ByteBuffer buf = ByteBuffer.allocate(8 * n * n).order(ByteOrder.LITTLE_ENDIAN);
        for (double[] row : c) {
            for (double x : row) {
                buf.putDouble(x);
            }
        }
        Files.write(path, buf.array());
    }
}
