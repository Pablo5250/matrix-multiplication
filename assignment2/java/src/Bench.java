import java.io.IOException;
import java.io.PrintWriter;

/**
 * Benchmark program. One run of this program = one configuration (one method, one size).
 *
 *   java Bench dense  METHOD N WARMUP REPS OUT_CSV
 *       Part A. A and B are dense random matrices (seeds 42 + n and 4242 + n).
 *       METHOD = ijk | ikj | blocked
 *
 *   java Bench sparse METHOD N DENSITY_PCT WARMUP REPS OUT_CSV
 *       Part B. A and B are random sparse matrices with DENSITY_PCT % nonzeros (seeds 7 + n and 77 + n).
 *       METHOD = csr               -> CSR x CSR
 *              | ijk | ikj | blocked -> the same matrices converted to dense (conversion not timed)
 *       For csr, the time of converting dense -> CSR is also measured separately (n <= 4096).
 *
 * The timer only covers the multiplication (including creating the result). Creating the inputs
 * is not timed. Warm-up runs let the JIT compile the code; they are written but marked "warmup".
 */
public final class Bench {

    private Bench() {
    }

    public static void main(String[] args) throws IOException {
        String part = args[0];
        String method = args[1];
        int n = Integer.parseInt(args[2]);
        int i = 3;
        double densityPct = part.equals("sparse") ? Double.parseDouble(args[i++]) : 100.0;
        int warmup = Integer.parseInt(args[i++]);
        int reps = Integer.parseInt(args[i++]);
        String outCsv = args[i];

        try (PrintWriter out = new PrintWriter(outCsv, "UTF-8")) {
            out.println("part,method,n,density_pct,run_type,rep,time_ns,checksum,nnz_a,nnz_b,nnz_c");
            String prefix = part + "," + method + "," + n + "," + densityPct + ",";

            if (part.equals("dense")) {
                double[][] a = DenseMultiply.random(n, 42L + n);
                double[][] b = DenseMultiply.random(n, 4242L + n);
                long nn = (long) n * n;
                for (int r = 0; r < warmup + reps; r++) {
                    long t0 = System.nanoTime();
                    double[][] c = DenseMultiply.multiply(method, a, b);
                    long t1 = System.nanoTime();
                    out.println(prefix + kind(r, warmup) + "," + rep(r, warmup) + "," + (t1 - t0) + ","
                            + DenseMultiply.checksum(c) + "," + nn + "," + nn + "," + DenseMultiply.countNonZeros(c));
                    out.flush();
                }
                return;
            }

            CsrMatrix a = CsrMatrix.random(n, densityPct / 100.0, 7L + n);
            CsrMatrix b = CsrMatrix.random(n, densityPct / 100.0, 77L + n);
            String nnzIn = a.nnz() + "," + b.nnz();
            if (method.equals("csr")) {
                for (int r = 0; r < warmup + reps; r++) {
                    long t0 = System.nanoTime();
                    CsrMatrix c = CsrMatrix.multiply(a, b);
                    long t1 = System.nanoTime();
                    out.println(prefix + kind(r, warmup) + "," + rep(r, warmup) + "," + (t1 - t0) + ","
                            + c.checksum() + "," + nnzIn + "," + c.nnz());
                    out.flush();
                }
                if (n <= 4096) {                       // conversion cost, measured separately
                    double[][] denseA = a.toDense();
                    for (int r = 0; r < warmup + reps; r++) {
                        long t0 = System.nanoTime();
                        CsrMatrix back = CsrMatrix.fromDense(denseA);
                        long t1 = System.nanoTime();
                        String type = r < warmup ? "conversion_warmup" : "conversion";
                        out.println(prefix + type + "," + rep(r, warmup) + "," + (t1 - t0) + ","
                                + back.checksum() + "," + nnzIn + "," + back.nnz());
                        out.flush();
                    }
                }
            } else {
                double[][] da = a.toDense();            // not timed: same logical matrices as csr
                double[][] db = b.toDense();
                for (int r = 0; r < warmup + reps; r++) {
                    long t0 = System.nanoTime();
                    double[][] c = DenseMultiply.multiply(method, da, db);
                    long t1 = System.nanoTime();
                    out.println(prefix + kind(r, warmup) + "," + rep(r, warmup) + "," + (t1 - t0) + ","
                            + DenseMultiply.checksum(c) + "," + nnzIn + "," + DenseMultiply.countNonZeros(c));
                    out.flush();
                }
            }
        }
    }

    private static String kind(int r, int warmup) {
        return r < warmup ? "warmup" : "measured";
    }

    private static int rep(int r, int warmup) {
        return r < warmup ? r : r - warmup;
    }
}
