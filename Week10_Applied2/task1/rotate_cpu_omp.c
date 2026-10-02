/*
 * rotate_cpu_omp.c
 * FIT3143 Parallel Computing, Applied #2, Task 1: multi-core CPU baseline
 *
 * Team:
 *   Erwyna Soo Wen Xin  36555789  esoo0013@student.monash.edu
 *   Taabish Farooq Bhat 35473932  ttaa0006@student.monash.edu
 * Task 1 (this file): Taabish Farooq Bhat
 *
 * Same maths and rounding as v0 in rotate_cuda.cu and rotate_cpu.c, but
 * the row loop is split across all CPU cores with OpenMP. One core is an
 * unfair baseline for a GPU, so this gives the fairer comparison.
 *
 * Build: gcc -O3 -fopenmp -ffp-contract=off -o rotate_cpu_omp \
 *            rotate_cpu_omp.c -lm
 * Run:   ./rotate_cpu_omp [angle] [csv]     (default 30 degrees)
 * -ffp-contract=off keeps a*b+c as two roundings, like nvcc --fmad=false.
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef _OPENMP
#include <omp.h>
#endif

typedef unsigned char u8;

typedef struct {
    float c, s;   /* cos(theta), sin(theta) */
    float cx, cy; /* centre of rotation */
} Rot;

/* Builds cos, sin and the image centre for a rotation in degrees. */
static Rot make_rot(double deg, int w, int h)
{
    Rot r;
    double t = deg * M_PI / 180.0;
    r.c = (float)cos(t);
    r.s = (float)sin(t);
    if (fabsf(r.c) < 1e-7f) r.c = 0.0f;
    if (fabsf(r.s) < 1e-7f) r.s = 0.0f;
    r.cx = 0.5f * (w - 1);
    r.cy = 0.5f * (h - 1);
    return r;
}

/* Inverse mapping with y flipped, as in the GPU kernels. */
static void src_coord(Rot r, int x, int y, float *sx, float *sy)
{
    float dx = (float)x - r.cx;
    float dy = (float)y - r.cy;
    *sx = r.cx + r.c * dx - r.s * dy;
    *sy = r.cy + r.s * dx + r.c * dy;
}

/* Reads one channel of a source pixel, or 0 if it is off the image. */
static float fetch(const u8 *src, int w, int h, int x, int y, int ch)
{
    if (x < 0 || x >= w || y < 0 || y >= h)
        return 0.0f; /* outside counts as black */
    return (float)src[((size_t)y * w + x) * 3 + ch];
}

/* Rows are independent, so a static split of rows across threads has no
 * races: each output pixel still has exactly one writer. */
static void rotate_nearest(const u8 *src, u8 *dst, int w, int h, Rot r)
{
#pragma omp parallel for schedule(static)
    for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++) {
            float sx, sy;
            src_coord(r, x, y, &sx, &sy);
            int ix = (int)floorf(sx + 0.5f);
            int iy = (int)floorf(sy + 0.5f);
            size_t o = ((size_t)y * w + x) * 3;
            if (ix >= 0 && ix < w && iy >= 0 && iy < h) {
                memcpy(dst + o, src + ((size_t)iy * w + ix) * 3, 3);
            } else {
                dst[o] = dst[o + 1] = dst[o + 2] = 0;
            }
        }
}

/* Bilinear rotation, rows split across threads like nearest. */
static void rotate_bilinear(const u8 *src, u8 *dst, int w, int h, Rot r)
{
#pragma omp parallel for schedule(static)
    for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++) {
            float sx, sy;
            src_coord(r, x, y, &sx, &sy);
            float fx = floorf(sx), fy = floorf(sy);
            int x0 = (int)fx, y0 = (int)fy;
            float ax = sx - fx, ay = sy - fy;
            size_t o = ((size_t)y * w + x) * 3;
            for (int ch = 0; ch < 3; ch++) {
                float top = fetch(src, w, h, x0, y0, ch) * (1.0f - ax)
                          + fetch(src, w, h, x0 + 1, y0, ch) * ax;
                float bot = fetch(src, w, h, x0, y0 + 1, ch) * (1.0f - ax)
                          + fetch(src, w, h, x0 + 1, y0 + 1, ch) * ax;
                float v = top * (1.0f - ay) + bot * ay;
                dst[o + ch] = (u8)(v + 0.5f);
            }
        }
}

/* Wall-clock time in milliseconds. */
static double now_ms(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e3 + t.tv_nsec / 1e6;
}

/* How many threads OpenMP will use (1 if built without it). */
static int max_threads(void)
{
#ifdef _OPENMP
    return omp_get_max_threads();
#else
    return 1;
#endif
}

/* Sets the OpenMP thread count for the next timed run. */
static void use_threads(int n)
{
#ifdef _OPENMP
    omp_set_num_threads(n);
#else
    (void)n;
#endif
}

/* Warm-up run, then the mean of reps runs (same method as the GPU). */
static double time_it(int bl, const u8 *src, u8 *dst, int w, int h, Rot r,
                      int reps)
{
    if (bl) rotate_bilinear(src, dst, w, h, r);
    else rotate_nearest(src, dst, w, h, r);
    double t0 = now_ms();
    for (int i = 0; i < reps; i++) {
        if (bl) rotate_bilinear(src, dst, w, h, r);
        else rotate_nearest(src, dst, w, h, r);
    }
    return (now_ms() - t0) / reps;
}

/* Times 8K rotation on 1 thread and on all threads, checks they match. */
int main(int argc, char **argv)
{
    double angle = argc > 1 ? atof(argv[1]) : 30.0;
    const char *csv = argc > 2 ? argv[2] : NULL;
    int w = 7680, h = 4320;
    size_t bytes = (size_t)w * h * 3;
    u8 *src = malloc(bytes), *ref = malloc(bytes), *dst = malloc(bytes);
    srand(3143);
    for (size_t i = 0; i < bytes; i++)
        src[i] = (u8)(rand() & 0xFF);
    Rot r = make_rot(angle, w, h);
    int nt = max_threads();

    FILE *f = csv ? fopen(csv, "w") : NULL;
    if (f)
        fprintf(f, "kernel,threads,ms,speedup_vs_1core,"
                   "parallel_efficiency,mismatch\n");
    printf("8K %dx%d, %.1f deg, up to %d threads (OpenMP)\n", w, h, angle,
           nt);
    for (int bl = 0; bl < 2; bl++) {
        const char *name = bl ? "bilinear" : "nearest";
        use_threads(1);
        double t1 = time_it(bl, src, ref, w, h, r, 3);
        use_threads(nt);
        double tn = time_it(bl, src, dst, w, h, r, 10);
        size_t bad = 0; /* bytes that differ from the one-thread result */
        for (size_t i = 0; i < bytes; i++)
            bad += ref[i] != dst[i];
        double su = t1 / tn;
        printf("  %-9s 1 thread %8.1f ms | %d threads %8.1f ms | "
               "%.2fx, efficiency %.0f%% | mismatch %zu\n",
               name, t1, nt, tn, su, 100.0 * su / nt, bad);
        if (f) {
            fprintf(f, "%s,1,%.3f,1.00,1.00,0\n", name, t1);
            fprintf(f, "%s,%d,%.3f,%.2f,%.2f,%zu\n", name, nt, tn, su,
                    su / nt, bad);
        }
    }
    if (f)
        fclose(f);
    free(src);
    free(ref);
    free(dst);
    return 0;
}
