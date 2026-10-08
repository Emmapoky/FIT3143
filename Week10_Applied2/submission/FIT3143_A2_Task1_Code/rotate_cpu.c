/*
 * rotate_cpu.c
 * FIT3143 Parallel Computing, Applied #2, Task 1: CPU reference rotation
 *
 * Team:
 *   Erwyna Soo Wen Xin  36555789  esoo0013@student.monash.edu
 *   Taabish Farooq Bhat 35473932  ttaa0006@student.monash.edu
 * Task 1 (this file): Taabish Farooq Bhat
 *
 * Plain C copy of the v0 baseline in rotate_cuda.cu (same maths, same
 * rounding). It runs anywhere, so we used it to test the rotation maths
 * before touching the GPU, and to get a serial time for an 8K image.
 *
 * Build: cc -O2 -ffp-contract=off -o rotate_cpu rotate_cpu.c -lm
 * Run:   ./rotate_cpu            self-tests, then 8K timing at 30 degrees
 *        ./rotate_cpu 45         same, timing at 45 degrees
 * -ffp-contract=off keeps a*b+c as two roundings, like nvcc --fmad=false.
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

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
    /* cos(90 deg) is about 6e-17 in floating point; snap it to 0 */
    if (fabsf(r.c) < 1e-7f) r.c = 0.0f;
    if (fabsf(r.s) < 1e-7f) r.s = 0.0f;
    r.cx = 0.5f * (w - 1);
    r.cy = 0.5f * (h - 1);
    return r;
}

/* Inverse mapping with y flipped, so the turn is counterclockwise on
 * screen. Every destination pixel gets exactly one value: no holes. */
static void src_coord(Rot r, int x, int y, float *sx, float *sy)
{
    float dx = (float)x - r.cx;
    float dy = (float)y - r.cy;
    *sx = r.cx + r.c * dx - r.s * dy;
    *sy = r.cy + r.s * dx + r.c * dy;
}

/* Serial nearest neighbour rotation, one pixel at a time. */
static void rotate_nearest(const u8 *src, u8 *dst, int w, int h, Rot r)
{
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

/* Reads one channel of a source pixel, or 0 if it is off the image. */
static float fetch(const u8 *src, int w, int h, int x, int y, int ch)
{
    if (x < 0 || x >= w || y < 0 || y >= h)
        return 0.0f; /* outside counts as black, like texture border mode */
    return (float)src[((size_t)y * w + x) * 3 + ch];
}

/* Serial bilinear rotation: blends the 4 nearest source pixels. */
static void rotate_bilinear(const u8 *src, u8 *dst, int w, int h, Rot r)
{
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

/* Wall-clock time in milliseconds for timing the CPU. */
static double now_ms(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e3 + t.tv_nsec / 1e6;
}

/* Makes a random RGB test image. */
static u8 *random_image(int w, int h)
{
    size_t n = (size_t)w * h * 3;
    u8 *img = malloc(n);
    for (size_t i = 0; i < n; i++)
        img[i] = (u8)(rand() & 0xFF);
    return img;
}

static int g_fail = 0;

/* Prints PASS or FAIL for one self-test and counts failures. */
static void report(const char *name, int ok)
{
    printf("  %-52s %s\n", name, ok ? "PASS" : "FAIL");
    if (!ok)
        g_fail++;
}

/* expect[x, y] = src[fx(x, y), fy(x, y)] for an exact pixel permutation */
static int matches_perm(const u8 *src, const u8 *dst, int n, int kind)
{
    for (int i = 0; i < n; i++)     /* destination row */
        for (int j = 0; j < n; j++) /* destination column */
        {
            int si, sj; /* source row, column */
            if (kind == 90) { si = j; sj = n - 1 - i; }
            else if (kind == 180) { si = n - 1 - i; sj = n - 1 - j; }
            else { si = n - 1 - j; sj = i; } /* 270 */
            if (memcmp(dst + ((size_t)i * n + j) * 3,
                       src + ((size_t)si * n + sj) * 3, 3) != 0)
                return 0;
        }
    return 1;
}

/* Checks the maths: identity, exact 90/180/270 turns, direction. */
static void self_tests(void)
{
    printf("Self-tests\n");
    for (int k = 0; k < 2; k++) {
        int n = k ? 256 : 257; /* even and odd sizes: centre on or off */
        size_t bytes = (size_t)n * n * 3;
        u8 *src = random_image(n, n), *dst = malloc(bytes);
        char name[96];

        Rot r0 = make_rot(0, n, n);
        rotate_nearest(src, dst, n, n, r0);
        snprintf(name, sizeof(name), "%dx%d nearest, 0 deg is identity", n, n);
        report(name, !memcmp(src, dst, bytes));
        rotate_bilinear(src, dst, n, n, r0);
        snprintf(name, sizeof(name), "%dx%d bilinear, 0 deg is identity", n,
                 n);
        report(name, !memcmp(src, dst, bytes));

        int kinds[3] = {90, 180, 270};
        for (int q = 0; q < 3; q++) {
            Rot r = make_rot(kinds[q], n, n);
            rotate_nearest(src, dst, n, n, r);
            snprintf(name, sizeof(name),
                     "%dx%d nearest, %d deg is exact CCW permutation", n, n,
                     kinds[q]);
            report(name, matches_perm(src, dst, n, kinds[q]));
            rotate_bilinear(src, dst, n, n, r);
            snprintf(name, sizeof(name),
                     "%dx%d bilinear, %d deg is exact CCW permutation", n,
                     n, kinds[q]);
            report(name, matches_perm(src, dst, n, kinds[q]));
        }

        /* 4 x 90 degrees should give the original back */
        u8 *a = malloc(bytes), *b = malloc(bytes);
        memcpy(a, src, bytes);
        Rot r90 = make_rot(90, n, n);
        for (int t = 0; t < 4; t++) {
            rotate_nearest(a, b, n, n, r90);
            memcpy(a, b, bytes);
        }
        snprintf(name, sizeof(name), "%dx%d four 90 deg turns = identity", n,
                 n);
        report(name, !memcmp(a, src, bytes));
        free(a);
        free(b);
        free(src);
        free(dst);
    }

    /* Direction: a marker on the right edge must end up on the top edge
     * after +90 degrees, because the rotation is counterclockwise. */
    int n = 101;
    u8 *src = calloc((size_t)n * n * 3, 1), *dst = malloc((size_t)n * n * 3);
    src[((size_t)50 * n + 100) * 3] = 255; /* red dot, middle of right edge */
    rotate_nearest(src, dst, n, n, make_rot(90, n, n));
    report("+90 deg moves right-edge dot to top edge (CCW)",
           dst[((size_t)0 * n + 50) * 3] == 255);
    free(src);
    free(dst);

    /* 30 degrees: corners of the output have no source and must be black,
     * the centre pixel must not move. */
    n = 201;
    src = random_image(n, n);
    dst = malloc((size_t)n * n * 3);
    rotate_bilinear(src, dst, n, n, make_rot(30, n, n));
    size_t c = ((size_t)100 * n + 100) * 3;
    report("30 deg: centre pixel fixed, corner pixel black",
           !memcmp(dst + c, src + c, 3) && dst[0] == 0 && dst[1] == 0);
    free(src);
    free(dst);
}

/* Runs the self-tests, then times an 8K rotation on one core. */
int main(int argc, char **argv)
{
    double angle = argc > 1 ? atof(argv[1]) : 30.0;
    srand(3143);
    self_tests();
    printf("%s\n\n", g_fail ? "SOME TESTS FAILED" : "all tests passed");

    int w = 7680, h = 4320;
    size_t bytes = (size_t)w * h * 3;
    u8 *src = random_image(w, h), *dst = malloc(bytes);
    Rot r = make_rot(angle, w, h);
    printf("8K timing: %dx%d RGB (%.1f MB), %.1f deg, one core\n", w, h,
           bytes / 1e6, angle);
    for (int bl = 0; bl < 2; bl++) {
        double best = 1e30;
        for (int rep = 0; rep < 3; rep++) { /* best of 3 */
            double t0 = now_ms();
            if (bl)
                rotate_bilinear(src, dst, w, h, r);
            else
                rotate_nearest(src, dst, w, h, r);
            double t = now_ms() - t0;
            if (t < best)
                best = t;
        }
        printf("  %-9s %8.1f ms  (%.1f Mpixel/s)\n",
               bl ? "bilinear" : "nearest", best, (double)w * h / best / 1e3);
    }
    free(src);
    free(dst);
    return g_fail != 0;
}
