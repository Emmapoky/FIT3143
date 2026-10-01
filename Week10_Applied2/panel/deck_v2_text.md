# Canva deck text export (design DAHWprLb4Ls, 26 pages), 1 Oct 2026
Speaker notes per slide are in ../Taabish_script.txt and ../Erwyna_script.txt (same text as the Canva notes).
Images on slides are listed in [brackets] (they are real PNGs placed in Canva).

## 1. Title
Monash FIT3143 Parallel Computing, Applied #2
GPU Image Rotation and the Ethics of Scaling HPC for AI
FIT3143 Applied #2: GPU/NPU and Exponential Growth
Erwyna Soo Wen Xin (36555789) and Taabish Farooq Bhat (35473932)
esoo0013@student.monash.edu | ttaa0006@student.monash.edu
Task 1: GPU design | Task 2: Ethics of scaling HPC | Limitations and Q&A

## 2. Task 1: 33 Million Independent Pixels (Presenter: Taabish)
8K = 7680 x 4320 = 33,177,600 output pixels, each independent: a data-parallel workload.
Inverse mapping: one thread per output pixel, one writer, no holes.
[D4 inverse mapping diagram]

## 3. 1a. Host to Device and Back (Taabish)
- Pageable: extra staging copy
- Pinned: DMA straight over PCIe
- Pinned H2D measured: 12.3 GB/s; T4 GDDR6: 320 GB/s (NVIDIA, n.d.-d)
Unified Memory and zero-copy move data on demand (NVIDIA, 2026a, 2026b).
[D1 host-device round-trip diagram]

## 4. 1b. CUDA Model: host, device, <<<grid, block>>> (Taabish)
Host (CPU): allocate, copy, launch async, sync, check errors.
Device (GPU): SIMT threads in warps of 32.
Block 16 x 16 = 256 threads = 8 warps.
Grid 480 x 270 = 129,600 blocks for 8K.
[D2 grid/block/thread/warp hierarchy diagram]

## 5. 1b. Kernel and launch (from rotate_cuda.cu) (Taabish)
```
__global__ void rotate_nn_2d(const u8 *src, u8 *dst, int w, int h, Rot r)
{
    int x = blockIdx.x * blockDim.x + threadIdx.x;  // global column
    int y = blockIdx.y * blockDim.y + threadIdx.y;  // global row
    if (x >= w || y >= h) return;          // grid is rounded up
    float dx = x - r.cx, dy = y - r.cy;    // R^-1 = R^T, y flipped
    int ix = floorf(r.cx + r.c * dx - r.s * dy + 0.5f);
    int iy = floorf(r.cy + r.s * dx + r.c * dy + 0.5f);
    copy_or_black(src, dst, w, h, ix, iy, x, y);   // outside -> black
}
dim3 block(16, 16);                         // 256 threads = 8 warps
dim3 grid((w + block.x - 1) / block.x,      // ceil(7680/16) = 480
          (h + block.y - 1) / block.y);     // ceil(4320/16) = 270
// 129,600 blocks x 256 threads = 33,177,600 threads, one per pixel
rotate_nn_2d<<<grid, block>>>(d_src, d_dst, w, h, r);
CUDA_CHECK(cudaGetLastError());   // launch is async: check it here
```
Each thread owns one output pixel and reads its source with R transpose, so there are no holes and no write races. Simplified from the file in our submission.

## 6. 1b. Each Feature, Measured (Taabish)
v1 1D grid / v2 2D 16 x 16 blocks / v3 bilinear / v4 pageable memory / v5 streams / v6 texture object
[g1 chart: kernel-only vs end-to-end speed-up per variant]
Kernel 328x | End to end 29.6x | Copies 91% of the time
v2 (nearest, 16 x 16), 8K at 30 degrees, Tesla T4 vs one CPU core, mean of 10 runs.

## 7. 1c. GPUDirect Storage: helps the bulk pipeline, not one photo (Taabish)
[D3 GDS vs bounce-buffer diagram]
Where it helps: Bulk raw frames, or JPEGs decoded on the GPU (nvJPEG), when I/O is the bottleneck (Thompson & Newburn, 2019).
Where it does not help: One photo, JPEGs decoded on the CPU, or images already in RAM. Needs nvidia-fs and O_DIRECT, so we could not test it on Colab (NVIDIA, n.d.-a).

## 8. 2a. Energy: data centre demand keeps climbing (Erwyna)
[C2 IEA chart]
- 415 TWh in 2024
- 945 TWh by 2030, about 1,200 TWh by 2035
- GPU servers drive the growth (International Energy Agency [IEA], 2025)

## 9. 2a. Same chip, different grid (Erwyna)
[C1 Green500/TOP500 chart]
Frontier 55.0 vs LUMI 53.4 GFLOPS/W (TOP500, 2026)
LUMI: 100% hydropower, waste heat warms a town (LUMI consortium, 2023)
Carbon per FLOP depends on the grid, not only the chip

## 10. 2a. Malaysia Lens and a Myth Check (Erwyna)
Kajaani, Finland (LUMI): 100% hydropower (LUMI consortium, 2023); Cold climate cooling; Waste heat: up to 20% of town heating (LUMI consortium, 2023); Water: not a constraint
Johor, Malaysia: 79% fossil grid (Ember, 2026); 10 MW (2021) to 1.3 GW (2024) (Loo, 2025); Up to 31% of Peninsular demand by 2035 (The Sun, 2026); Water: Tier 1 and 2 approvals stopped (Lowyat.NET, 2025)
Myth check: AI emitting more CO2 than aviation is a 2030 projection (Giles, 2025). All data centres emit about 180 Mt CO2 now (IEA, 2025).

## 11. 2b. Data Governance, Security and Fairness (Erwyna)
Governance: 75% of AI supercomputer performance is in the US (Pilz et al., 2025). Gradients can leak training samples (Zhu et al., 2019), so data residency becomes a scheduler placement rule.
Security: dual-use: The same accelerators train a hospital or a military model, so the US limits chip exports, and since July 2025 Malaysia requires a permit for US AI chips (Bureau of Industry and Security, 2022; Ministry of Investment, Trade and Industry Malaysia [MITI], 2025).
Fairness: Malay is 0.086% of web text, and Tamil needs about 10x the tokens per word (Common Crawl, 2026; Ahuja et al., 2023).
[C5 data residency diagram: shards in two countries, gradients crossing a border]

## 12. 2c. The Compute Divide (Erwyna)
[C3 Epoch AI compute chart]
Over 90% of notable 2025 models: industry (Stanford HAI, 2026)
Frontier compute 5x a year; top academic model about 3,000x lower (Epoch AI, 2026)
Most academics: 1 to 8 GPUs (Khandelwal et al., 2025)
NCI Gadi: 776 GPUs, demand about 3x allocation (NCI, n.d.-a, n.d.-b)

## 13. 2d. Frameworks, and our SCALE checklist (Erwyna)
[C4 SCALE chart]
UNESCO, OECD and Malaysia's AIGE give values, not metrics (UNESCO, 2021; OECD, 2024; Ministry of Science, Technology and Innovation [MOSTI], 2024).
The EU gives numbers: 10^25 FLOP, PUE reporting above 500 kW (European Parliament & Council, 2024; European Commission, n.d.).
SCALE: each step is a Slurm setting and a reported number.

## 14. Limitations, Future Work and Takeaways (Erwyna)
Task 1: Limits: one CPU core, shared Colab VM, GDS not testable, RGB only, corners cropped. Future: nvJPEG + GDS + streams on a GDS server. Takeaway: rotation is memory bound, so PCIe sets the ceiling.
Task 2: Limits: energy figures mostly estimates (Epoch AI, 2026); carbon-aware gains 1 to 2% fleet-wide (Radovanovic et al., 2023). Future: joules per job across a strong-scaling sweep with Slurm. Takeaway: the carbon and access cost of a FLOP depends on where and for whom it runs.

## 15. Q&A (Erwyna)
Questions? Erwyna Soo Wen Xin and Taabish Farooq Bhat

## 16. APPENDIX A1. Where the time goes, 8K at 30 degrees
[g2 stage breakdown chart]
v2 nearest, pinned: H2D 8.06 ms, Kernel 1.55 ms, D2H 7.58 ms, Total 17.19 ms, CPU one core 509.3 ms, Mismatch 0 pixels

## 17. APPENDIX A2. Pinned vs pageable, and streams
[D5 streams timeline] + v5b streams code (cudaMallocHost, 4 streams, cudaMemcpyAsync, kernel in stream, cudaDeviceSynchronize)
Measured: pageable 4.6 GB/s vs pinned 12.3 GB/s. Streams: 1.8x on a batch of 8 images, 1.36x on one image.

## 18. APPENDIX A3. Block sweep and image size sweep
[g4 block sweep] [g5 size sweep]
16 x 16 is among the fastest for nearest (1.45 ms); bilinear is fastest at 16 x 8. Speed-up grows with image size as the fixed launch cost is amortised.

## 19. APPENDIX A4. How we timed it
cudaEvent timing code (ev[0..3] around H2D, kernel, D2H; cudaEventSynchronize; cudaEventElapsedTime)
Warm-up run discarded, then the mean of 10. Built with --fmad=false so every GPU output matches the CPU byte for byte (mismatch = 0). The CPU baseline uses clock_gettime.

## 20. APPENDIX A5. Why PCIe is the narrow pipe
PCIe 3.0 x16 (T4): 15.75 GB/s per direction (PCI-SIG, 2019); Measured pinned copy: 12.3 GB/s; T4 GDDR6: 320 GB/s (NVIDIA, n.d.-d)
Roofline: T4 balance is about 25 FLOP per byte (NVIDIA, n.d.-d). Rotation does a few FLOPs per byte moved, so the kernel is memory bound.
Implication for Task 1: PCIe is about 20x narrower than GDDR6, so copies are 91% of the time for one image (measured).
[g3 pinned vs pageable chart]

## 21. APPENDIX A6. GDS in practice
cuFileDriverOpen, cuFileHandleRegister (O_DIRECT), cuFileBufRegister, cuFileRead. CPU issues calls; data DMAs NVMe to GPU with no host bounce buffer (NVIDIA, n.d.-a, n.d.-b).
Requirements: nvidia-fs, O_DIRECT, aligned buffers, supported FS on NVMe/NVMe-oF; otherwise compatibility mode via bounce buffer, as on Colab (NVIDIA, n.d.-b, n.d.-c).

## 22. APPENDIX A7. SIMD vs SIMT vs NPU (Lindholm et al., 2008; Jouppi et al., 2017)

## 23. APPENDIX A8. References, Task 1 (APA 7) -> see ../references_APA7_slides.md
## 24-25. APPENDIX A9. References, Task 2 (APA 7), parts 1 and 2 -> see ../references_APA7_slides.md

## 26. APPENDIX A10. Generative AI declaration
Generative AI (Claude, Gemini, ChatGPT) was used during preparation, as allowed by the spec, for research, code drafting, diagrams, charts and wording. Every tool, prompt and use is listed in AI_Declaration.pdf with the full prompt records. We checked, ran and edited all outputs ourselves.
