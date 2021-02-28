#include<stdlib.h>
#include<stdio.h>
#include<pthread.h>

#define MIN(a, b) ((a) > (b) ? (b) : (a))

typedef struct _Data {
    const void * __restrict__ v;
    const void * __restrict__ w;
    void * __restrict__ p;
    int n;
    int blkIdx;
    int blkSz;
} Data;

pthread_mutex_t mutex;

void *DOTInt(void *arg) {
    Data * __restrict__ data = (Data *)arg;
    const long * __restrict__ v = (const long *)data->v;
    const long * __restrict__ w = (const long *)data->w;
    long * __restrict__ p = (long *)data->p;
    int n = (int)data->n;
    int blkIdx = (int)data->blkIdx;
    int blkSz = (int)data->blkSz;
    long tmp = 0;

    for (int i = 0; i < n; i++) {
        tmp += v[blkIdx * blkSz + i] * w[blkIdx * blkSz + i];
    }

    pthread_mutex_lock(&mutex);
    *p += tmp;
    pthread_mutex_unlock(&mutex);
    pthread_exit(0);
}

void *DOTFloat(void *arg) {
    Data * __restrict__ data = (Data *)arg;
    const double * __restrict__ v = (const double *)data->v;
    const double * __restrict__ w = (const double *)data->w;
    double * __restrict__ p = (double *)data->p;
    int n = (int)data->n;
    int blkIdx = (int)data->blkIdx;
    int blkSz = (int)data->blkSz;
    double tmp = 0;

    for (int i = 0; i < n; i++) {
        tmp += v[blkIdx * blkSz + i] * w[blkIdx * blkSz + i];
    }

    pthread_mutex_lock(&mutex);
    *p += tmp;
    pthread_mutex_unlock(&mutex);
    pthread_exit(0);
}

void DOT(const void * __restrict__ v, const void * __restrict__ w, void * __restrict__ p, int n, _Bool intFlag, int blkSz) {
    int nBlk = (n - 1) / blkSz + 1;

    pthread_mutex_init(&mutex, NULL);
    pthread_t * __restrict__ threads = (pthread_t *)malloc(nBlk * sizeof(pthread_t));
    Data * __restrict__ data = (Data *)malloc(nBlk * sizeof(Data));

    for (int i = 0; i < nBlk; i++) {
        data[i].v = v;
        data[i].w = w;
        data[i].p = p;
        data[i].n = MIN(blkSz, n - blkSz * i);
        data[i].blkIdx = i;
        data[i].blkSz = blkSz;

        if (intFlag) {
            pthread_create(&threads[i], NULL, DOTInt, &data[i]);
        } else {
            pthread_create(&threads[i], NULL, DOTFloat, &data[i]);
        }
    }

    for (int i = 0; i < nBlk; i++) {
        pthread_join(threads[i], NULL);
    }

    free(threads);
    free(data);

    return;
}