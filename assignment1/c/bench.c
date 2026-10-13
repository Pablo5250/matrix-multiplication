/* Benchmark program for the C implementation.
   Usage: bench_c N INPUT_DIR WARMUP REPS OUT_CSV [DUMP_FILE]

   The timer only covers multiply() (the kernel, including allocating C).
   Same arguments and CSV columns as the Python and Java programs. */
#include "matmul.h"

#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc < 6) {
        fprintf(stderr, "usage: %s N INPUT_DIR WARMUP REPS OUT_CSV [DUMP_FILE]\n", argv[0]);
        return 2;
    }
    int n = atoi(argv[1]);
    const char *input_dir = argv[2];
    int warmup = atoi(argv[3]);
    int reps = atoi(argv[4]);
    const char *out_csv = argv[5];
    const char *dump = argc > 6 ? argv[6] : NULL;

    char path_a[4096], path_b[4096];
    snprintf(path_a, sizeof path_a, "%s/A_n%d.bin", input_dir, n);
    snprintf(path_b, sizeof path_b, "%s/B_n%d.bin", input_dir, n);
    double *a = load_matrix(path_a, n);
    double *b = load_matrix(path_b, n);
    if (a == NULL || b == NULL) { fprintf(stderr, "cannot read input matrices\n"); return 1; }

    FILE *out = fopen(out_csv, "w");
    if (out == NULL) { fprintf(stderr, "cannot write %s\n", out_csv); return 1; }
    fprintf(out, "language,n,run_type,rep,time_ns,checksum\n");

    double *c = NULL;
    for (int r = 0; r < warmup + reps; r++) {
        free(c);
        long long t0 = now_ns();
        c = multiply(a, b, n);
        long long t1 = now_ns();
        if (c == NULL) { fprintf(stderr, "out of memory\n"); return 3; }
        double s = checksum(c, n);              /* consume the result */
        const char *kind = r < warmup ? "warmup" : "measured";
        int rep = r < warmup ? r : r - warmup;
        fprintf(out, "c,%d,%s,%d,%lld,%.17g\n", n, kind, rep, t1 - t0, s);
        fflush(out);
    }
    fclose(out);

    if (dump != NULL && !save_matrix(dump, c, n)) { fprintf(stderr, "cannot write dump\n"); return 1; }
    free(a); free(b); free(c);
    return 0;
}
