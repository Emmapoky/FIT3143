# Task 1 Q&A Drill

**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu) and Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)

How to answer: **verdict first, then the mechanism, then our evidence** (a number from our own run or a line of our code). Use parallel computing terms, not everyday analogies. If you name a fix, name the problem it solves first.

---

**1. What does `blockIdx.x` mean, and how does a thread find its pixel?**
`blockIdx.x` is the index of the thread's block along x within the grid. It is not a thread number. The global column is `x = blockIdx.x * blockDim.x + threadIdx.x`, and y works the same way. Example: thread (9, 5) in block (4, 3) with 16 x 16 blocks owns pixel (73, 53).

**2. Why inverse mapping instead of applying R to each source pixel?**
Forward mapping leaves holes and lets two source pixels write the same destination, which is a write race. Inverse mapping gives each output pixel exactly one owning thread that computes R^T times its offset and gathers one value. So there are no races, no atomics, and no gaps. D4 shows the hit counts.

**3. What happens at the image borders?**
Two things. First, the grid is rounded up to whole blocks, so the guard `if (x >= w || y >= h) return;` stops the extra threads. Only border warps diverge. Second, if the source point falls outside the input, the pixel is written black (bilinear treats out-of-range neighbours as 0, the same as texture border mode).

**4. Does `cudaMemcpy` block the host?**
Yes, in our pipeline. From pinned memory, H2D is synchronous with respect to the host. For pageable H2D, the runtime does a stream sync before the copy. D2H returns only once the copy has completed. It also waits for our kernel because both are on stream 0. Only `cudaMemcpyAsync` with pinned memory returns early and can overlap.

**5. What does `cudaMallocHost` return, and why use it?**
It returns a `cudaError_t` status. The page-locked host address comes back through the pointer argument. Pinned pages cannot be swapped, so the copy engine can DMA directly from them. Pageable memory first needs a driver staging copy. Our v4 vs v2 shows the gap: pinned H2D 12.3 GB/s against pageable 4.6 GB/s, so 2.7x.

**6. Where does the time go, and what is the bottleneck?**
PCIe transfers, not the kernel. An 8K frame is 99.5 MB each way over PCIe 3.0 x16 on the T4 (about 12 GB/s achievable). The kernel only streams 199 MB through 320 GB/s GDDR6. Our stage breakdown shows the copies at 91% of GPU time (8.06 + 7.58 of 17.19 ms).

**7. Why is the kernel-only speed-up so much larger than the end-to-end speed-up?**
Amdahl's law. The copies are a serial fraction that more cores cannot shrink, so S_max = T_cpu / (T_H2D + T_D2H) no matter how fast the kernel is. Measured: kernel 328x vs end-to-end 29.6x, with copies 91% of the time.

**8. Is rotation compute-bound or memory-bound?**
Memory-bound. Nearest does about 2 flops per byte and bilinear about 7, far below the T4's ridge point of about 25 flops per byte (8.1 TFLOPS / 320 GB/s). Our v2 kernel reaches 128 GB/s, 40% of peak DRAM bandwidth, so extra ALUs would not help.

**9. Why 16 x 16 blocks, and what is occupancy?**
Occupancy is resident warps per SM divided by the maximum (32 on a T4). It limits how well the scheduler hides memory latency. 256 threads (8 warps) is a multiple of 32 and lets up to 4 blocks stay resident per SM. Careful: the shape is not why 2D beats 1D. 128 x 1 (1.44 ms) is as fast as 16 x 16 (1.45 ms) for nearest; v1 is slower (2.96 ms) because of its divide and modulo. Shape matters for bilinear (16 x 8 best at 2.83 ms, 64 x 4 at 4.00 ms). 32-thread blocks (8 x 4, 32 x 1) cap occupancy at 50%.

**10. What do the streams overlap, and why is the gain capped?**
H2D of one image, the kernel of another and D2H of a third, on separate copy engines over full-duplex PCIe. Rotation's kernel is short, so the best case is about max(H2D, D2H) per image, roughly 2x. Measured: batch of 8 gives 1.81x. For a single image, output bands need source rows from most of the frame at 30 degrees, so overlap is smaller there than at 5 degrees (one image: 1.36x at 30 degrees, 1.80x at 5 degrees, from results_streams_5deg.csv).

**11. Is GPUDirect Storage worth it for our routine?**
Only for bulk, I/O-bound pipelines. GDS DMAs from NVMe straight into GPU memory, which removes the CPU bounce buffer and CPU load; NVIDIA reports 2x to 8x bandwidth. But it does nothing when the image is already in RAM, when JPEG is decoded on the CPU (unless nvJPEG), or on unsupported file systems, which fall back to compatibility mode. The data still crosses PCIe once.

**12. How do you know the GPU output is correct, and how did you time it?**
Every GPU result is compared byte by byte with the CPU v0 output. We compiled with `--fmad=false` so both round the same way. v1 to v5 show 0 mismatches. v6 differs in 257,964 bytes (0.26% of the 99.5 MB output), each by at most 1 level, because of its 8-bit texture filter weights. Note the count is bytes, not pixels. Each stage is timed separately with a pair of `cudaEvent`s. We discard a warm-up run and take the mean of 10.

**Bonus (future work, have it ready):** OpenMP CPU baseline for a fairer comparison, NPP `nppiRotate` comparison, nvJPEG + GDS + streams pipeline, and an expand-to-fit canvas.

---

## More likely questions (panel, 1 Oct)

**13. Your estimate was 6.6x end to end, so why did you measure 29.6x?**
The GPU side matched the estimate (17.2 ms). The baseline changed: the Colab CPU core took 509 ms against 113 ms on the M3 Max. So the speed-up mostly measures how weak one core is. Against a CPU that saturates its DRAM bandwidth, the honest ceiling is about 4x (320 / 76.8 GB/s).

**14. What is the Amdahl bound here?**
With a zero-time kernel, 509.3 / (8.06 + 7.58) = 32.6x. We reach 29.6x, 91% of that bound. Faster GPUs cannot move it; only faster links (PCIe 5, NVLink), GPU-side decode or keeping data resident can.

**15. Why do your kernel times differ between slides (1.55 ms vs 1.45 ms)?**
They come from separate runs on a shared Colab GPU. The v2 kernel varied from 1.45 to 2.11 ms across runs, while the copies stayed at 8.06 ms every time. So the copy-bound end-to-end figure is stable, and kernel-only speed-ups carry about plus or minus 30%.

**16. How close is the streams result to ideal?**
The ideal per image is about max(H2D, D2H), roughly 8.1 ms. We got 10.14 ms per image (1.81x), about 80% of ideal. For one image, overlap depends on the angle: chunked streams gave 1.80x at 5 degrees but 1.36x at 30 degrees, because a band's source rows spread over more of the frame at larger angles.

**17. (Cross, asked of Erwyna) Why does pinned memory help?**
Pageable memory forces a staging copy into a driver pinned buffer before DMA. Pinned memory lets the copy engine DMA directly: 12.3 against 4.6 GB/s, 2.7x. It is also required for async copies in streams.

**18. (Cross, asked of Erwyna) Would GDS speed up one photo?**
No. GDS only removes the host bounce buffer on the storage to GPU path. One photo is decoded on the CPU and is already in RAM. It helps bulk raw or nvJPEG pipelines where I/O dominates; we could not test it on Colab (no nvidia-fs, no O_DIRECT).

**19. Isn't one CPU core an unfair baseline?**
Yes, and we measured the fairer one. `rotate_cpu_omp.c` splits the row loop across all cores with OpenMP (0 mismatches against one thread). On a 14-thread laptop (M3 Max) it does 8K nearest in 14.5 ms (8.9x over one thread, 63% parallel efficiency), which actually beats the T4's 17.2 ms end to end, because the GPU pays 15.6 ms of PCIe copies. So the GPU wins only when data stays on the GPU or images are batched. Colab's own all-core number is in `results/run_cpu_omp.txt` (Colab VMs usually have only 2 vCPUs).
