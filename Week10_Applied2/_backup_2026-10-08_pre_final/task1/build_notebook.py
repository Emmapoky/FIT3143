"""
build_notebook.py
Rebuilds Applied2_Task1_Colab.ipynb from rotate_cuda.cu so the %%writefile
cell always matches the submitted source. Run after editing the .cu:
    python3 tools/build_notebook.py
Erwyna Soo Wen Xin (36555789), Taabish Farooq Bhat (35473932)
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CU = open(os.path.join(ROOT, "rotate_cuda.cu")).read()

cells = []


def md(text):
    cells.append({"cell_type": "markdown", "metadata": {},
                  "source": text.strip("\n").splitlines(True)})


def code(text):
    cells.append({"cell_type": "code", "metadata": {},
                  "execution_count": None, "outputs": [],
                  "source": text.strip("\n").splitlines(True)})


md("""
# FIT3143 Applied #2, Task 1: Image rotation with CUDA

**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu) and
Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)

This notebook compiles and runs `rotate_cuda.cu` on a Colab GPU, sweeps
block sizes and image sizes, and draws the graphs used in our slides.

**Before running:** Runtime > Change runtime type > **T4 GPU**, then
Runtime > Run all. The whole notebook takes a few minutes.

The Week 9 class notebook used Numba (`@cuda.jit`). Here the main program
is CUDA C++ compiled with `nvcc`, so the `<<<grid, block>>>` launch syntax
from the spec appears literally in the code. A short Numba version is at
the end to tie back to Week 9.

| Variant | Feature shown |
|---|---|
| v0 | CPU serial baseline (nearest, bilinear), also the reference answer |
| v1 | naive 1D grid, nearest neighbour |
| v2 | 2D grid of 2D blocks (`blockIdx`, `threadIdx`, `blockDim`) |
| v3 | bilinear interpolation (quality vs cost) |
| v4 | pageable host memory, compared with pinned in v2/v3 |
| v5 | CUDA streams: (a) one image in row chunks, (b) a batch of images |
| v6 | texture object with hardware bilinear filtering |

Every stage (H2D, kernel, D2H, total) is timed separately with
`cudaEvent`s, and every GPU output is compared with the CPU output.
""")

md("## 1. Check the GPU and compiler")
code("""
!nvidia-smi
!nvcc --version
""")
code("""
import subprocess

# Compile for whatever GPU Colab gave us (T4 = compute capability 7.5).
try:
    cap = subprocess.run(
        ["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"],
        capture_output=True, text=True).stdout.split()[0]
    ARCH = "sm_" + cap.replace(".", "")
except Exception:
    ARCH = "sm_75"
print("compiling for", ARCH)
""")

md("""
## 2. Write the CUDA source

This cell is an exact copy of `rotate_cuda.cu` from our submission.
""")
code("%%writefile rotate_cuda.cu\n" + CU)

md("""
## 3. Compile

`--fmad=false` stops nvcc fusing `a*b+c` into one FMA instruction, so the
GPU rounds exactly like the CPU and the outputs can be compared byte for
byte. `-Xptxas -v` prints registers per thread for each kernel, which
limits occupancy.
""")
code("""
!nvcc -O3 -arch={ARCH} --fmad=false -Xptxas -v -o rotate_cuda rotate_cuda.cu
!ls -la rotate_cuda
""")

md("""
## 4. Main run: 8K image (7680 x 4320), 30 degrees

Runs every variant, the block sweep and the streams test. Output is saved
to `results/run_8k.txt` and `results/results_8k.csv`.

Columns: `kern-SU` = CPU time / kernel time, `e2e-SU` = CPU time /
(H2D + kernel + D2H). `mismatch` counts bytes that differ from the CPU.
""")
code("""
!mkdir -p results
!rm -f results/*.csv
!./rotate_cuda --angle 30 --csv results/results_8k.csv --save results/sample | tee results/run_8k.txt
""")

md("""
## 5. Look at the output

Nearest neighbour copies one source pixel, so edges come out jagged.
Bilinear blends four, so they are smooth. Zoomed crops make it clear.
""")
code("""
from PIL import Image
import matplotlib.pyplot as plt

imgs = [("input", "results/sample_input.ppm"),
        ("v2 nearest, +30 deg", "results/sample_v2_nearest.ppm"),
        ("v3 bilinear, +30 deg", "results/sample_v3_bilinear.ppm")]
fig, ax = plt.subplots(2, 3, figsize=(16, 7.5))
for k, (title, path) in enumerate(imgs):
    im = Image.open(path)
    ax[0, k].imshow(im.resize((im.width // 8, im.height // 8)))
    ax[0, k].set_title(title)
    ax[1, k].imshow(im.crop((3700, 1400, 3940, 1560)).resize((720, 480),
                                                             Image.NEAREST))
    ax[1, k].set_title(title + " (zoom)")
for a in ax.flat:
    a.axis("off")
plt.tight_layout()
plt.savefig("results/sample_output.png", dpi=110)
plt.show()
""")

md("""
## 6. Image size sweep

Same pipelines from 360p to 16K. Small images cannot fill the GPU and pay
fixed launch and transfer latency, so speed-up grows with size.
""")
code("""
sizes = [(640, 360), (1280, 720), (1920, 1080), (3840, 2160),
         (7680, 4320), (15360, 8640)]
for w, h in sizes:
    print(f"--- {w} x {h} ---")
    !./rotate_cuda --w {w} --h {h} --mode main --reps 5 --csv results/results_sizes.csv | grep -E "v[0-9]|CPU"
""")

md("""
## 7. Streams at a small angle

At 30 degrees each output band needs source rows from most of the image,
so the chunked single-image version (v5a) must wait for most of the H2D
copy. At 5 degrees each band needs a thin strip, so overlap is better.
""")
code("""
!./rotate_cuda --mode streams --angle 5 --csv results/results_streams_5deg.csv | tee results/run_streams_5deg.txt
""")

md("## 8. Tables")
code("""
import pandas as pd

pd.set_option("display.width", 200)
main = pd.read_csv("results/results_8k.csv")
sizes_df = pd.read_csv("results/results_sizes.csv")
st5 = pd.read_csv("results/results_streams_5deg.csv")
cols = ["variant", "block", "h2d_ms", "kernel_ms", "d2h_ms", "total_ms",
        "cpu_ms", "speedup_kernel", "speedup_e2e", "mismatch", "max_diff"]
print("8K pipelines")
display(main[main.section == "main"][cols])
print("Block sweep")
display(main[main.section == "blocks"][["variant", "block", "kernel_ms",
                                        "occupancy", "kernel_GBps",
                                        "mismatch"]])
print("Streams")
display(pd.concat([main[main.section == "streams"],
                   st5[st5.section == "streams"]])[
    ["variant", "angle", "total_ms", "mismatch"]])
""")

md("## 9. Graphs (saved into `results/` for the slides)")
code("""
import re
import numpy as np
import matplotlib.pyplot as plt

H2D_C, K_C, D2H_C, CPU_C = "#D9820B", "#2E8B57", "#2F6DB5", "#7B8794"
plt.rcParams.update({"font.size": 13, "axes.spines.top": False,
                     "axes.spines.right": False})

gpu = main[(main.section == "main") & ~main.variant.str.startswith("v0")]
labels = [v.replace("_pinned", "\\n(pinned)").replace("_pageable",
          "\\n(pageable)") for v in gpu.variant]

# (a) speed-up over the matching CPU baseline
x = np.arange(len(gpu))
fig, ax = plt.subplots(figsize=(13, 5.5))
ax.bar(x - 0.2, gpu.speedup_kernel, 0.4, color=K_C, label="kernel only")
ax.bar(x + 0.2, gpu.speedup_e2e, 0.4, color=D2H_C,
       label="end to end (H2D + kernel + D2H)")
for i, (a, b) in enumerate(zip(gpu.speedup_kernel, gpu.speedup_e2e)):
    ax.text(i - 0.2, a, f"{a:.0f}x", ha="center", va="bottom", fontsize=11)
    ax.text(i + 0.2, b, f"{b:.1f}x", ha="center", va="bottom", fontsize=11)
ax.set_yscale("log")
ax.set_xticks(x, labels, fontsize=10.5)
ax.set_ylabel("speed-up vs one CPU core (log)")
ax.set_title("8K rotation: kernel-only vs end-to-end speed-up")
ax.legend()
plt.tight_layout()
plt.savefig("results/g1_speedup.png", dpi=130)
plt.show()

# (b) where the GPU time goes
fig, ax = plt.subplots(figsize=(13, 5.5))
y = np.arange(len(gpu))
ax.barh(y, gpu.h2d_ms, color=H2D_C, label="H2D copy")
ax.barh(y, gpu.kernel_ms, left=gpu.h2d_ms, color=K_C, label="kernel")
ax.barh(y, gpu.d2h_ms, left=gpu.h2d_ms + gpu.kernel_ms, color=D2H_C,
        label="D2H copy")
for i, (t, k) in enumerate(zip(gpu.total_ms, gpu.kernel_ms)):
    ax.text(t, i, f"  {t:.1f} ms (kernel {100 * k / t:.0f}%)",
            va="center", fontsize=11)
ax.set_yticks(y, labels, fontsize=10.5)
ax.invert_yaxis()
ax.set_xlabel("time per 8K image (ms)")
ax.set_title("Stage breakdown per 8K image (pinned vs pageable)")
ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.13))
plt.tight_layout()
plt.savefig("results/g2_stage_breakdown.png", dpi=130)
plt.show()

# (c) pinned vs pageable transfer bandwidth
bw = main[main.variant.isin(["v2_nn_2d_pinned", "v4_nn_2d_pageable"])]
fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(2)
ax.bar(x - 0.2, bw.h2d_GBps, 0.4, color=H2D_C, label="H2D")
ax.bar(x + 0.2, bw.d2h_GBps, 0.4, color=D2H_C, label="D2H")
for i, (a, b) in enumerate(zip(bw.h2d_GBps, bw.d2h_GBps)):
    ax.text(i - 0.2, a, f"{a:.1f}", ha="center", va="bottom")
    ax.text(i + 0.2, b, f"{b:.1f}", ha="center", va="bottom")
ax.axhline(15.75, ls="--", color=CPU_C)
ax.text(1.45, 15.9, "PCIe 3.0 x16 peak, one direction", ha="right",
        color=CPU_C, fontsize=11)
ax.set_xticks(x, ["pinned\\n(cudaMallocHost)", "pageable\\n(malloc)"])
ax.set_ylabel("GB/s")
ax.set_title("Host memory type vs copy bandwidth (99.5 MB image)")
ax.legend()
plt.tight_layout()
plt.savefig("results/g3_pinned_vs_pageable.png", dpi=130)
plt.show()

# (d) block size sweep
blk = main[main.section == "blocks"]
nn = blk[blk.variant == "v2_nn_2d"].reset_index(drop=True)
bl = blk[blk.variant == "v3_bilinear_2d"].reset_index(drop=True)
fig, ax = plt.subplots(figsize=(13, 5.5))
x = np.arange(len(nn))
ax.bar(x - 0.2, nn.kernel_ms, 0.4, color=K_C, label="nearest (v2)")
ax.bar(x + 0.2, bl.kernel_ms, 0.4, color=D2H_C, label="bilinear (v3)")
ax.set_xticks(x, nn.block, rotation=30)
ax.set_xlabel("block shape (threads x by y)")
ax.set_ylabel("kernel time (ms)")
ax2 = ax.twinx()
ax2.plot(x, 100 * nn.occupancy, "o--", color=H2D_C,
         label="theoretical occupancy (v2)")
ax2.set_ylim(0, 110)
ax2.set_ylabel("occupancy (%)")
ax.set_title("Block shape sweep, 8K kernel only")
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="upper center")
plt.tight_layout()
plt.savefig("results/g4_block_sweep.png", dpi=130)
plt.show()

# (e) image size sweep
sz = sizes_df[sizes_df.section == "main"].copy()
sz["mpix"] = sz.width * sz.height / 1e6
fig, ax = plt.subplots(figsize=(11, 5.5))
for var, col in [("v2_nn_2d_pinned", K_C), ("v3_bilinear_2d_pinned",
                                             D2H_C)]:
    d = sz[sz.variant == var]
    ax.plot(d.mpix, d.speedup_kernel, "o-", color=col,
            label=var.split("_pinned")[0] + " kernel only")
    ax.plot(d.mpix, d.speedup_e2e, "s--", color=col,
            label=var.split("_pinned")[0] + " end to end")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("image size (megapixels, log)")
ax.set_ylabel("speed-up vs one CPU core (log)")
ax.set_title("Speed-up vs image size")
ax.legend(fontsize=11)
plt.tight_layout()
plt.savefig("results/g5_size_sweep.png", dpi=130)
plt.show()

# (f) streams
allst = pd.concat([main[main.section == "streams"],
                   st5[st5.section == "streams"]])
rows = []
for ang in sorted(allst.angle.unique()):
    d = allst[allst.angle == ang].set_index("variant").total_ms
    rows.append((f"one image\\n{ang:.0f} deg", d["v5a_serial"],
                 d["v5a_chunked"]))
d = main[main.section == "streams"].set_index("variant").total_ms
rows.append(("batch, per image\\n30 deg", d["v5b_serial_per_image"],
             d["v5b_streams_per_image"]))
fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(rows))
ax.bar(x - 0.2, [r[1] for r in rows], 0.4, color=CPU_C,
       label="serial (default stream)")
ax.bar(x + 0.2, [r[2] for r in rows], 0.4, color=K_C,
       label="4 CUDA streams")
for i, r in enumerate(rows):
    ax.text(i + 0.2, r[2], f"{r[1] / r[2]:.2f}x", ha="center",
            va="bottom")
ax.set_xticks(x, [r[0] for r in rows])
ax.set_ylabel("ms per 8K image (bilinear)")
ax.set_title("Overlapping copies and compute with streams")
ax.legend()
plt.tight_layout()
plt.savefig("results/g6_streams.png", dpi=130)
plt.show()
""")

md("""
## 10. Numbers for the slides

Pulled straight from the CSVs so the slides quote measured values.
""")
code("""
run = open("results/run_8k.txt").read()
peak = re.search(r"peak DRAM ~(\\d+) GB/s", run)
peak = float(peak.group(1)) if peak else float("nan")
gpu_name = re.search(r"GPU: ([^,]+)", run).group(1)

r = main.set_index("variant")
cpu_nn = r.loc["v0_cpu_nn", "cpu_ms"]
cpu_bl = r.loc["v0_cpu_bilinear", "cpu_ms"]
v2, v3 = r.loc["v2_nn_2d_pinned"], r.loc["v3_bilinear_2d_pinned"]
v4 = r.loc["v4_nn_2d_pageable"]
copy_share = (v2.h2d_ms + v2.d2h_ms) / v2.total_ms
print(f"GPU: {gpu_name}, peak DRAM about {peak:.0f} GB/s")
print(f"CPU one core: nearest {cpu_nn:.1f} ms, bilinear {cpu_bl:.1f} ms")
print(f"v2 nearest: kernel {v2.kernel_ms:.2f} ms "
      f"({v2.speedup_kernel:.0f}x), end to end {v2.total_ms:.2f} ms "
      f"({v2.speedup_e2e:.1f}x)")
print(f"v3 bilinear: kernel {v3.kernel_ms:.2f} ms "
      f"({v3.speedup_kernel:.0f}x), end to end {v3.total_ms:.2f} ms "
      f"({v3.speedup_e2e:.1f}x)")
print(f"copies are {100 * copy_share:.0f}% of v2's GPU time")
print(f"v2 kernel moves {v2.kernel_GBps:.0f} GB/s = "
      f"{100 * v2.kernel_GBps / peak:.0f}% of peak DRAM bandwidth")
print(f"pinned H2D {v2.h2d_GBps:.1f} GB/s vs pageable {v4.h2d_GBps:.1f} "
      f"GB/s ({v2.h2d_GBps / v4.h2d_GBps:.2f}x)")
# Amdahl view: even an infinitely fast kernel cannot beat the copies.
bound = cpu_nn / (v2.h2d_ms + v2.d2h_ms)
print(f"Amdahl bound with copies kept, nearest: {bound:.1f}x "
      f"(measured {v2.speedup_e2e:.1f}x)")
bad = main[(main.section != "blocks") & (main.mismatch > 0) &
           ~main.variant.str.startswith("v6")]
print("all exact variants match the CPU" if bad.empty else bad)
""")

md("""
## 11. Tie-back to Week 9: the same kernel in Numba

Same inverse mapping, nearest neighbour, 2D grid of 16 x 16 blocks.
Numba compiles the kernel the first time it is called (JIT), so we launch
once to warm up before timing. Wrapped in `try` so the notebook still
finishes if Numba's CUDA support is missing on the runtime.
""")
code("""
import math
import numpy as np

try:
    from numba import cuda

    @cuda.jit
    def rotate_nn(src, dst, c, s, cx, cy):
        x, y = cuda.grid(2)             # blockIdx * blockDim + threadIdx
        h, w = dst.shape[0], dst.shape[1]
        if x >= w or y >= h:
            return
        dx = np.float32(x) - cx
        dy = np.float32(y) - cy
        sx = cx + c * dx - s * dy
        sy = cy + s * dx + c * dy
        ix = int(math.floor(sx + np.float32(0.5)))
        iy = int(math.floor(sy + np.float32(0.5)))
        for ch in range(3):
            if 0 <= ix < w and 0 <= iy < h:
                dst[y, x, ch] = src[iy, ix, ch]
            else:
                dst[y, x, ch] = 0

    W, H = 3840, 2160
    t = math.radians(30)
    c, s = np.float32(math.cos(t)), np.float32(math.sin(t))
    cx, cy = np.float32((W - 1) / 2), np.float32((H - 1) / 2)
    img = np.random.randint(0, 256, (H, W, 3), dtype=np.uint8)
    d_src = cuda.to_device(img)
    d_dst = cuda.device_array_like(img)
    block = (16, 16)
    grid = ((W + 15) // 16, (H + 15) // 16)

    rotate_nn[grid, block](d_src, d_dst, c, s, cx, cy)  # JIT + warm-up
    cuda.synchronize()
    e0, e1 = cuda.event(), cuda.event()
    e0.record()
    for _ in range(10):
        rotate_nn[grid, block](d_src, d_dst, c, s, cx, cy)
    e1.record()
    e1.synchronize()
    print(f"Numba kernel, 4K: {e0.elapsed_time(e1) / 10:.3f} ms")

    # NumPy reference with the same float32 maths
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = xs - cx, ys - cy
    ix = np.floor(cx + c * dx - s * dy + np.float32(0.5)).astype(int)
    iy = np.floor(cy + s * dx + c * dy + np.float32(0.5)).astype(int)
    ok = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
    ref = np.zeros_like(img)
    ref[ok] = img[iy[ok], ix[ok]]
    out = d_dst.copy_to_host()
    diff = np.count_nonzero(out != ref)
    print(f"bytes different from NumPy: {diff} of {out.size} "
          f"({100 * diff / out.size:.4f}%)")
    if diff:
        print("Numba lets LLVM fuse a*b+c into FMA, so a few pixels that"
              " sit right on a rounding edge land on the neighbour.")
except Exception as e:
    print("Numba CUDA section skipped:", e)
""")

md("## 12. Download everything in `results/`")
code("""
!zip -qr results.zip results
try:
    from google.colab import files
    files.download("results.zip")
except Exception:
    print("results.zip is in the Colab file browser")
""")

nb = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "T4"},
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
    },
    "cells": cells,
}
out = os.path.join(ROOT, "Applied2_Task1_Colab.ipynb")
with open(out, "w") as f:
    json.dump(nb, f, indent=1)
print("wrote", out, len(cells), "cells")
