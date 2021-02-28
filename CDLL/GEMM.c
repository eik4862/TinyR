#include<stdlib.h>
#include<stdio.h>
#include<pthread.h>

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

void *GEMMInt(void *arg) {
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
                tmp[i][j] += A[blkIdx[0] * blkSz + i][blkIdx[1] * blkSz + k] * B[blkIdx[1] * blkSz + k][blkIdx[2] * blkSz + j];
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

void *GEMMFloat(void *arg) {
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
                tmp[i][j] += A[blkIdx[0] * blkSz + i][blkIdx[1] * blkSz + k] * B[blkIdx[1] * blkSz + k][blkIdx[2] * blkSz + j];
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

void GEMM(const void ** __restrict__ A, const void ** __restrict__ B, void ** __restrict__ C, int l, int m, int n, _Bool intFlag, int blkSz) {
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