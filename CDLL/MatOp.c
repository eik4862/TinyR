#include<stdlib.h>
#include<stdio.h>
#include<pthread.h>
#include<math.h>

#define TRUE 1
#define FALSE 0
#define MIN(a, b) ((a) > (b) ? (b) : (a))

typedef struct _Data {
    const void ** __restrict__ A;
    const void ** __restrict__ B;
    void ** __restrict__ C;
    int dim[3];
    int blkIdx[3];
    int blkSz;
} Data;

pthread_mutex_t mutex;

void *__GEMMI(void *arg);
void *__GEMMF(void *arg);
void GEMM(const void ** __restrict__ A, const void ** __restrict__ B, void ** __restrict__ C, int l, int m, int n,
          int blkSz, _Bool int_mat);

void __LUPP(double ** __restrict__ A, int * __restrict__ p, int * __restrict__ flag, int m, int n, double tol);
void __LUCP(double ** __restrict__ A, int * __restrict__ p, int * __restrict__ q, int * __restrict__ flag,
            int m, int n, double tol);
void LU(double ** __restrict__ A, int * __restrict__ p, int * __restrict__ q, int * __restrict__ flag,
        int m, int n, _Bool cp, double tol);

void CHOL(double ** __restrict__ A, int * __restrict__ flag, int n, double tol);

void QR(double ** __restrict__ A, double * __restrict__ v, int * __restrict__ flag, int m, int n, double tol);

void *__GEMMI(void *arg) {
    Data * __restrict__ data = (Data *)arg;
    const long ** __restrict__ A = (const long **)data->A;
    const long ** __restrict__ B = (const long **)data->B;
    long ** __restrict__ C = (long **)data->C;
    int * __restrict__ dim = data->dim;
    int * __restrict__ blkIdx = data->blkIdx;
    int blkSz = data->blkSz;
    long ** __restrict__ tmp = (long **)malloc(dim[0] * sizeof(long *));

    for (int i = 0; i < dim[0]; i++) {
        tmp[i] = (long *)malloc(dim[2] * sizeof(long));

        for (int j = 0; j < dim[2]; j++) {
            tmp[i][j] = 0;
        }
    }

    for (int i = 0; i < dim[0]; i++) {
        for (int k = 0; k < dim[1]; k++) {
            for (int j = 0; j < dim[2]; j++) {
                tmp[i][j] += A[blkIdx[0] * blkSz + i][blkIdx[1] * blkSz + k]
                             * B[blkIdx[1] * blkSz + k][blkIdx[2] * blkSz + j];
            }
        }
    }

    pthread_mutex_lock(&mutex);

    for (int i = 0; i < dim[0]; i++) {
        for (int j = 0; j < dim[2]; j++) {
            C[blkIdx[0] * blkSz + i][blkIdx[2] * blkSz + j] += tmp[i][j];
        }
    }

    pthread_mutex_unlock(&mutex);
    free(tmp);
    pthread_exit(0);
}

void *__GEMMF(void *arg) {
    Data * __restrict__ data = (Data *)arg;
    const double ** __restrict__ A = (const double **)data->A;
    const double ** __restrict__ B = (const double **)data->B;
    double ** __restrict__ C = (double **)data->C;
    int * __restrict__ dim = data->dim;
    int * __restrict__ blkIdx = data->blkIdx;
    int blkSz = data->blkSz;
    double ** __restrict__ tmp = (double **)malloc(dim[0] * sizeof(double *));

    for (int i = 0; i < dim[0]; i++) {
        tmp[i] = (double *)malloc(dim[2] * sizeof(double));

        for (int j = 0; j < dim[2]; j++) {
            tmp[i][j] = 0;
        }
    }

    for (int i = 0; i < dim[0]; i++) {
        for (int k = 0; k < dim[1]; k++) {
            for (int j = 0; j < dim[2]; j++) {
                tmp[i][j] += A[blkIdx[0] * blkSz + i][blkIdx[1] * blkSz + k]
                             * B[blkIdx[1] * blkSz + k][blkIdx[2] * blkSz + j];
            }
        }
    }

    pthread_mutex_lock(&mutex);

    for (int i = 0; i < dim[0]; i++) {
        for (int j = 0; j < dim[2]; j++) {
            C[blkIdx[0] * blkSz + i][blkIdx[2] * blkSz + j] += tmp[i][j];
        }
    }

    pthread_mutex_unlock(&mutex);
    free(tmp);
    pthread_exit(0);
}

void GEMM(const void ** __restrict__ A, const void ** __restrict__ B, void ** __restrict__ C, int l, int m, int n,
          int blkSz, _Bool int_mat) {
    int lBlk = (l - 1) / blkSz + 1;
    int mBlk = (m - 1) / blkSz + 1;
    int nBlk = (n - 1) / blkSz + 1;

    pthread_mutex_init(&mutex, NULL);
    pthread_t * __restrict__ threads = (pthread_t *)malloc(lBlk * mBlk * nBlk * sizeof(pthread_t));
    Data * __restrict__ data = (Data *)malloc(lBlk * mBlk * nBlk * sizeof(Data));
    int cnt = 0;

    for (int i = 0; i < lBlk; i++) {
        for (int j = 0; j < mBlk; j++) {
            for (int k = 0; k < nBlk; k++) {
                data[cnt].A = A;
                data[cnt].B = B;
                data[cnt].C = C;
                data[cnt].dim[0] = MIN(blkSz, l - blkSz * i);
                data[cnt].dim[1] = MIN(blkSz, m - blkSz * j);
                data[cnt].dim[2] = MIN(blkSz, n - blkSz * k);
                data[cnt].blkIdx[0] = i;
                data[cnt].blkIdx[1] = j;
                data[cnt].blkIdx[2] = k;
                data[cnt].blkSz = blkSz;

                if (int_mat) {
                    pthread_create(&threads[cnt], NULL, __GEMMI, &data[cnt]);
                } else {
                    pthread_create(&threads[cnt], NULL, __GEMMF, &data[cnt]);
                }

                cnt++;
            }
        }
    }

    for (int i = 0; i < cnt; i++) {
        pthread_join(threads[i], NULL);
    }

    free(threads);
    free(data);

    return;
}

void __LUPP(double ** __restrict__ A, int * __restrict__ p, int * __restrict__ flag, int m, int n, double tol) {
    int pv, pv_tmp;
    double *r_tmp;
    int l = MIN(m, n);

    for (int i = 0; i < l - 1; i++) {
        pv = i;

        for (int j = i + 1; j < m; j++) {
            if (fabs(A[pv][i]) < fabs(A[j][i])) {
                pv = j;
            }
        }

        if (pv != i) {
            pv_tmp = p[pv];
            p[pv] = p[i];
            p[i] = pv_tmp;

            r_tmp = A[pv];
            A[pv] = A[i];
            A[i] = r_tmp;
        }


        if (fabs(A[i][i]) < tol) {
            *flag = i;

            return;
        }

        for (int j = i + 1; j < m; j++) {
            A[j][i] /= A[i][i];

            for (int k = i + 1; k < n; k++) {
                A[j][k] -= A[j][i] * A[i][k];
            }
        }
    }

    *flag = fabs(A[l - 1][l - 1]) < tol ? (l - 1) : l;

    return;
}

void __LUCP(double ** __restrict__ A, int * __restrict__ p, int * __restrict__ q, int * __restrict__ flag,
            int m, int n, double tol) {
    int pv1, pv2, pv_tmp;
    double *r_tmp, c_tmp;
    int l = MIN(m, n);

    for (int i = 0; i < l - 1; i++) {
        pv1 = pv2 = i;

        for (int j = i; j < m; j++) {
            for (int k = i; k < n; k++) {
                if (fabs(A[pv1][pv2]) < fabs(A[j][k])) {
                    pv1 = j;
                    pv2 = k;
                }
            }
        }

        if (pv1 != i) {
            pv_tmp = p[pv1];
            p[pv1] = p[i];
            p[i] = pv_tmp;

            r_tmp = A[pv1];
            A[pv1] = A[i];
            A[i] = r_tmp;
        }

        if (pv2 != i) {
            pv_tmp = q[pv2];
            q[pv2] = q[i];
            q[i] = pv_tmp;

            for (int j = 0; j < m; j++) {
                c_tmp = A[j][i];
                A[j][i] = A[j][pv2];
                A[j][pv2] = c_tmp;
            }
        }

        if (fabs(A[i][i]) < tol) {
            *flag = i;

            return;
        }

        for (int j = i + 1; j < m; j++) {
            A[j][i] /= A[i][i];

            for (int k = i + 1; k < n; k++) {
                A[j][k] -= A[j][i] * A[i][k];
            }
        }
    }

    *flag = fabs(A[l - 1][l - 1]) < tol ? (l - 1) : l;

    return;
}

void LU(double ** __restrict__ A, int * __restrict__ p, int * __restrict__ q, int * __restrict__ flag,
        int m, int n, _Bool cp, double tol) {
    if (cp) {
        __LUCP(A, p, q, flag, m, n, tol);
    } else {
        __LUPP(A, p, flag, m, n, tol);
    }

    return;
}

void CHOL(double ** __restrict__ A, int * __restrict__ flag, int n, double tol) {
    double tmp;

    for (int i = 0; i < n; i++) {
        if (A[i][i] < tol) {
            *flag = i;

            return;
        }

        for (int j = i + 1; j < n; j++) {
            tmp = A[i][j] / A[i][i];

            for (int k = j; k < n; k++) {
                A[j][k] -= tmp * A[i][k];
            }
        }

        tmp = sqrt(A[i][i]);

        for (int j = i; j < n; j++) {
            A[i][j] /= tmp;
        }
    }

    *flag = n;

    return;
}

void QR(double ** __restrict__ A, double * __restrict__ v, int * __restrict__ flag, int m, int n, double tol) {
    double norm, u1, tmp;
    int s;
    int l = MIN(m, n - 1);

    for (int i = 0; i < l; i++) {
        norm = 0;
        s = A[i][i] < 0 ? -1 : 1;

        for (int j = i; j < n; j++) {
            norm += A[i][j] * A[i][j];
        }

        norm = sqrt(norm);
        u1 = A[i][i] + s * norm;

        if (fabs(norm) < tol) {
            *flag = i;

            return;
        }

        v[i] = u1 / (s * norm);
        A[i][i] = -s * norm;

        for (int j = i + 1; j < n; j++) {
            A[i][j] /= u1;
        }

        for (int j = i + 1; j < m; j++) {
            tmp = A[j][i];

            for (int k = i + 1; k < n; k++) {
                tmp += A[i][k] * A[j][k];
            }

            A[j][i] -= tmp * v[i];

            for (int k = i + 1; k < n; k++) {
                A[j][k] -= tmp * v[i] * A[i][k];
            }
        }
    }

    if (n == m & fabs(A[n - 1][n - 1]) < tol) {
        *flag = n - 1;
    } else {
        *flag = m;
    }

    return;
}