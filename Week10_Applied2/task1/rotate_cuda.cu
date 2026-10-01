/*
 * rotate_cuda.cu
 * FIT3143 Parallel Computing, Applied #2, Task 1: image rotation on a GPU
 *
 * Team:
 *   Erwyna Soo Wen Xin  36555789  esoo0013@student.monash.edu
 *   Taabish Farooq Bhat 35473932  ttaa0006@student.monash.edu
 *
 * Rotates an RGB image counterclockwise by theta about its centre using
 * R = [[cos t, -sin t], [sin t, cos t]]. Every variant below shows one
 * CUDA feature, and all GPU output is checked against the CPU output.
 *
 *   v0  CPU serial baseline (nearest and bilinear)
 *   v1  GPU naive 1D grid, nearest neighbour
 *   v2  GPU 2D grid of 2D blocks, nearest neighbour
 *   v3  GPU 2D grid, bilinear interpolation
 *   v4  v2 again but with pageable host memory (v2 uses pinned)
 *   v5  CUDA streams: (a) one image in row chunks, (b) a batch of images
 *   v6  texture object with hardware bilinear filtering
 *
 * Build (Colab T4):
 *   nvcc -O3 -arch=sm_75 --fmad=false -o rotate_cuda rotate_cuda.cu
 * --fmad=false stops nvcc fusing a*b+c into one FMA, so GPU and CPU
 * round the same way and the outputs can be compared byte for byte.
 *
 * Run:
 *   ./rotate_cuda                       8K synthetic image, 30 degrees
 *   ./rotate_cuda --w 3840 --h 2160 --angle 45 --csv results.csv
 *   ./rotate_cuda --in photo.ppm --save out     (binary P6 PPM only)
 *   ./rotate_cuda --mode blocks|streams|main|all
 */

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <cuda_runtime.h>

#define CUDA_CHECK(call)                                                  \
    do {                                                                  \
        cudaError_t err_ = (call);                                        \
        if (err_ != cudaSuccess) {                                        \
            fprintf(stderr, "CUDA error \"%s\" at %s:%d\n",               \
                    cudaGetErrorString(err_), __FILE__, __LINE__);        \
            exit(EXIT_FAILURE);                                           \
        }                                                                 \
    } while (0)

// Kernel launches return nothing, so check the launch and the run apart.
#define CUDA_CHECK_LAUNCH() CUDA_CHECK(cudaGetLastError())

typedef unsigned char u8;

struct Rot {
    float c, s;   // cos(theta), sin(theta), worked out once on the host
    float cx, cy; // centre of rotation in pixel coordinates
};

/* ===================== shared host/device pixel maths ================== */

// Inverse mapping: for destination pixel (x, y) find where it came from.
// Pixel rows grow downwards, so y is flipped into Cartesian form, R^-1
// (= R^T) is applied, and y is flipped back. Worked through, that gives
// the two lines below, and the picture turns counterclockwise on screen.
__host__ __device__ inline void src_coord(const Rot r, int x, int y,
                                          float *sx, float *sy)
{
    float dx = (float)x - r.cx;
    float dy = (float)y - r.cy;
    *sx = r.cx + r.c * dx - r.s * dy;
    *sy = r.cy + r.s * dx + r.c * dy;
}

__host__ __device__ inline void pixel_nearest(const u8 *src, u8 *dst,
                                              int w, int h, const Rot r,
                                              int x, int y)
{
    float sx, sy;
    src_coord(r, x, y, &sx, &sy);
    int ix = (int)floorf(sx + 0.5f);   // round half up, same on CPU and GPU
    int iy = (int)floorf(sy + 0.5f);
    size_t o = ((size_t)y * w + x) * 3;
    if (ix >= 0 && ix < w && iy >= 0 && iy < h) {
        size_t i = ((size_t)iy * w + ix) * 3;
        dst[o] = src[i];
        dst[o + 1] = src[i + 1];
        dst[o + 2] = src[i + 2];
    } else {
        // Corners with no source pixel become black.
        dst[o] = dst[o + 1] = dst[o + 2] = 0;
    }
}

// Pixels outside the image read as 0, which is exactly what the texture
// unit does in border mode, so v3 and v6 can be compared fairly.
__host__ __device__ inline float fetch(const u8 *src, int w, int h,
                                       int x, int y, int ch)
{
    if (x < 0 || x >= w || y < 0 || y >= h)
        return 0.0f;
    return (float)src[((size_t)y * w + x) * 3 + ch];
}

__host__ __device__ inline void pixel_bilinear(const u8 *src, u8 *dst,
                                               int w, int h, const Rot r,
                                               int x, int y)
{
    float sx, sy;
    src_coord(r, x, y, &sx, &sy);
    float fx = floorf(sx), fy = floorf(sy);
    int x0 = (int)fx, y0 = (int)fy;
    float ax = sx - fx, ay = sy - fy; // distance past the top-left neighbour
    size_t o = ((size_t)y * w + x) * 3;
    for (int ch = 0; ch < 3; ch++) {
        // Blend the 4 neighbours: 4 reads per channel instead of 1, so
        // this costs more memory traffic than nearest but has no jaggies.
        float top = fetch(src, w, h, x0, y0, ch) * (1.0f - ax)
                  + fetch(src, w, h, x0 + 1, y0, ch) * ax;
        float bot = fetch(src, w, h, x0, y0 + 1, ch) * (1.0f - ax)
                  + fetch(src, w, h, x0 + 1, y0 + 1, ch) * ax;
        float v = top * (1.0f - ay) + bot * ay;
        dst[o + ch] = (u8)(v + 0.5f);
    }
}

/* ============================== kernels ================================ */

// v1: one flat 1D grid. Simple, but each thread pays for a divide and a
// modulo, and a 256-wide block covers one long thin strip of the output.
__global__ void rotate_nn_1d(const u8 *__restrict__ src,
                             u8 *__restrict__ dst, int w, int h, Rot r)
{
    size_t id = (size_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (id >= (size_t)w * h)
        return; // the last block hangs past the end of the image
    int x = (int)(id % w);
    int y = (int)(id / w);
    pixel_nearest(src, dst, w, h, r, x, y);
}

// v2: 2D grid of 2D blocks. blockIdx picks the output tile, threadIdx the
// pixel inside it. No divide or modulo like v1, which is why it is
// faster. Our sweep shows shape barely matters for nearest (128x1 ~ 16x16).
// y0..y1 lets the streams version run one band of rows at a time.
__global__ void rotate_nn_2d(const u8 *__restrict__ src,
                             u8 *__restrict__ dst, int w, int h, Rot r,
                             int y0, int y1)
{
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = y0 + blockIdx.y * blockDim.y + threadIdx.y;
    if (x >= w || y >= y1)
        return; // grid is rounded up to whole blocks
    pixel_nearest(src, dst, w, h, r, x, y);
}

// v3: same thread layout as v2, bilinear sampling.
__global__ void rotate_bl_2d(const u8 *__restrict__ src,
                             u8 *__restrict__ dst, int w, int h, Rot r,
                             int y0, int y1)
{
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = y0 + blockIdx.y * blockDim.y + threadIdx.y;
    if (x >= w || y >= y1)
        return;
    pixel_bilinear(src, dst, w, h, r, x, y);
}

// v6 step 1: textures have no 3-channel 8-bit format, so pad RGB to RGBA.
__global__ void pack_rgba(const u8 *__restrict__ src, uchar4 *dst,
                          size_t pitch, int w, int h)
{
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    if (x >= w || y >= h)
        return;
    size_t i = ((size_t)y * w + x) * 3;
    uchar4 *row = (uchar4 *)((char *)dst + (size_t)y * pitch);
    row[x] = make_uchar4(src[i], src[i + 1], src[i + 2], 255);
}

// v6 step 2: the texture unit does the 4-neighbour blend in hardware and
// reads through its own cache. Its weights only have 8 fractional bits,
// so results can differ from v3 by a level or two.
__global__ void rotate_tex(cudaTextureObject_t tex, u8 *__restrict__ dst,
                           int w, int h, Rot r)
{
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    if (x >= w || y >= h)
        return;
    float sx, sy;
    src_coord(r, x, y, &sx, &sy);
    // Texel centres sit at +0.5 in unnormalised texture coordinates.
    float4 p = tex2D<float4>(tex, sx + 0.5f, sy + 0.5f);
    size_t o = ((size_t)y * w + x) * 3;
    dst[o] = (u8)(p.x * 255.0f + 0.5f);
    dst[o + 1] = (u8)(p.y * 255.0f + 0.5f);
    dst[o + 2] = (u8)(p.z * 255.0f + 0.5f);
}

/* ============================ host helpers ============================= */

static double now_ms(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e3 + t.tv_nsec / 1e6;
}

static float event_ms(cudaEvent_t a, cudaEvent_t b)
{
    float ms;
    CUDA_CHECK(cudaEventElapsedTime(&ms, a, b));
    return ms;
}

// A made-up but photo-sized test card: gradients, a checkerboard and thin
// grid lines, so bad interpolation or wrong direction is easy to spot.
static void make_test_image(u8 *img, int w, int h)
{
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            size_t o = ((size_t)y * w + x) * 3;
            int line = (x % 256 < 3) || (y % 256 < 3);
            int check = ((x / 64) + (y / 64)) & 1;
            img[o] = line ? 255 : (u8)(255.0 * x / (w - 1));
            img[o + 1] = line ? 255 : (u8)(255.0 * y / (h - 1));
            img[o + 2] = line ? 255 : (check ? 200 : 40);
        }
    }
    // A red block on the right edge: after +90 degrees it should be on top.
    for (int y = h / 2 - h / 16; y < h / 2 + h / 16; y++)
        for (int x = w - w / 8; x < w; x++) {
            size_t o = ((size_t)y * w + x) * 3;
            img[o] = 255;
            img[o + 1] = img[o + 2] = 0;
        }
}

static int skip_ws_comments(FILE *f)
{
    int c = fgetc(f);
    while (c == '#' || c == ' ' || c == '\n' || c == '\r' || c == '\t') {
        if (c == '#')
            while (c != '\n' && c != EOF)
                c = fgetc(f);
        c = fgetc(f);
    }
    return c;
}

// Minimal binary PPM (P6, maxval 255) reader. Returns malloc'd pixels.
static u8 *read_ppm(const char *path, int *w, int *h)
{
    FILE *f = fopen(path, "rb");
    if (!f) {
        perror(path);
        return NULL;
    }
    int maxv = 0;
    char magic[3] = {0};
    if (fread(magic, 1, 2, f) != 2 || strcmp(magic, "P6") != 0) {
        fprintf(stderr, "%s: only binary P6 PPM is supported\n", path);
        fclose(f);
        return NULL;
    }
    int vals[3];
    for (int k = 0; k < 3; k++) {
        ungetc(skip_ws_comments(f), f);
        if (fscanf(f, "%d", &vals[k]) != 1) {
            fclose(f);
            return NULL;
        }
    }
    *w = vals[0];
    *h = vals[1];
    maxv = vals[2];
    fgetc(f); // exactly one whitespace byte before the pixel data
    size_t n = (size_t)(*w) * (*h) * 3;
    u8 *img = (u8 *)malloc(n);
    if (maxv != 255 || !img || fread(img, 1, n, f) != n) {
        fprintf(stderr, "%s: bad or truncated PPM\n", path);
        free(img);
        img = NULL;
    }
    fclose(f);
    return img;
}

static void write_ppm(const char *path, const u8 *img, int w, int h)
{
    FILE *f = fopen(path, "wb");
    if (!f) {
        perror(path);
        return;
    }
    fprintf(f, "P6\n%d %d\n255\n", w, h);
    fwrite(img, 1, (size_t)w * h * 3, f);
    fclose(f);
}

static void rotate_cpu(const u8 *src, u8 *dst, int w, int h, Rot r,
                       int bilinear)
{
    for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++) {
            if (bilinear)
                pixel_bilinear(src, dst, w, h, r, x, y);
            else
                pixel_nearest(src, dst, w, h, r, x, y);
        }
}

struct Check {
    size_t mismatch; // bytes that differ from the CPU answer
    int max_diff;    // largest absolute difference in intensity levels
};

static Check compare(const u8 *a, const u8 *b, size_t n)
{
    Check c = {0, 0};
    for (size_t i = 0; i < n; i++) {
        int d = abs((int)a[i] - (int)b[i]);
        if (d) {
            c.mismatch++;
            if (d > c.max_diff)
                c.max_diff = d;
        }
    }
    return c;
}

/* ====================== GPU state and one pipeline ===================== */

enum Kind { K_NN_1D, K_NN_2D, K_BL_2D, K_TEX };

struct Gpu {
    int w, h;
    size_t bytes;
    Rot r;
    dim3 block;
    u8 *d_src, *d_dst;
    uchar4 *d_rgba; // pitched RGBA copy, only used by the texture path
    size_t pitch;
    cudaTextureObject_t tex;
    int tex_ok;
    cudaEvent_t ev[4];
};

static dim3 grid_for(dim3 block, int w, int rows)
{
    // Round up so the ragged right and bottom edges still get threads.
    return dim3((w + block.x - 1) / block.x, (rows + block.y - 1) / block.y);
}

static void launch(const Gpu &g, Kind k, dim3 block, cudaStream_t st,
                   int y0, int y1)
{
    dim3 grid = grid_for(block, g.w, y1 - y0);
    switch (k) {
    case K_NN_1D: {
        int threads = block.x * block.y;
        size_t n = (size_t)g.w * g.h;
        unsigned blocks = (unsigned)((n + threads - 1) / threads);
        rotate_nn_1d<<<blocks, threads, 0, st>>>(g.d_src, g.d_dst, g.w, g.h,
                                                 g.r);
        break;
    }
    case K_NN_2D:
        rotate_nn_2d<<<grid, block, 0, st>>>(g.d_src, g.d_dst, g.w, g.h,
                                             g.r, y0, y1);
        break;
    case K_BL_2D:
        rotate_bl_2d<<<grid, block, 0, st>>>(g.d_src, g.d_dst, g.w, g.h,
                                             g.r, y0, y1);
        break;
    case K_TEX:
        pack_rgba<<<grid, block, 0, st>>>(g.d_src, g.d_rgba, g.pitch, g.w,
                                          g.h);
        CUDA_CHECK_LAUNCH();
        rotate_tex<<<grid, block, 0, st>>>(g.tex, g.d_dst, g.w, g.h, g.r);
        break;
    }
    CUDA_CHECK_LAUNCH();
}

static void setup_texture(Gpu &g)
{
    cudaDeviceProp p;
    CUDA_CHECK(cudaGetDeviceProperties(&p, 0));
    g.tex_ok = g.w <= p.maxTexture2DLinear[0] &&
               g.h <= p.maxTexture2DLinear[1];
    if (!g.tex_ok)
        return;
    // cudaMallocPitch pads each row so it meets the texture alignment.
    CUDA_CHECK(cudaMallocPitch((void **)&g.d_rgba, &g.pitch,
                               g.w * sizeof(uchar4), g.h));
    cudaResourceDesc res;
    memset(&res, 0, sizeof(res));
    res.resType = cudaResourceTypePitch2D;
    res.res.pitch2D.devPtr = g.d_rgba;
    res.res.pitch2D.desc = cudaCreateChannelDesc<uchar4>();
    res.res.pitch2D.width = g.w;
    res.res.pitch2D.height = g.h;
    res.res.pitch2D.pitchInBytes = g.pitch;
    cudaTextureDesc td;
    memset(&td, 0, sizeof(td)); // border colour stays 0, i.e. black
    td.addressMode[0] = cudaAddressModeBorder;
    td.addressMode[1] = cudaAddressModeBorder;
    td.filterMode = cudaFilterModeLinear;       // hardware bilinear
    td.readMode = cudaReadModeNormalizedFloat;  // bytes come back as 0..1
    td.normalizedCoords = 0;                    // address in pixels
    CUDA_CHECK(cudaCreateTextureObject(&g.tex, &res, &td, NULL));
}

struct Stage {
    double h2d, ker, d2h, tot;
};

// One full pipeline: H2D copy, kernel(s), D2H copy, each stage timed with
// its own pair of CUDA events. The first run is a warm-up and is thrown
// away, then the mean of `reps` runs is returned.
static Stage run_pipeline(Gpu &g, Kind k, const u8 *h_src, u8 *h_dst,
                          int reps)
{
    Stage s = {0, 0, 0, 0};
    for (int it = 0; it <= reps; it++) {
        CUDA_CHECK(cudaEventRecord(g.ev[0]));
        CUDA_CHECK(cudaMemcpy(g.d_src, h_src, g.bytes,
                              cudaMemcpyHostToDevice));
        CUDA_CHECK(cudaEventRecord(g.ev[1]));
        launch(g, k, g.block, 0, 0, g.h);
        CUDA_CHECK(cudaEventRecord(g.ev[2]));
        // Blocking copy: it waits for the kernel since both use stream 0.
        CUDA_CHECK(cudaMemcpy(h_dst, g.d_dst, g.bytes,
                              cudaMemcpyDeviceToHost));
        CUDA_CHECK(cudaEventRecord(g.ev[3]));
        CUDA_CHECK(cudaEventSynchronize(g.ev[3]));
        if (it == 0)
            continue;
        s.h2d += event_ms(g.ev[0], g.ev[1]);
        s.ker += event_ms(g.ev[1], g.ev[2]);
        s.d2h += event_ms(g.ev[2], g.ev[3]);
        s.tot += event_ms(g.ev[0], g.ev[3]);
    }
    s.h2d /= reps;
    s.ker /= reps;
    s.d2h /= reps;
    s.tot /= reps;
    return s;
}

// Kernel only, input already on the device. Used by the block sweep.
static double time_kernel(Gpu &g, Kind k, dim3 block, int reps)
{
    launch(g, k, block, 0, 0, g.h); // warm-up
    CUDA_CHECK(cudaEventRecord(g.ev[0]));
    for (int i = 0; i < reps; i++)
        launch(g, k, block, 0, 0, g.h);
    CUDA_CHECK(cudaEventRecord(g.ev[1]));
    CUDA_CHECK(cudaEventSynchronize(g.ev[1]));
    return event_ms(g.ev[0], g.ev[1]) / reps;
}

/* ============================ result output ============================ */

static FILE *g_csv = NULL;
static double g_angle = 30.0;

static void csv_row(const char *section, const char *variant, int w, int h,
                    const char *block, Stage s, double cpu, double bytes,
                    Check c, double occ)
{
    if (!g_csv)
        return;
    double gb = bytes / 1e9;
    fprintf(g_csv,
            "%s,%s,%d,%d,%.1f,%s,%.4f,%.4f,%.4f,%.4f,%.3f,%.2f,%.2f,"
            "%.2f,%.2f,%.2f,%zu,%d,%.3f\n",
            section, variant, w, h, g_angle, block, s.h2d, s.ker, s.d2h,
            s.tot, cpu, s.ker > 0 ? cpu / s.ker : 0,
            s.tot > 0 ? cpu / s.tot : 0, s.h2d > 0 ? gb / (s.h2d / 1e3) : 0,
            s.d2h > 0 ? gb / (s.d2h / 1e3) : 0,
            s.ker > 0 ? 2 * gb / (s.ker / 1e3) : 0, c.mismatch, c.max_diff,
            occ);
    fflush(g_csv);
}

static void print_row(const char *name, Stage s, double cpu, Check c)
{
    printf("%-28s %8.3f %9.3f %8.3f %9.3f %9.1fx %8.1fx %10zu %4d\n", name,
           s.h2d, s.ker, s.d2h, s.tot, cpu / s.ker, cpu / s.tot, c.mismatch,
           c.max_diff);
}

static void print_device(void)
{
    cudaDeviceProp p;
    CUDA_CHECK(cudaGetDeviceProperties(&p, 0));
    int mem_khz = 0, bus_bits = 0;
    // Attributes instead of the deprecated cudaDeviceProp clock fields.
    CUDA_CHECK(cudaDeviceGetAttribute(&mem_khz, cudaDevAttrMemoryClockRate,
                                      0));
    CUDA_CHECK(cudaDeviceGetAttribute(&bus_bits,
                                      cudaDevAttrGlobalMemoryBusWidth, 0));
    // x2 because GDDR/HBM move data on both clock edges.
    double peak = 2.0 * mem_khz * 1e3 * (bus_bits / 8.0) / 1e9;
    printf("GPU: %s, compute %d.%d, %d SMs, %.1f GB, warp %d\n", p.name,
           p.major, p.minor, p.multiProcessorCount,
           p.totalGlobalMem / 1073741824.0, p.warpSize);
    printf("     max %d threads/block, %d threads/SM, %d-bit bus, "
           "peak DRAM ~%.0f GB/s\n",
           p.maxThreadsPerBlock, p.maxThreadsPerMultiProcessor, bus_bits,
           peak);
    printf("     copy engines: %d, concurrent kernels: %s\n\n",
           p.asyncEngineCount, p.concurrentKernels ? "yes" : "no");
}

/* =============================== sections ============================== */

static const char *HDR =
    "variant                       H2D(ms) kernel(ms)  D2H(ms)  total(ms)"
    "  kern-SU    e2e-SU  mismatch  max\n";

// v1 to v4 and v6: full pipelines against the matching CPU baseline.
static void section_main(Gpu &g, const u8 *img, const u8 *ref_nn,
                         const u8 *ref_bl, double cpu_nn, double cpu_bl,
                         int reps, const char *save)
{
    size_t n = g.bytes;
    char blk[32], blk1d[32];
    snprintf(blk, sizeof(blk), "%ux%u", g.block.x, g.block.y);
    snprintf(blk1d, sizeof(blk1d), "%u(1D)", g.block.x * g.block.y);
    u8 *pin_in, *pin_out;
    // Pinned (page-locked) buffers: the DMA engine can read them directly.
    CUDA_CHECK(cudaMallocHost((void **)&pin_in, n));
    CUDA_CHECK(cudaMallocHost((void **)&pin_out, n));
    memcpy(pin_in, img, n);
    // Pageable buffers from malloc; the driver must stage these first.
    u8 *pg_in = (u8 *)malloc(n), *pg_out = (u8 *)malloc(n);
    memcpy(pg_in, img, n);
    memset(pg_out, 0, n); // touch every page so page faults are not timed

    printf("== Main pipelines: %dx%d, %.1f deg, block %s, %.1f MB ==\n",
           g.w, g.h, g_angle, blk, n / 1e6);
    printf("CPU v0 nearest %.2f ms, bilinear %.2f ms (one core)\n", cpu_nn,
           cpu_bl);
    printf("%s", HDR);

    struct V {
        const char *name;
        Kind k;
        int pinned;
        int bl;
    } vs[] = {
        {"v1_nn_1d_pinned", K_NN_1D, 1, 0},
        {"v2_nn_2d_pinned", K_NN_2D, 1, 0},
        {"v3_bilinear_2d_pinned", K_BL_2D, 1, 1},
        {"v4_nn_2d_pageable", K_NN_2D, 0, 0},
        {"v4_bilinear_2d_pageable", K_BL_2D, 0, 1},
        {"v6_texture_bilinear_pinned", K_TEX, 1, 1},
    };
    for (size_t i = 0; i < sizeof(vs) / sizeof(vs[0]); i++) {
        if (vs[i].k == K_TEX && !g.tex_ok) {
            printf("%-28s skipped: image too big for a 2D texture\n",
                   vs[i].name);
            continue;
        }
        const u8 *in = vs[i].pinned ? pin_in : pg_in;
        u8 *out = vs[i].pinned ? pin_out : pg_out;
        memset(out, 0, n);
        CUDA_CHECK(cudaMemset(g.d_dst, 0, n)); // no stale result can pass
        Stage s = run_pipeline(g, vs[i].k, in, out, reps);
        double cpu = vs[i].bl ? cpu_bl : cpu_nn;
        Check c = compare(out, vs[i].bl ? ref_bl : ref_nn, n);
        print_row(vs[i].name, s, cpu, c);
        csv_row("main", vs[i].name, g.w, g.h,
                vs[i].k == K_NN_1D ? blk1d : blk, s, cpu,
                (double)n, c, 0);
        if (save && vs[i].k == K_BL_2D && vs[i].pinned) {
            char path[512];
            snprintf(path, sizeof(path), "%s_v3_bilinear.ppm", save);
            write_ppm(path, out, g.w, g.h);
        }
        if (save && vs[i].k == K_NN_2D && vs[i].pinned) {
            char path[512];
            snprintf(path, sizeof(path), "%s_v2_nearest.ppm", save);
            write_ppm(path, out, g.w, g.h);
        }
    }
    printf("kern-SU = CPU time / kernel time, e2e-SU = CPU time / "
           "(H2D + kernel + D2H)\n");
    printf("v6 is checked against v3's CPU bilinear; small max diff is "
           "expected (8-bit weights)\n\n");
    CUDA_CHECK(cudaFreeHost(pin_in));
    CUDA_CHECK(cudaFreeHost(pin_out));
    free(pg_in);
    free(pg_out);
}

// Block shape sweep: same work, different <<<grid, block>>> shapes.
static void section_blocks(Gpu &g, const u8 *img, const u8 *ref_nn,
                           const u8 *ref_bl, double cpu_nn, double cpu_bl,
                           int reps)
{
    const int shapes[][2] = {{32, 1}, {64, 1},  {128, 1}, {256, 1},
                             {8, 4},  {8, 8},   {16, 8},  {32, 4},
                             {16, 16}, {32, 8}, {64, 4},  {32, 16},
                             {32, 32}};
    cudaDeviceProp p;
    CUDA_CHECK(cudaGetDeviceProperties(&p, 0));
    u8 *out = (u8 *)malloc(g.bytes);
    CUDA_CHECK(cudaMemcpy(g.d_src, img, g.bytes, cudaMemcpyHostToDevice));
    printf("== Block size sweep (kernel only, input already on GPU) ==\n");
    printf("block    threads  occupancy  nearest(ms)  bilinear(ms)  "
           "checks\n");
    for (size_t i = 0; i < sizeof(shapes) / sizeof(shapes[0]); i++) {
        dim3 b(shapes[i][0], shapes[i][1]);
        int threads = b.x * b.y;
        char name[32];
        snprintf(name, sizeof(name), "%ux%u", b.x, b.y);
        double res[2];
        Check chk[2];
        double occ[2];
        for (int bl = 0; bl < 2; bl++) {
            Kind k = bl ? K_BL_2D : K_NN_2D;
            int per_sm = 0;
            // Resident blocks per SM, limited by registers, block slots
            // and threads per SM. Occupancy = resident warps / max warps.
            CUDA_CHECK(cudaOccupancyMaxActiveBlocksPerMultiprocessor(
                &per_sm, bl ? (const void *)rotate_bl_2d
                            : (const void *)rotate_nn_2d,
                threads, 0));
            occ[bl] = (double)per_sm * threads /
                      p.maxThreadsPerMultiProcessor;
            CUDA_CHECK(cudaMemset(g.d_dst, 0, g.bytes));
            res[bl] = time_kernel(g, k, b, reps);
            CUDA_CHECK(cudaMemcpy(out, g.d_dst, g.bytes,
                                  cudaMemcpyDeviceToHost));
            chk[bl] = compare(out, bl ? ref_bl : ref_nn, g.bytes);
            Stage s = {0, res[bl], 0, 0};
            csv_row("blocks", bl ? "v3_bilinear_2d" : "v2_nn_2d", g.w, g.h,
                    name, s, bl ? cpu_bl : cpu_nn, (double)g.bytes,
                    chk[bl], occ[bl]);
        }
        printf("%-8s %7d  %8.0f%%  %11.3f  %12.3f  %s\n", name, threads,
               100 * occ[0], res[0], res[1],
               (chk[0].mismatch || chk[1].mismatch) ? "MISMATCH" : "ok");
    }
    printf("\n");
    free(out);
}

// Row range of the source that destination rows [r0, r1) can touch.
// The mapping is linear, so the extremes are at the band's corners.
static void src_rows(const Gpu &g, int r0, int r1, int *lo, int *hi)
{
    float mn = 1e30f, mx = -1e30f;
    int xs[2] = {0, g.w - 1}, ys[2] = {r0, r1 - 1};
    for (int a = 0; a < 2; a++)
        for (int b = 0; b < 2; b++) {
            float sx, sy;
            src_coord(g.r, xs[a], ys[b], &sx, &sy);
            mn = fminf(mn, sy);
            mx = fmaxf(mx, sy);
        }
    *lo = (int)floorf(mn) - 1; // -1 and +2 cover rounding and the
    *hi = (int)floorf(mx) + 2; // extra bilinear neighbour row
}

// v5a: one image, split into row chunks over several streams.
// Each output chunk may need source rows from anywhere, so a kernel only
// waits for the H2D chunks that cover its source rows. At small angles
// that is a thin band and the copies overlap well; at large angles most
// of the image is needed first and the overlap mostly comes from D2H.
// v5b: a batch of whole images, one per stream, which always overlaps.
static void section_streams(Gpu &g, const u8 *img, const u8 *ref_bl,
                            double cpu_bl, int nstreams, int nchunks,
                            int batch, int reps)
{
    size_t n = g.bytes, row = (size_t)g.w * 3;
    char blk[32];
    snprintf(blk, sizeof(blk), "%ux%u", g.block.x, g.block.y);
    u8 *pin_in, *pin_out;
    // Async copies only overlap if the host memory is pinned.
    CUDA_CHECK(cudaMallocHost((void **)&pin_in, n));
    CUDA_CHECK(cudaMallocHost((void **)&pin_out, n));
    memcpy(pin_in, img, n);

    // nstreams kernel streams plus one extra stream just for H2D copies.
    cudaStream_t *st =
        (cudaStream_t *)malloc((nstreams + 1) * sizeof(*st));
    for (int i = 0; i <= nstreams; i++)
        CUDA_CHECK(cudaStreamCreate(&st[i]));
    cudaStream_t up = st[nstreams];
    cudaEvent_t *copied = (cudaEvent_t *)malloc(nchunks * sizeof(*copied));
    for (int i = 0; i < nchunks; i++)
        CUDA_CHECK(cudaEventCreateWithFlags(&copied[i],
                                            cudaEventDisableTiming));
    int rows = (g.h + nchunks - 1) / nchunks;

    printf("== Streams: %d streams, %d chunks, bilinear, %.1f deg ==\n",
           nstreams, nchunks, g_angle);

    // Serial reference: the same bilinear pipeline with no overlap.
    Stage ser = run_pipeline(g, K_BL_2D, pin_in, pin_out, reps);

    double tot = 0;
    for (int it = 0; it <= reps; it++) {
        memset(pin_out, 0, n);
        // Events on the legacy default stream wait for all other streams.
        CUDA_CHECK(cudaEventRecord(g.ev[0], 0));
        for (int c = 0; c < nchunks; c++) {
            int r0 = c * rows, r1 = r0 + rows < g.h ? r0 + rows : g.h;
            if (r0 >= r1)
                break;
            // All H2D chunks go in order on one stream, so chunk c being
            // done means every chunk before it is done too.
            CUDA_CHECK(cudaMemcpyAsync(g.d_src + r0 * row, pin_in + r0 * row,
                                       (r1 - r0) * row,
                                       cudaMemcpyHostToDevice, up));
            CUDA_CHECK(cudaEventRecord(copied[c], up));
        }
        for (int c = 0; c < nchunks; c++) {
            int r0 = c * rows, r1 = r0 + rows < g.h ? r0 + rows : g.h;
            if (r0 >= r1)
                break;
            cudaStream_t s = st[c % nstreams];
            int lo, hi;
            src_rows(g, r0, r1, &lo, &hi);
            if (hi >= 0 && lo < g.h) {
                int last = (hi < g.h ? hi : g.h - 1) / rows;
                // Wait on the GPU, not the CPU: the host keeps queueing.
                CUDA_CHECK(cudaStreamWaitEvent(s, copied[last], 0));
            }
            launch(g, K_BL_2D, g.block, s, r0, r1);
            CUDA_CHECK(cudaMemcpyAsync(pin_out + r0 * row, g.d_dst + r0 * row,
                                       (r1 - r0) * row,
                                       cudaMemcpyDeviceToHost, s));
        }
        CUDA_CHECK(cudaEventRecord(g.ev[1], 0));
        CUDA_CHECK(cudaEventSynchronize(g.ev[1]));
        if (it > 0)
            tot += event_ms(g.ev[0], g.ev[1]);
    }
    tot /= reps;
    Check c = compare(pin_out, ref_bl, n);
    Stage s5a = {0, 0, 0, tot};
    printf("v5a one image serial   %9.3f ms\n", ser.tot);
    printf("v5a one image streams  %9.3f ms  (%.2fx vs serial)  "
           "mismatch %zu\n",
           tot, ser.tot / tot, c.mismatch);
    csv_row("streams", "v5a_serial", g.w, g.h, blk, ser, cpu_bl, (double)n,
            c, 0);
    csv_row("streams", "v5a_chunked", g.w, g.h, blk, s5a, cpu_bl,
            (double)n, c, 0);

    // v5b: batch of images. One device buffer pair per stream is enough,
    // because work inside one stream runs in order.
    u8 *b_in, *b_out;
    CUDA_CHECK(cudaMallocHost((void **)&b_in, n * batch));
    CUDA_CHECK(cudaMallocHost((void **)&b_out, n * batch));
    for (int i = 0; i < batch; i++)
        memcpy(b_in + i * n, img, n);
    u8 **d_in = (u8 **)malloc(nstreams * sizeof(u8 *));
    u8 **d_out = (u8 **)malloc(nstreams * sizeof(u8 *));
    for (int i = 0; i < nstreams; i++) {
        CUDA_CHECK(cudaMalloc((void **)&d_in[i], n));
        CUDA_CHECK(cudaMalloc((void **)&d_out[i], n));
    }
    Gpu gs = g; // copy of the launch settings, buffers swapped per stream
    double t_ser = 0, t_str = 0;
    for (int it = 0; it <= reps; it++) {
        // Serial batch: blocking copies, nothing overlaps.
        CUDA_CHECK(cudaEventRecord(g.ev[0], 0));
        for (int i = 0; i < batch; i++) {
            gs.d_src = d_in[0];
            gs.d_dst = d_out[0];
            CUDA_CHECK(cudaMemcpy(gs.d_src, b_in + i * n, n,
                                  cudaMemcpyHostToDevice));
            launch(gs, K_BL_2D, g.block, 0, 0, g.h);
            CUDA_CHECK(cudaMemcpy(b_out + i * n, gs.d_dst, n,
                                  cudaMemcpyDeviceToHost));
        }
        CUDA_CHECK(cudaEventRecord(g.ev[1], 0));
        CUDA_CHECK(cudaEventSynchronize(g.ev[1]));
        memset(b_out, 0, n * batch);
        // Streamed batch: image i goes to stream i % nstreams, so one
        // image's H2D can run beside another's kernel and a third's D2H.
        CUDA_CHECK(cudaEventRecord(g.ev[2], 0));
        for (int i = 0; i < batch; i++) {
            int k = i % nstreams;
            gs.d_src = d_in[k];
            gs.d_dst = d_out[k];
            CUDA_CHECK(cudaMemcpyAsync(gs.d_src, b_in + i * n, n,
                                       cudaMemcpyHostToDevice, st[k]));
            launch(gs, K_BL_2D, g.block, st[k], 0, g.h);
            CUDA_CHECK(cudaMemcpyAsync(b_out + i * n, gs.d_dst, n,
                                       cudaMemcpyDeviceToHost, st[k]));
        }
        CUDA_CHECK(cudaEventRecord(g.ev[3], 0));
        CUDA_CHECK(cudaEventSynchronize(g.ev[3]));
        if (it > 0) {
            t_ser += event_ms(g.ev[0], g.ev[1]);
            t_str += event_ms(g.ev[2], g.ev[3]);
        }
    }
    t_ser /= reps;
    t_str /= reps;
    Check cb = {0, 0};
    for (int i = 0; i < batch; i++) {
        Check ci = compare(b_out + i * n, ref_bl, n);
        cb.mismatch += ci.mismatch;
        if (ci.max_diff > cb.max_diff)
            cb.max_diff = ci.max_diff;
    }
    printf("v5b batch of %d serial  %9.3f ms  (%.3f ms/image)\n", batch,
           t_ser, t_ser / batch);
    printf("v5b batch of %d streams %9.3f ms  (%.3f ms/image, %.2fx)  "
           "mismatch %zu\n\n",
           batch, t_str, t_str / batch, t_ser / t_str, cb.mismatch);
    Stage sb1 = {0, 0, 0, t_ser / batch}, sb2 = {0, 0, 0, t_str / batch};
    csv_row("streams", "v5b_serial_per_image", g.w, g.h, blk, sb1, cpu_bl,
            (double)n, cb, 0);
    csv_row("streams", "v5b_streams_per_image", g.w, g.h, blk, sb2, cpu_bl,
            (double)n, cb, 0);

    for (int i = 0; i < nstreams; i++) {
        CUDA_CHECK(cudaFree(d_in[i]));
        CUDA_CHECK(cudaFree(d_out[i]));
        CUDA_CHECK(cudaStreamDestroy(st[i]));
    }
    CUDA_CHECK(cudaStreamDestroy(up));
    for (int i = 0; i < nchunks; i++)
        CUDA_CHECK(cudaEventDestroy(copied[i]));
    free(d_in);
    free(d_out);
    free(st);
    free(copied);
    CUDA_CHECK(cudaFreeHost(b_in));
    CUDA_CHECK(cudaFreeHost(b_out));
    CUDA_CHECK(cudaFreeHost(pin_in));
    CUDA_CHECK(cudaFreeHost(pin_out));
}

/* ================================= main ================================ */

int main(int argc, char **argv)
{
    int w = 7680, h = 4320, reps = 10, cpu_reps = 1;
    int bx = 16, by = 16, nstreams = 4, nchunks = 8, batch = 8;
    const char *in_path = NULL, *csv_path = NULL, *save = NULL;
    const char *mode = "all";
    for (int i = 1; i < argc; i += 2) { // options come in pairs
        const char *a = argv[i];
        const char *v = i + 1 < argc ? argv[i + 1] : NULL;
        if (!v) {
            fprintf(stderr, "missing value after %s\n", a);
            return 1;
        }
        if (!strcmp(a, "--w")) w = atoi(v);
        else if (!strcmp(a, "--h")) h = atoi(v);
        else if (!strcmp(a, "--angle")) g_angle = atof(v);
        else if (!strcmp(a, "--block")) sscanf(v, "%dx%d", &bx, &by);
        else if (!strcmp(a, "--reps")) reps = atoi(v);
        else if (!strcmp(a, "--cpu-reps")) cpu_reps = atoi(v);
        else if (!strcmp(a, "--streams")) nstreams = atoi(v);
        else if (!strcmp(a, "--chunks")) nchunks = atoi(v);
        else if (!strcmp(a, "--batch")) batch = atoi(v);
        else if (!strcmp(a, "--in")) in_path = v;
        else if (!strcmp(a, "--csv")) csv_path = v;
        else if (!strcmp(a, "--save")) save = v;
        else if (!strcmp(a, "--mode")) mode = v;
        else {
            fprintf(stderr, "unknown option %s\n", a);
            return 1;
        }
    }
    if (reps < 1) reps = 1;
    if (cpu_reps < 1) cpu_reps = 1;

    u8 *img;
    if (in_path) {
        img = read_ppm(in_path, &w, &h);
        if (!img)
            return 1;
    } else {
        img = (u8 *)malloc((size_t)w * h * 3);
        make_test_image(img, w, h);
    }
    if (save) {
        char path[512];
        snprintf(path, sizeof(path), "%s_input.ppm", save);
        write_ppm(path, img, w, h);
    }

    if (csv_path) {
        FILE *probe = fopen(csv_path, "r");
        int fresh = probe == NULL;
        if (probe)
            fclose(probe);
        g_csv = fopen(csv_path, "a"); // append so sweeps share one file
        if (g_csv && fresh)
            fprintf(g_csv, "section,variant,width,height,angle,block,"
                           "h2d_ms,kernel_ms,d2h_ms,total_ms,cpu_ms,"
                           "speedup_kernel,speedup_e2e,h2d_GBps,d2h_GBps,"
                           "kernel_GBps,mismatch,max_diff,occupancy\n");
    }

    CUDA_CHECK(cudaFree(0)); // create the CUDA context before any timing
    print_device();

    Gpu g;
    memset(&g, 0, sizeof(g));
    g.w = w;
    g.h = h;
    g.bytes = (size_t)w * h * 3;
    g.block = dim3(bx, by);
    double th = g_angle * M_PI / 180.0;
    g.r.c = (float)cos(th);
    g.r.s = (float)sin(th);
    // cos(90 deg) comes out as about 6e-17, not 0. Snap tiny values so
    // right-angle turns are exact pixel moves.
    if (fabsf(g.r.c) < 1e-7f) g.r.c = 0.0f;
    if (fabsf(g.r.s) < 1e-7f) g.r.s = 0.0f;
    g.r.cx = 0.5f * (w - 1);
    g.r.cy = 0.5f * (h - 1);

    CUDA_CHECK(cudaMalloc((void **)&g.d_src, g.bytes));
    CUDA_CHECK(cudaMalloc((void **)&g.d_dst, g.bytes));
    for (int i = 0; i < 4; i++)
        CUDA_CHECK(cudaEventCreate(&g.ev[i]));
    setup_texture(g);

    // v0: serial CPU baselines, also the reference answers for checking.
    u8 *ref_nn = (u8 *)malloc(g.bytes), *ref_bl = (u8 *)malloc(g.bytes);
    double t0 = now_ms();
    for (int i = 0; i < cpu_reps; i++)
        rotate_cpu(img, ref_nn, w, h, g.r, 0);
    double cpu_nn = (now_ms() - t0) / cpu_reps;
    t0 = now_ms();
    for (int i = 0; i < cpu_reps; i++)
        rotate_cpu(img, ref_bl, w, h, g.r, 1);
    double cpu_bl = (now_ms() - t0) / cpu_reps;
    Stage cs = {0, 0, 0, 0};
    Check none = {0, 0};
    cs.tot = cpu_nn;
    csv_row("main", "v0_cpu_nn", w, h, "-", cs, cpu_nn, (double)g.bytes,
            none, 0);
    cs.tot = cpu_bl;
    csv_row("main", "v0_cpu_bilinear", w, h, "-", cs, cpu_bl,
            (double)g.bytes, none, 0);

    int all = !strcmp(mode, "all");
    if (all || !strcmp(mode, "main"))
        section_main(g, img, ref_nn, ref_bl, cpu_nn, cpu_bl, reps, save);
    if (all || !strcmp(mode, "blocks"))
        section_blocks(g, img, ref_nn, ref_bl, cpu_nn, cpu_bl, reps);
    if (all || !strcmp(mode, "streams"))
        section_streams(g, img, ref_bl, cpu_bl, nstreams, nchunks, batch,
                        reps);

    if (g.tex_ok) {
        CUDA_CHECK(cudaDestroyTextureObject(g.tex));
        CUDA_CHECK(cudaFree(g.d_rgba));
    }
    for (int i = 0; i < 4; i++)
        CUDA_CHECK(cudaEventDestroy(g.ev[i]));
    CUDA_CHECK(cudaFree(g.d_src));
    CUDA_CHECK(cudaFree(g.d_dst));
    free(img);
    free(ref_nn);
    free(ref_bl);
    if (g_csv)
        fclose(g_csv);
    return 0;
}
