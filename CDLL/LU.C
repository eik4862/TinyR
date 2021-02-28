#include<stdlib.h>
#include<stdio.h>

void LUInt(long ** __restrict__ A, int * __restrict__ perm, int n) {
    int p = 0;
    int tmp;
    long *tmp2;

    for (int i = 0; i < n - 1; i++) {
         p = i;

         for (int j = i + 1; j < n; j++) {
            if (A[p][i] < A[j][i]) {
                p = j;
            }
         }

         tmp = perm[p];
         perm[p] = perm[i];
         perm[i] = tmp;

         tmp2 = A[p];
         A[p] = A[i];
         A[i] = tmp2;

         for (int j = i + 1; j < n; j++) {
            A[j][i] /= A[i][i];

            for (int k = i + 1; k < n; k++) {
                A[j][k] -= A[j][i] * A[i][k];
            }
         }
    }

    return;
}

void LUFloat(double ** __restrict__ A, int * __restrict__ perm, int n) {
    int p = 0;
    int tmp;
    double *tmp2;

    for (int i = 0; i < n - 1; i++) {
         p = i;

         for (int j = i + 1; j < n; j++) {
            if (A[p][i] < A[j][i]) {
                p = j;
            }
         }

         tmp = perm[p];
         perm[p] = perm[i];
         perm[i] = tmp;

         tmp2 = A[p];
         A[p] = A[i];
         A[i] = tmp2;

         for (int j = i + 1; j < n; j++) {
            A[j][i] /= A[i][i];

            for (int k = i + 1; k < n; k++) {
                A[j][k] -= A[j][i] * A[i][k];
            }
         }
    }

    return;
}

void LU(void ** __restrict__ A, int * __restrict__ perm, int n, _Bool intFlag) {
    if (intFlag) {
        LUInt((long **)A, perm, n);
    } else {
        LUFloat((double **)A, perm, n);
    }

    return;
}