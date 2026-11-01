import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Locale;

/**
 * Measures ONE configuration in this JVM: warm-up runs (not counted), then measured runs.
 *
 * Usage: java Bench METHOD N THREADS WARMUP REPS OUT.csv
 *   METHOD = sequential (no threads, THREADS must be 1) or parallel
 *
 * The timer covers the multiplication, including creating the result matrix. The inputs are made
 * before it. The checksum is computed after it and uses the result, so the JVM cannot skip the work.
 */
public final class Bench {

    private Bench() {
    }

    private static double[][] run(String method, double[][] a, double[][] b, int threads) {
        switch (method) {
            case "sequential":
                return DenseMultiply.blocked(a, b, DenseMultiply.BLOCK);
            case "parallel":
                return ParallelMultiply.blocked(a, b, DenseMultiply.BLOCK, threads);
            default:
                throw new IllegalArgumentException("unknown method: " + method);
        }
    }

    public static void main(String[] args) throws IOException {
        if (args.length != 6) {
            System.err.println("usage: java Bench METHOD N THREADS WARMUP REPS OUT.csv");
            System.exit(2);
        }
        String method = args[0];
        int n = Integer.parseInt(args[1]);
        int threads = Integer.parseInt(args[2]);
        int warmup = Integer.parseInt(args[3]);
        int reps = Integer.parseInt(args[4]);

        double[][] a = DenseMultiply.random(n, 42L + n);      // same seeds as Assignment 2
        double[][] b = DenseMultiply.random(n, 4242L + n);

        try (PrintWriter out = new PrintWriter(new FileWriter(args[5]))) {
            out.println("method,n,threads,numeric_type,run_type,rep,time_ns,checksum");
            double[][] c = null;
            for (int r = 0; r < warmup + reps; r++) {
                c = null;                                     // drop the previous result first
                long t0 = System.nanoTime();
                c = run(method, a, b, threads);
                long t1 = System.nanoTime();
                String type = r < warmup ? "warmup" : "measured";
                int rep = r < warmup ? r : r - warmup;
                out.println(String.format(Locale.ROOT, "%s,%d,%d,double,%s,%d,%d,%s",
                        method, n, threads, type, rep, t1 - t0, DenseMultiply.checksum(c)));
                out.flush();
            }
        }
    }
}
