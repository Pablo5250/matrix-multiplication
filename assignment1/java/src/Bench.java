import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Path;

/**
 * Benchmark program for the Java implementation.
 * Usage: java Bench N INPUT_DIR WARMUP REPS OUT_CSV [DUMP_FILE]
 *
 * The timer only covers MatMul.multiply() (the kernel, including allocating C).
 * Warm-up runs let the JIT compiler optimise multiply() before we measure;
 * they are written to the CSV but marked "warmup" and excluded from the analysis.
 */
public class Bench {
    public static void main(String[] args) throws IOException {
        int n = Integer.parseInt(args[0]);
        Path inputDir = Path.of(args[1]);
        int warmup = Integer.parseInt(args[2]);
        int reps = Integer.parseInt(args[3]);
        String outCsv = args[4];
        String dump = args.length > 5 ? args[5] : null;

        double[][] a = MatMul.load(inputDir.resolve("A_n" + n + ".bin"), n);
        double[][] b = MatMul.load(inputDir.resolve("B_n" + n + ".bin"), n);

        double[][] c = null;
        try (PrintWriter out = new PrintWriter(outCsv, "UTF-8")) {
            out.println("language,n,run_type,rep,time_ns,checksum");
            for (int r = 0; r < warmup + reps; r++) {
                c = null;                          // drop the previous result (like free(c) in C)
                long t0 = System.nanoTime();       // monotonic, nanoseconds
                c = MatMul.multiply(a, b);
                long t1 = System.nanoTime();
                double s = MatMul.checksum(c);     // consume the result
                String kind = r < warmup ? "warmup" : "measured";
                int rep = r < warmup ? r : r - warmup;
                out.println("java," + n + "," + kind + "," + rep + "," + (t1 - t0) + "," + s);
                out.flush();
            }
        }
        if (dump != null) {
            MatMul.save(Path.of(dump), c);
        }
    }
}
