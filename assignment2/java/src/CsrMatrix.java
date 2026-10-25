import java.util.Arrays;
import java.util.Random;

/**
 * Sparse n x n matrix in CSR format (Compressed Sparse Row). Only the nonzero numbers are saved:
 *   values[p]  = the p-th nonzero number, row after row
 *   colIdx[p]  = its column
 *   rowPtr[i]  = where row i starts in values (row i is values[rowPtr[i] .. rowPtr[i+1]-1])
 * Inside each row the columns are in increasing order. All the code is my own (no library).
 */
public final class CsrMatrix {
    public final int n;
    public final int[] rowPtr;
    public final int[] colIdx;
    public final double[] values;

    public CsrMatrix(int n, int[] rowPtr, int[] colIdx, double[] values) {
        this.n = n;
        this.rowPtr = rowPtr;
        this.colIdx = colIdx;
        this.values = values;
    }

    public int nnz() {
        return rowPtr[n];
    }

    /** Bytes of the three arrays: 8 per value + 4 per column index + 4 per row pointer. */
    public long storageBytes() {
        return 12L * nnz() + 4L * (n + 1);
    }

    /**
     * Random n x n matrix: every position is nonzero with probability `density` (0..1), independently,
     * and the nonzero values are random numbers in (0, 1]. Instead of throwing one random number
     * per position, we jump directly to the next nonzero position (geometric gap), so building a
     * very large and very sparse matrix is fast. Same seed -> same matrix.
     */
    public static CsrMatrix random(int n, double density, long seed) {
        Random rnd = new Random(seed);
        long total = (long) n * n;
        Builder out = new Builder(n, (int) Math.min(Integer.MAX_VALUE - 8, total * density * 1.1 + 16));
        double logQ = density < 1.0 ? Math.log(1.0 - density) : 0.0;
        long pos = -1;
        while (true) {
            if (density >= 1.0) {
                pos++;
            } else {
                double u = 1.0 - rnd.nextDouble();                  // in (0, 1]
                pos += 1 + (long) Math.floor(Math.log(u) / logQ);
            }
            if (pos >= total) {
                break;
            }
            out.add((int) (pos / n), (int) (pos % n), 1.0 - rnd.nextDouble());
        }
        return out.build();
    }

    /** Dense -> CSR (keeps every number that is not 0). */
    public static CsrMatrix fromDense(double[][] d) {
        int n = d.length;
        Builder out = new Builder(n, 16);
        for (int i = 0; i < n; i++) {
            double[] row = d[i];
            for (int j = 0; j < n; j++) {
                if (row[j] != 0.0) {
                    out.add(i, j, row[j]);
                }
            }
        }
        return out.build();
    }

    /** CSR -> dense. */
    public double[][] toDense() {
        double[][] d = new double[n][n];
        for (int i = 0; i < n; i++) {
            for (int p = rowPtr[i]; p < rowPtr[i + 1]; p++) {
                d[i][colIdx[p]] = values[p];
            }
        }
        return d;
    }

    /**
     * C = A x B, both in CSR, result in CSR (row-by-row method of Gustavson).
     * For each row i of A: for each nonzero a[i][k], add a[i][k] * (row k of B) into a work row.
     * Only the nonzero numbers are touched, so the work depends on the nonzeros, not on n^3.
     * The terms of each c[i][j] are added with k in increasing order, like the dense methods.
     */
    public static CsrMatrix multiply(CsrMatrix a, CsrMatrix b) {
        int n = a.n;
        double[] acc = new double[n];        // work row: acc[j] is c[i][j] while building row i
        int[] seenInRow = new int[n];        // seenInRow[j] == i + 1  ->  column j already has a value in row i
        int[] touched = new int[n];          // columns that got a value in row i
        Builder out = new Builder(n, Math.max(16, a.nnz() + b.nnz()));
        for (int i = 0; i < n; i++) {
            int count = 0;
            for (int p = a.rowPtr[i]; p < a.rowPtr[i + 1]; p++) {
                int k = a.colIdx[p];
                double aik = a.values[p];
                for (int q = b.rowPtr[k]; q < b.rowPtr[k + 1]; q++) {
                    int j = b.colIdx[q];
                    if (seenInRow[j] != i + 1) {
                        seenInRow[j] = i + 1;
                        touched[count++] = j;
                        acc[j] = aik * b.values[q];
                    } else {
                        acc[j] += aik * b.values[q];
                    }
                }
            }
            Arrays.sort(touched, 0, count);  // CSR keeps the columns of a row in order
            for (int t = 0; t < count; t++) {
                out.add(i, touched[t], acc[touched[t]]);
            }
        }
        return out.build();
    }

    /** Sum of all values, row by row (same as the dense checksum, because zeros add nothing). */
    public double checksum() {
        double s = 0.0;
        for (int p = 0; p < nnz(); p++) {
            s += values[p];
        }
        return s;
    }

    /** Collects (row, column, value) in row order and makes the CSR arrays; grows like an ArrayList. */
    static final class Builder {
        private final int n;
        private final int[] rowPtr;
        private int[] cols;
        private double[] vals;
        private int size;
        private int lastRow;

        Builder(int n, int capacity) {
            this.n = n;
            this.rowPtr = new int[n + 1];
            this.cols = new int[Math.max(capacity, 1)];
            this.vals = new double[Math.max(capacity, 1)];
        }

        void add(int row, int col, double value) {
            while (lastRow < row) {
                rowPtr[++lastRow] = size;
            }
            if (size == cols.length) {
                int bigger = (int) Math.min(Integer.MAX_VALUE - 8, 2L * cols.length);
                cols = Arrays.copyOf(cols, bigger);
                vals = Arrays.copyOf(vals, bigger);
            }
            cols[size] = col;
            vals[size] = value;
            size++;
        }

        CsrMatrix build() {
            while (lastRow < n) {
                rowPtr[++lastRow] = size;
            }
            return new CsrMatrix(n, rowPtr, Arrays.copyOf(cols, size), Arrays.copyOf(vals, size));
        }
    }
}
