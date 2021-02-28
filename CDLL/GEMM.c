#include<stdlib.h>
#include<stdio.h>
#include<pthread.h>

#define MIN(a, b) ((a) > (b) ? (b) : (a))
#define BLK_SZ 500

typedef struct _Data {
    const void ** __restrict__ A;
    const void ** __restrict__ B;
    void ** __restrict__ C;
    int dim[3];
    int blkIdx[3];
} Data;

pthread_mutex_t mutex;

void *GEMMInt(void *arg) {
    Data * __restrict__ data = (Data *)arg;
    const long ** __restrict__ A = (const long **)data->A;
    const long ** __restrict__ B = (const long **)data->B;
    long ** __restrict__ C = (long **)data->C;
    int * __restrict__ dim = data->dim;
    int * __restrict__ blkIdx = data->blkIdx;
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
                tmp[i][j] += A[blkIdx[0] * BLK_SZ + i][blkIdx[1] * BLK_SZ + k] * B[blkIdx[1] * BLK_SZ + k][blkIdx[2] * BLK_SZ + j];
            }
        }
    }

    pthread_mutex_lock(&mutex);
    
    for (int i = 0; i < dim[0]; i++) {
        for (int j = 0; j < dim[2]; j++) {
            C[blkIdx[0] * BLK_SZ + i][blkIdx[2] * BLK_SZ + j] += tmp[i][j];
        }
    }
    
    pthread_mutex_unlock(&mutex);
    free(tmp);
    pthread_exit(0);
}

void *GEMMFloat(void *arg) {
    Data * __restrict__ data = (Data *)arg;
    const double ** __restrict__ A = (const double **)data->A;
    const double ** __restrict__ B = (const double **)data->B;
    double ** __restrict__ C = (double **)data->C;
    int * __restrict__ dim = data->dim;
    int * __restrict__ blkIdx = data->blkIdx;
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
                tmp[i][j] += A[blkIdx[0] * BLK_SZ + i][blkIdx[1] * BLK_SZ + k] * B[blkIdx[1] * BLK_SZ + k][blkIdx[2] * BLK_SZ + j];
            }
        }
    }

    pthread_mutex_lock(&mutex);

    for (int i = 0; i < dim[0]; i++) {
        for (int j = 0; j < dim[2]; j++) {
            C[blkIdx[0] * BLK_SZ + i][blkIdx[2] * BLK_SZ + j] += tmp[i][j];
        }
    }

    pthread_mutex_unlock(&mutex);
    free(tmp);
    pthread_exit(0);
}

void GEMM(const void ** __restrict__ A, const void ** __restrict__ B, void ** __restrict__ C, int l, int m, int n, _Bool intFlag) {
    int lBlk = (l - 1) / BLK_SZ + 1;
    int mBlk = (m - 1) / BLK_SZ + 1;
    int nBlk = (n - 1) / BLK_SZ + 1;

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
                data[cnt].dim[0] = MIN(BLK_SZ, l - BLK_SZ * i);
                data[cnt].dim[1] = MIN(BLK_SZ, m - BLK_SZ * j);
                data[cnt].dim[2] = MIN(BLK_SZ, n - BLK_SZ * k);
                data[cnt].blkIdx[0] = i;
                data[cnt].blkIdx[1] = j;
                data[cnt].blkIdx[2] = k;

                if (intFlag) {
                    pthread_create(&threads[cnt], NULL, GEMMInt, &data[cnt]);
                } else {
                    pthread_create(&threads[cnt], NULL, GEMMFloat, &data[cnt]);
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