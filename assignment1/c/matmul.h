#ifndef MATMUL_H
#define MATMUL_H

#include <stddef.h>

/* Storage: one contiguous block of n*n doubles in row-major order.
   Element (i, j) is m[i * n + j]. */

double *multiply(const double *a, const double *b, int n);  /* returns new C, caller frees */
double checksum(const double *c, int n);
double *load_matrix(const char *path, int n);               /* returns NULL on error */
int save_matrix(const char *path, const double *c, int n);
long long now_ns(void);                                     /* monotonic clock in ns */

#endif
