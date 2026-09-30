# Task 1 Q&A Drill

**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu) and Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)

How to answer: **verdict first, then the mechanism, then our evidence** (a number from our own run or a line of our code). Use parallel computing terms, not everyday analogies. If you name a fix, name the problem it solves first. Replace every `[g#]` with the measured number from the Colab run before class.

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
It returns a `cudaError_t` status. The page-locked host address comes back through the pointer argument. Pinned pages cannot be swapped, so the copy engine can DMA directly from them. Pageable memory first needs a driver staging copy. Our v4 vs v2 shows the gap: `[g3: pinned vs pageable GB/s]`.

**6. Where does the time go, and what is the bottleneck?**
PCIe transfers, not the kernel. An 8K frame is 99.5 MB each way over PCIe 3.0 x16 on the T4 (about 12 GB/s achievable). The kernel only streams 199 MB through 320 GB/s GDDR6. Our stage breakdown shows the copies at `[g2: %]` of GPU time.

**7. Why is the kernel-only speed-up so much larger than the end-to-end speed-up?**
Amdahl's law. The copies are a serial fraction that more cores cannot shrink, so S_max = T_cpu / (T_H2D + T_D2H) no matter how fast the kernel is. Measured: kernel `[g1]`x vs end-to-end `[g1]`x.

**8. Is rotation compute-bound or memory-bound?**
Memory-bound. Nearest does about 2 flops per byte and bilinear about 7, far below the T4's ridge point of about 25 flops per byte (8.1 TFLOPS / 320 GB/s). Our v2 kernel reaches `[section 10: % of peak]` of peak DRAM bandwidth, so extra ALUs would not help.

**9. Why 16 x 16 blocks, and what is occupancy?**
Occupancy is resident warps per SM divided by the maximum (32 on a T4). It limits how well the scheduler hides memory latency. 256 threads (8 warps) is a multiple of 32, lets up to 4 blocks stay resident per SM, and a square tile keeps the gathered source reads compact in cache. The sweep shows `[g4: best shape and time]`, and blocks as small as 8 x 4 underfill the SM.

**10. What do the streams overlap, and why is the gain capped?**
H2D of one image, the kernel of another and D2H of a third, on separate copy engines over full-duplex PCIe. Rotation's kernel is short, so the best case is about max(H2D, D2H) per image, roughly 2x. Measured: batch `[g6]`x. For a single image, output bands need source rows from most of the frame at 30 degrees, so overlap is smaller there than at 5 degrees `[g6]`.

**11. Is GPUDirect Storage worth it for our routine?**
Only for bulk, I/O-bound pipelines. GDS DMAs from NVMe straight into GPU memory, which removes the CPU bounce buffer and CPU load; NVIDIA reports 2x to 8x bandwidth. But it does nothing when the image is already in RAM, when JPEG is decoded on the CPU (unless nvJPEG), or on unsupported file systems, which fall back to compatibility mode. The data still crosses PCIe once.

**12. How do you know the GPU output is correct, and how did you time it?**
Every GPU result is compared byte by byte with the CPU v0 output. We compiled with `--fmad=false` so both round the same way. The exact variants should show 0 mismatches (confirm in section 10 of the notebook: `[result]`); v6 differs by at most `[max_diff]` levels because of its 8-bit texture filter weights. Each stage is timed separately with a pair of `cudaEvent`s. We discard a warm-up run and take the mean of 10.

**Bonus (future work, have it ready):** OpenMP CPU baseline for a fairer comparison, NPP `nppiRotate` comparison, nvJPEG + GDS + streams pipeline, and an expand-to-fit canvas.
