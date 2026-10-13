/* Correctness tests for the C implementation. */
#include "matmul.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failures = 0;

static void check(const char *name, int ok) {
    printf("%s  %s\n", ok ? "PASS" : "FAIL", name);
    if (!ok) failures++;
}

static int equal(const double *x, const double *y, int n) {
    return memcmp(x, y, (size_t)n * n * sizeof(double)) == 0;
}

int main(void) {
    double a[] = {1, 2, 3, 4}, b[] = {5, 6, 7, 8}, e[] = {19, 22, 43, 50};
    double *c = multiply(a, b, 2);
    check("known 2x2", equal(c, e, 2));
    free(c);

    double a3[] = {1, 2, 3, 4, 5, 6, 7, 8, 9}, b3[] = {9, 8, 7, 6, 5, 4, 3, 2, 1};
    double e3[] = {30, 24, 18, 84, 69, 54, 138, 114, 90};
    c = multiply(a3, b3, 3);
    check("known 3x3", equal(c, e3, 3));
    free(c);

    enum { N = 7 };
    double r[N * N], id[N * N] = {0}, z[N * N] = {0};
    srand(1);
    for (int i = 0; i < N * N; i++) r[i] = (double)rand() / RAND_MAX;
    for (int i = 0; i < N; i++) id[i * N + i] = 1.0;
    c = multiply(r, id, N); check("A x I = A", equal(c, r, N)); free(c);
    c = multiply(id, r, N); check("I x A = A", equal(c, r, N)); free(c);
    c = multiply(r, z, N);  check("A x 0 = 0", equal(c, z, N)); free(c);

    double one_a[] = {3}, one_b[] = {4};
    c = multiply(one_a, one_b, 1); check("1x1", c[0] == 12.0); free(c);
    check("checksum", checksum(a, 2) == 10.0);

    if (failures > 0) { printf("%d test(s) failed\n", failures); return 1; }
    printf("All C tests passed\n");
    return 0;
}
