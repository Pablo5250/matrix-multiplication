import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Parallel version of the blocked method, with plain Java threads.
 *
 * The rows of C are split into chunks, and each thread takes the next free chunk until none are
 * left. Safe access to shared data: A and B are only read, and each row of C belongs to one chunk,
 * so no two threads write to the same number. Thread.join makes the results visible to the caller.
 */
public final class ParallelMultiply {

    /** More chunks than threads, so a thread that runs slower simply takes fewer chunks. */
    public static final int CHUNKS_PER_THREAD = 4;

    private ParallelMultiply() {
    }

    /** First row of a chunk. The last row of chunk id is chunkStart(id + 1, ...) - 1. */
    public static int chunkStart(int id, int n, int chunks) {
        return (int) ((long) id * n / chunks);
    }

    public static double[][] blocked(double[][] a, double[][] b, int size, int threads) {
        if (threads < 1) {
            throw new IllegalArgumentException("threads must be at least 1");
        }
        int n = a.length;
        double[][] c = new double[n][n];
        int chunks = Math.min(n, threads * CHUNKS_PER_THREAD);
        AtomicInteger next = new AtomicInteger();
        AtomicReference<Throwable> failure = new AtomicReference<>();

        Runnable work = () -> {
            try {
                for (int id = next.getAndIncrement(); id < chunks; id = next.getAndIncrement()) {
                    DenseMultiply.blockedRows(a, b, c, chunkStart(id, n, chunks), chunkStart(id + 1, n, chunks), size);
                }
            } catch (Throwable t) {
                failure.compareAndSet(null, t);
            }
        };

        Thread[] workers = new Thread[threads];
        for (int t = 0; t < threads; t++) {
            workers[t] = new Thread(work, "multiply-" + t);
            workers[t].start();
        }
        try {
            for (Thread w : workers) {
                w.join();
            }
        } catch (InterruptedException e) {
            throw new IllegalStateException("interrupted while waiting for the threads", e);
        }
        if (failure.get() != null) {
            throw new IllegalStateException("a thread failed", failure.get());
        }
        return c;
    }
}
