/* Basic (naive) matrix multiplication in C. */
#ifndef _WIN32
#define _POSIX_C_SOURCE 199309L   /* for clock_gettime */
#endif

#include "matmul.h"

#include <stdio.h>
#include <stdlib.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <time.h>
#endif

/* C = A x B with the classic triple loop, loop order i-j-k. O(n^3). */
double *multiply(const double *a, const double *b, int n) {
    double *c = calloc((size_t)n * n, sizeof(double));   /* output allocated inside the timed call */
    if (c == NULL) return NULL;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            for (int k = 0; k < n; k++) {
                c[(size_t)i * n + j] += a[(size_t)i * n + k] * b[(size_t)k * n + j];
            }
        }
    }
    return c;
}

/* Sum of all elements, row by row (same order in Python, Java and C). */
double checksum(const double *c, int n) {
    double s = 0.0;
    for (size_t idx = 0; idx < (size_t)n * n; idx++) s += c[idx];
    return s;
}

/* Read a raw little-endian float64 file (x86/ARM machines are little-endian). */
double *load_matrix(const char *path, int n) {
    FILE *f = fopen(path, "rb");
    if (f == NULL) return NULL;
    double *m = malloc((size_t)n * n * sizeof(double));
    size_t got = m ? fread(m, sizeof(double), (size_t)n * n, f) : 0;
    fclose(f);
    if (got != (size_t)n * n) { free(m); return NULL; }
    return m;
}

int save_matrix(const char *path, const double *c, int n) {
    FILE *f = fopen(path, "wb");
    if (f == NULL) return 0;
    size_t put = fwrite(c, sizeof(double), (size_t)n * n, f);
    fclose(f);
    return put == (size_t)n * n;
}

long long now_ns(void) {
#ifdef _WIN32
    LARGE_INTEGER freq, count;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&count);
    return (long long)(count.QuadPart / freq.QuadPart) * 1000000000LL
         + (long long)(count.QuadPart % freq.QuadPart) * 1000000000LL / freq.QuadPart;
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
#endif
}
