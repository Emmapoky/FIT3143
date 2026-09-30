# FIT3143 Applied #2 Assessment Report & Presentation Documentation
(Draft v1 as pasted by Erwyna into chat on 2026-09-30. Saved verbatim for the HD Panel. Source of draft: unknown, likely Gemini/ChatGPT per its own declaration log.)

Course: FIT3143 - Parallel Computing
Topic: GPU/NPU Architecture and Exponential Growth in AI Computing
Format: Formal Documentation & Presentation Deck Outline

## Section 1: Task 1 — Image Rotation with GPU Architecture

### 1.1 Host-to-Device Memory Transfer Mechanisms

In GPU-accelerated computing architectures, data transfer between system host memory (e.g., DDR5 SDRAM) and GPU device memory (e.g., GDDR6 or High Bandwidth Memory, HBM) occurs across the Peripheral Component Interconnect Express (PCIe) system bus.

```
+-----------------------------------------------------------------------+
|                              HOST (CPU)                               |
|  +-----------------------+               +-------------------------+  |
|  | Pageable Memory       | --(Sys Copy)->| Pinned Host Memory      |  |
|  | (Standard Host RAM)   |               | (cudaMallocHost)        |  |
|  +-----------------------+               +-------------------------+  |
+------------------------------------------------|----------------------+
                                                 | PCIe Bus (DMA Controller)
+------------------------------------------------|----------------------+
|                              DEVICE (GPU)      v                      |
|  +-----------------------------------------------------------------+  |
|  | Device Global Memory (GDDR6 / HBM)                              |  |
|  +-----------------------------------------------------------------+  |
+-----------------------------------------------------------------------+
```

Pageable Memory Transfers: By default, host memory allocated using standard C malloc() is pageable (virtual memory managed by the Operating System that can be swapped to disk). When calling cudaMemcpy(..., cudaMemcpyHostToDevice), the CUDA driver allocates an internal temporary page-locked (pinned) staging buffer, performs a synchronous CPU copy from pageable memory to pinned memory, and then transfers the bytes across PCIe to GPU global memory via Direct Memory Access (DMA). This intermediate copy introduces memory latency and limits bandwidth utilization.

Pinned (Page-Locked) Host Memory: Allocating host memory via cudaHostAlloc() or cudaMallocHost() locks physical RAM pages into place, preventing OS swapping. Pinned host memory allows the GPU DMA controller to read data directly from CPU RAM without intermediate staging, saturating PCIe bandwidth (e.g., PCIe 5.0 x16 yields up to 64 GB/s unidirectional). Pinned memory enables asynchronous data transfers via cudaMemcpyAsync(), allowing overlap of PCIe transfers with CPU execution or CUDA kernel execution in concurrent streams.

Unified Memory (cudaMallocManaged): Unified Memory establishes a managed, unified virtual address space accessible across CPU and GPU. The system automatically migrates data pages between host DDR5 RAM and device VRAM on demand via hardware page fault handlers across the PCIe bus. While simplifying code development, explicit pinned memory transfers remain preferred for time-critical, high-throughput image processing pipelines.

### 1.2 CUDA Programming Model & Execution Architecture

Host (CPU) vs. Device (GPU) Responsibilities
- Host Responsibilities: Manages program flow, initial memory allocation (cudaMalloc), host-to-device memory initialization (cudaMemcpy), kernel launch configuration, stream scheduling, and asynchronous completion synchronization.
- Device Responsibilities: Executes compute-heavy routines across thousands of parallel execution threads.

2D Coordinate Transformation Mathematics: Rotating a 2D Cartesian point (x, y) counterclockwise by angle θ around the origin uses the standard linear rotation matrix R:
[x'; y'] = [cosθ −sinθ; sinθ cosθ][x; y] = [x cosθ − y sinθ; x sinθ + y cosθ]
To prevent holes or missing pixel artifacts caused by discrete rounding in forward mapping, high-throughput image rotation routines perform inverse coordinate mapping: for every output pixel coordinate (x', y'), the kernel computes the corresponding input source location (x, y).

CUDA Kernel Implementation
```c
#include <cuda_runtime.h>
#include <math.h>

// CUDA Kernel performing inverse 2D image rotation
__global__ void rotateImageKernel(const unsigned char* __restrict__ srcImage,
                                 unsigned char* __restrict__ dstImage,
                                 int width, int height,
                                 float cosTheta, float sinTheta,
                                 int centerX, int centerY)
{
    // Compute global 2D target thread coordinates
    int x_dst = blockIdx.x * blockDim.x + threadIdx.x;
    int y_dst = blockIdx.y * blockDim.y + threadIdx.y;

    if (x_dst < width && y_dst < height) {
        // Shift target coordinate relative to rotation center
        float xc = (float)(x_dst - centerX);
        float yc = (float)(y_dst - centerY);

        // Apply inverse rotation matrix
        int x_src = __float2int_rn( xc * cosTheta + yc * sinTheta + (float)centerX );
        int y_src = __float2int_rn(-xc * sinTheta + yc * cosTheta + (float)centerY );

        int dstIdx = y_dst * width + x_dst;

        // Check source bounds
        if (x_src >= 0 && x_src < width && y_src >= 0 && y_src < height) {
            int srcIdx = y_src * width + x_src;
            dstImage[dstIdx] = srcImage[srcIdx];
        } else {
            dstImage[dstIdx] = 0; // Black background padding
        }
    }
}
```

Kernel Launch Configuration (<<<grid, block>>>): Kernel calls specify execution parameters using triple angle bracket syntax <<<dimGrid, dimBlock>>>:
- dimBlock: Defines thread allocation per block (e.g., dim3 dimBlock(16, 16) = 256 threads per block).
- dimGrid: Defines grid dimensions required to cover image resolution (e.g., dim3 dimGrid((width + 15)/16, (height + 15)/16)).

Hardware Thread Hierarchy & Speedup Drivers
- Logical Mapping: Grid → Thread Block → Thread.
- Hardware Execution Model: Threads within a block are grouped into warps of 32 threads. Warps execute concurrently on Streaming Multiprocessors (SMs) following the SIMT (Single Instruction, Multiple Threads) architecture.
- Speedup Analysis: On sequential CPUs, image rotation requires O(W × H) iterations. Modern GPUs containing thousands of CUDA cores process millions of pixel coordinates concurrently with O(1) algorithmic depth, achieving 20× to 100×+ speedups. Throughput is primarily bound by GDDR/HBM memory bandwidth rather than compute limits.

### 1.3 GPUDirect Storage (GDS) Evaluation

GPUDirect Storage (GDS) establishes a Direct Memory Access (DMA) path between local NVMe storage and GPU memory (GDDR/HBM), completely bypassing the Host CPU, CPU caches, and host RAM (DDR5).

```
[ Traditional Path ]  NVMe Storage  --> Host RAM (DDR5) --> CPU Cache --> GPU VRAM (GDDR6)
[ GPUDirect Path  ]  NVMe Storage  =====================================> GPU VRAM (GDDR6)
```

| Pipeline Factor | Beneficial Scenario for GDS | Non-Beneficial Scenario for GDS |
|---|---|---|
| Data Format | Massive, uncompressed multi-gigabyte RAW image files or frames. | Compressed formats (e.g., JPEG, PNG) requiring CPU decoding before GPU processing. |
| I/O Bottlenecks | Ultra-high-throughput image streams saturating PCIe lanes. | In-memory image streams already resident in host RAM. |
| CPU Overhead | High-throughput batch processing where CPU overhead creates a system bottleneck. | Small file workloads (<1 MB) where driver setup overhead offsets DMA savings. |

## Section 2: Task 2 — Ethical Implications of Scaling HPC for AI

### 2.1 Environmental and Energy Impact
- Energy Draw & Carbon Footprint: Modern enterprise AI hardware operates at high power profiles (e.g., 700W–1200W per accelerator board). Megawatt-scale AI clusters consume vast quantities of electricity during multi-week training runs. When powered by fossil-fuel-dependent grids, large-scale training generates significant CO2 emissions.
- Resource Depletion & Lifecycle Waste: Evaporative cooling systems consume millions of liters of fresh water daily in datacenter regions. Additionally, short GPU replacement cycles (18–36 months) drive growing electronic waste.

### 2.2 Data Governance, Security, and Algorithmic Fairness
- Unsanctioned Ingestion: Training datasets harvested at scale often ingest copyrighted content, personal identifying information (PII), and sensitive metadata without explicit user consent.
- Bias Amplification: Massive foundation models trained on uncurated web data risk perpetuating historical, racial, and socioeconomic biases at system scale.

### 2.3 Socio-Economic Impact & The "Compute Divide"
- Capital Concentration: Supercomputing centers costing hundreds of millions of dollars create an oligopoly where only a small number of well-funded technology firms can train frontier-class AI systems.
- Academic & Global South Exclusion: University labs and developing nations face resource constraints, leading to unequal access to cutting-edge research tools and AI development.

### 2.4 Sustainable & Equitable HPC Frameworks
- Green AI & Carbon-Aware Scheduling: Modern schedulers dynamically delay non-urgent training jobs to coincide with peak renewable energy availability (solar/wind grid peaks).
- Algorithmic Efficiency: Low-Rank Adaptation (LoRA), FP8/INT4 quantization, and structured pruning reduce computational overhead without significantly impacting model accuracy.
- Equitable Compute Initiatives: Public programs, such as the National Artificial Intelligence Research Resource (NAIRR), provide subsidized HPC access to academic and non-profit researchers.

## Section 3: Task 3 — Presentation Slide Deck & Script (7-Minute Target)

Timing Summary: Task 1 Coverage: 3 minutes · Task 2 Coverage: 4 minutes · Target Presentation Time: 7 minutes total

Slide 1: Title & Overview (0:00 - 0:30)
Visual: Assessment Title, Unit FIT3143, Team Member Names and Student IDs.
Speaker Script: "Good day everyone. Today we are presenting our analysis on GPU Acceleration for Image Rotation and the Ethical Implications of Scaling HPC for AI. We will cover CUDA memory architectures, execution mechanics, and GPUDirect Storage, followed by a discussion on energy sustainability and equitable access to high-performance computing."

Slide 2: GPU Memory Architecture & Data Transfers (0:30 - 1:30) [ETA: 1 min]
Visual: System Architecture Diagram comparing Pageable Memory, Pinned Host Memory (cudaMallocHost), DMA, and PCIe transfer paths.
Speaker Script: "To process high-resolution images on a GPU, data must move from host system RAM across the PCIe bus to GPU VRAM. Standard pageable memory requires a CPU copy into an internal staging buffer before DMA transfer. By using pinned memory via cudaMallocHost, we prevent OS page swapping, allowing direct DMA access over PCIe. This enables asynchronous streaming using cudaMemcpyAsync to overlap transfer latency with kernel execution."

Slide 3: CUDA Thread Hierarchy & Image Rotation Kernel (1:30 - 2:30) [ETA: 1 min]
Visual: Thread/Block/Grid Hierarchy Diagram, 2D Inverse Mapping Math Formula, and CUDA Kernel snippet.
Speaker Script: "Our image rotation routine maps each output pixel back to source coordinates using inverse transformation matrix math to prevent pixel gaps. The kernel is structured in 2D thread blocks (e.g., 16 × 16 threads) spanning a 2D block grid. Hardware schedules these threads in warps of 32 onto Streaming Multiprocessors. By processing millions of pixels concurrently, GPUs achieve 20× to 100× speedups compared to sequential CPU loops."

Slide 4: GPUDirect Storage (GDS) Analysis (2:30 - 3:00) [ETA: 30 sec]
Visual: GDS NVMe-to-VRAM Path Diagram and Suitability Comparison Table.
Speaker Script: "GPUDirect Storage creates a direct DMA link between high-speed NVMe drives and GPU memory, bypassing host CPU RAM and caches. GDS is highly effective for large uncompressed image pipelines streaming directly from storage arrays. However, if images require CPU decoding (like JPEGs) or are already present in host RAM, GDS provides limited benefits."

Slide 5: Environmental & Energy Impact of HPC (3:00 - 4:15) [ETA: 1 min 15 sec]
Visual: Power Consumption Charts, Carbon Emission Estimates, and Datacenter Water Usage Metrics.
Speaker Script: "Transitioning to Task 2: scaling modern HPC for AI poses significant energy and environmental challenges. Large-scale training clusters consume megawatts of continuous power, contributing to carbon emissions when reliant on fossil-fuel grids. Furthermore, evaporative cooling systems consume large quantities of fresh water, and rapid GPU refresh cycles contribute to e-waste."

Slide 6: Data Governance & The Compute Divide (4:15 - 5:30) [ETA: 1 min 15 sec]
Visual: Infographic illustrating the "Compute Divide" and data privacy/governance risks.
Speaker Script: "Scaling compute introduces data governance and accessibility issues. Massive datasets harvested from the web can embed privacy violations and perpetuate historical biases. Furthermore, because top-tier HPC clusters require substantial capital investment, control over frontier models is concentrated among a few tech firms, creating a compute divide that disadvantages academic institutions and developing nations."

Slide 7: Sustainable Frameworks & Green AI (5:30 - 6:45) [ETA: 1 min 15 sec]
Visual: Four Pillars: Carbon-Aware Scheduling, Quantization/LoRA, Dynamic Power Management, and Public Compute Grants (NAIRR).
Speaker Script: "To build a sustainable compute ecosystem, we recommend four key strategies: carbon-aware scheduling to run jobs when renewable energy peaks, algorithmic optimizations such as LoRA and FP8 quantization to reduce FLOP requirements, improved dynamic hardware power management, and public compute initiatives like NAIRR to ensure broader access."

Slide 8: Conclusion & Q&A Transition (6:45 - 7:00) [ETA: 15 sec]
Visual: Key Takeaway Summary Points and "Questions & Answers" Prompt.
Speaker Script: "In conclusion, GPU memory management and parallel CUDA kernel design unlock massive throughput for image processing, but scaling HPC infrastructure requires careful management of energy and access disparities. Thank you for your time, and we welcome your questions."

## Section 4: Generative AI Declaration & Submission Checklist

Moodle Submission Checklist
- [x] Task 3: Presentation Slides Document (PDF)
- [x] Task 1 & 2: Technical Design Documentation & Results
- [x] Source Code: CUDA Kernel implementation file (rotate_kernel.cu)
- [x] AI Declaration: Prompt and AI tools usage record (PDF)

Generative AI Prompt Record
```
GENAI DECLARATION LOG
Course: FIT3143 Applied #2 Assessment
Tools Used: Gemini, ChatGPT

Prompt 1: "Explain how CUDA handles host-to-device memory transfers over PCIe, focusing on pageable vs pinned memory and asynchronous streaming."
Prompt 2: "Derive 2D inverse image rotation transformation matrix math and convert it into a CUDA kernel using blockIdx and threadIdx."
Prompt 3: "Evaluate GPUDirect Storage (GDS) for high-resolution image processing pipelines and explain scenarios where GDS is beneficial vs non-beneficial."
Prompt 4: "Discuss ethical implications of scaling HPC supercomputing for AI, including carbon emissions, the compute divide, and Green AI scheduling frameworks."
```
