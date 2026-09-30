"""
make_diagrams.py
FIT3143 Applied #2, Task 1 diagrams
Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu)
Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)

Draws the Task 1 figures as 1920x1080 PNGs (16:9, white background):
  D1_data_path.png         host <-> GPU memory transfer path
  D2_cuda_hierarchy.png    host/device roles, grid > block > warp > thread
  D3_gpudirect_storage.png traditional I/O path vs GPUDirect Storage
  D4_inverse_mapping.png   inverse mapping and bilinear sampling
  D5_streams_timeline.png  serial copies vs overlapped CUDA streams

Run: python3 make_diagrams.py   (needs matplotlib only)
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

OUT = os.path.dirname(os.path.abspath(__file__))

# One palette for every figure so the slides look consistent.
HOST, HOST_L = "#2F6DB5", "#DCE8F6"
GPU, GPU_L = "#2E8B57", "#DDF1E4"
BUS, BUS_L = "#D9820B", "#FCEFD6"
STOR, STOR_L = "#6B5B95", "#ECE7F4"
BAD, BAD_L = "#C0392B", "#F8E0DD"
INK, GREY = "#1F2933", "#7B8794"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 15,
    "text.color": INK,
})


def canvas(title, subtitle=None):
    """16:9 figure whose axes run 0..160 by 0..90, so layout is in units."""
    fig = plt.figure(figsize=(16, 9), dpi=120, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 160)
    ax.set_ylim(0, 90)
    ax.axis("off")
    ax.text(4, 85.5, title, fontsize=27, weight="bold", va="center")
    if subtitle:
        ax.text(4, 81, subtitle, fontsize=16, color=GREY, va="center")
    return fig, ax


def box(ax, x, y, w, h, text="", fc="white", ec=INK, fs=15, bold=False,
        lw=2.0, ls="-", va="center", tcolor=INK, r=1.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, ls=ls))
    if text:
        ty = y + h / 2 if va == "center" else y + h - 1.6
        ax.text(x + w / 2, ty, text, ha="center", va=va, fontsize=fs,
                weight="bold" if bold else "normal", color=tcolor,
                linespacing=1.3)


def arrow(ax, p0, p1, color=INK, lw=3, ls="-", both=False, rad=0.0,
          label=None, lpos=0.5, loff=(0, 1.6), fs=13, lcolor=None):
    style = "<|-|>" if both else "-|>"
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style,
                                 mutation_scale=22, color=color, lw=lw,
                                 ls=ls, connectionstyle=f"arc3,rad={rad}",
                                 shrinkA=2, shrinkB=2))
    if label:
        mx = p0[0] + (p1[0] - p0[0]) * lpos + loff[0]
        my = p0[1] + (p1[1] - p0[1]) * lpos + loff[1]
        ax.text(mx, my, label, ha="center", va="center", fontsize=fs,
                color=lcolor or color,
                bbox=dict(fc="white", ec="none", pad=1.5))


def badge(ax, x, y, n, color):
    """Numbered circle used to tie a diagram step to the legend."""
    ax.add_patch(plt.Circle((x, y), 1.7, fc=color, ec="white", lw=1.5,
                            zorder=5))
    ax.text(x, y, str(n), ha="center", va="center", color="white",
            fontsize=13, weight="bold", zorder=6)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=120, facecolor="white")
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- D1
def d1_data_path():
    fig, ax = canvas(
        "D1  Moving an image between host DDR5 and GPU memory",
        "cudaMemcpy / cudaMemcpyAsync: the GPU's DMA copy engine moves "
        "the bytes over PCIe, the CPU only queues the request")

    # Host side
    box(ax, 3, 13, 62, 63, "HOST (CPU side)", fc="#F7FAFD", ec=HOST,
        va="top", fs=18, bold=True, tcolor=HOST)
    box(ax, 7, 58, 22, 11, "CPU cores\n(decode, launch,\nsync)", fc=HOST_L,
        ec=HOST)
    box(ax, 7, 17, 22, 11, "NVMe SSD / disk\n(JPEG, PNG, raw)",
        fc=STOR_L, ec=STOR)
    box(ax, 34, 17, 28, 52, "", fc=HOST_L, ec=HOST)
    ax.text(48, 66, "DDR5 system RAM", ha="center", fontsize=16,
            weight="bold", color=HOST)
    ax.text(48, 62.5, "DDR5-4800: 38.4 GB/s per DIMM\n(76.8 GB/s dual channel)",
            ha="center", fontsize=11.5, color=GREY)
    box(ax, 36, 48, 24, 10, "pageable buffer\nmalloc()", fc="white",
        ec=BAD, lw=2.2)
    box(ax, 36, 35, 24, 10, "pinned staging buffer\n(made by the driver)",
        fc="white", ec=BAD, ls="--", lw=2.2, fs=13.5)
    box(ax, 36, 20, 24, 11, "pinned buffer\ncudaMallocHost()", fc="white",
        ec=GPU, lw=2.6)

    # PCIe
    box(ax, 69, 38, 18, 14, "PCIe root\ncomplex", fc=BUS_L, ec=BUS, fs=15)
    box(ax, 89, 28, 7, 34, "", fc=BUS_L, ec=BUS)
    ax.text(92.5, 45, "PCIe x16 link", rotation=90, ha="center",
            va="center", fontsize=15, color=BUS, weight="bold")
    ax.text(78, 25.5, "Per direction, x16:\nGen3 15.75 GB/s (T4)\n"
            "Gen4 31.5 GB/s\nGen5 63 GB/s", ha="center", va="top",
            fontsize=12.5, color=BUS)

    # GPU side
    box(ax, 99, 13, 58, 63, "DEVICE (GPU)", fc="#F7FCF9", ec=GPU,
        va="top", fs=18, bold=True, tcolor=GPU)
    box(ax, 102, 38, 16, 14, "DMA copy\nengines", fc=GPU_L, ec=GPU)
    box(ax, 123, 17, 31, 22, "", fc=GPU_L, ec=GPU)
    ax.text(138.5, 33.5, "Global memory", ha="center", fontsize=16,
            weight="bold", color=GPU)
    ax.text(138.5, 28.5, "T4: GDDR6 16 GB, 320 GB/s", ha="center",
            fontsize=12.5)
    ax.text(138.5, 25, "H100 SXM: HBM3 80 GB, 3.35 TB/s", ha="center",
            fontsize=12.5)
    ax.text(138.5, 20.5, "d_src, d_dst from cudaMalloc()", ha="center",
            fontsize=12.5, color=GREY)
    box(ax, 123, 44, 31, 7, "L2 cache", fc="white", ec=GPU, fs=14)
    for i in range(6):
        box(ax, 123 + i * 5.3, 55, 4.4, 10, "", fc=GPU_L, ec=GPU, lw=1.5,
            r=0.6)
    ax.text(138.5, 68.5, "SMs (T4 has 40)",
            ha="center", fontsize=14)

    # Flows
    arrow(ax, (18, 28), (35, 55), color=STOR, rad=-0.25,
          label="read + decode", lpos=0.35, loff=(-5, 2))
    arrow(ax, (48, 48), (48, 45), color=BAD, lw=3,
          label="extra CPU copy", loff=(0, 0), lpos=0.5, fs=12)
    arrow(ax, (60, 40), (69, 44), color=BAD, lw=3, ls="--")
    arrow(ax, (60, 25.5), (69, 41), color=GPU, lw=3.5)
    arrow(ax, (87, 45), (89, 45), color=BUS, lw=3, both=True)
    arrow(ax, (96, 45), (102, 45), color=BUS, lw=3, both=True)
    arrow(ax, (118, 45), (123, 30), color=GPU, lw=3.5, both=True)
    arrow(ax, (138.5, 39), (138.5, 44), color=GPU, lw=3, both=True)
    arrow(ax, (138.5, 51), (138.5, 55), color=GPU, lw=3, both=True)
    ax.text(111, 30, "H2D in\nD2H out", fontsize=12.5, ha="center",
            color=GPU)

    # Steps
    badge(ax, 16, 32, 1, STOR)
    badge(ax, 144, 41, 2, GPU)
    badge(ax, 64, 30, 3, GPU)
    badge(ax, 64, 45, 4, BAD)
    badge(ax, 121, 60, 5, GPU)
    badge(ax, 105, 55, 6, BUS)

    legend = [
        (1, STOR, "CPU reads + decodes the file into DDR5 (8K RGB = "
                  "99.5 MB)"),
        (2, GPU, "cudaMalloc reserves d_src, d_dst in GPU global memory"),
        (3, GPU, "Pinned: copy engine DMAs straight from page-locked RAM"),
        (4, BAD, "Pageable: driver first copies to a pinned staging "
                 "buffer"),
        (5, GPU, "Kernel works only in GPU memory (SMs, L2, GDDR)"),
        (6, BUS, "cudaMemcpy D2H brings the result back the same way"),
    ]
    for i, (n, c, t) in enumerate(legend):
        col, row = i % 2, i // 2
        x, y = 5 + col * 78, 9.5 - row * 3.4
        badge(ax, x, y, n, c)
        ax.text(x + 2.5, y, t, va="center", fontsize=12.2)
    save(fig, "D1_data_path.png")


# ---------------------------------------------------------------- D2
def d2_hierarchy():
    fig, ax = canvas(
        "D2  CUDA model: host launches, device runs a grid of blocks "
        "of threads",
        "rotate_bl_2d<<<grid, block>>>(d_src, d_dst, ...) on an 8K image:"
        " one thread per output pixel")

    # Host / device timeline strip
    ax.text(4, 75, "HOST (CPU)", fontsize=15, weight="bold", color=HOST,
            va="center")
    ax.text(4, 69, "DEVICE (GPU)", fontsize=15, weight="bold", color=GPU,
            va="center")
    steps = [("cudaMalloc", 21, 12), ("cudaMemcpy H2D", 34, 17),
             ("kernel<<<grid, block>>>\n(returns at once)", 52, 24),
             ("cudaMemcpy D2H\n(waits for kernel)", 77.5, 21),
             ("cudaFree", 99.5, 11)]
    for t, x, w in steps:
        box(ax, x, 72, w, 6, t, fc=HOST_L, ec=HOST, fs=12)
    box(ax, 34, 66, 17, 5, "DMA over PCIe", fc=BUS_L, ec=BUS, fs=12)
    box(ax, 52, 66, 24, 5, "129,600 blocks run on SMs", fc=GPU_L, ec=GPU,
        fs=12)
    box(ax, 77.5, 66, 21, 5, "DMA over PCIe", fc=BUS_L, ec=BUS, fs=12)
    ax.text(112, 72.5, "Host: allocate, copy, pick\n<<<grid, block>>>, "
            "launch,\nsync, copy back, check errors", fontsize=12.5,
            va="center", color=HOST)
    ax.text(112, 66, "Device: run the kernel as\nthousands of threads (SIMT)",
            fontsize=12.5, va="center", color=GPU)

    # Grid of blocks over the image
    gx, gy, cols, rows, cw, ch = 4, 16, 12, 7, 3.6, 5.2
    ax.text(gx, 60, "GRID  =  (480, 270) blocks", fontsize=16,
            weight="bold")
    ax.text(gx, 57, "dim3 grid((W+15)/16, (H+15)/16)", fontsize=12.5,
            color=GREY, family="monospace")
    for i in range(cols):
        for j in range(rows):
            hi = (i == 4 and j == 3)
            ax.add_patch(Rectangle((gx + i * cw, gy + j * ch), cw, ch,
                                   fc=GPU if hi else GPU_L, ec="white",
                                   lw=1.5))
    ax.text(gx, gy - 3, "8K output image, 7680 x 4320\n(only a few of "
            "the 129,600 blocks drawn)", ha="left", va="center",
            fontsize=12, color=GREY)
    ax.text(gx + 4.5 * cw, gy + 3.5 * ch, "4,3", ha="center",
            va="center", color="white", fontsize=10, weight="bold")

    # Zoomed block
    bx, by, s = 58, 16, 2.25
    ax.plot([gx + 5 * cw, bx], [gy + 4 * ch, by + 16 * s], color=GREY,
            lw=1.2, ls="--")
    ax.plot([gx + 5 * cw, bx], [gy + 3 * ch, by], color=GREY, lw=1.2,
            ls="--")
    ax.text(bx, 60, "BLOCK  =  16 x 16 = 256 threads", fontsize=16,
            weight="bold")
    ax.text(bx, 57, "dim3 block(16, 16)", fontsize=12.5, color=GREY,
            family="monospace")
    warp_cols = ["#CFE8D9", "#B6DCC5"]
    for tx in range(16):
        for ty in range(16):
            row_from_top = 15 - ty
            warp = row_from_top // 2
            fc = warp_cols[warp % 2]
            if row_from_top == 5 and tx == 9:
                fc = BAD
            ax.add_patch(Rectangle((bx + tx * s, by + ty * s), s, s,
                                   fc=fc, ec="white", lw=0.8))
    for wv in range(8):
        yy = by + (15 - 2 * wv) * s
        ax.text(bx + 16 * s + 0.8, yy, f"warp {wv}", fontsize=10.5,
                va="center", color=GPU)
    ax.text(bx + 8 * s, by - 3, "2 rows of 16 = one warp of 32 threads",
            ha="center", fontsize=12, color=GPU)

    # Index formula
    box(ax, 104, 36, 53, 23, "", fc="white", ec=INK, lw=1.5)
    ax.text(106, 55.5, "Each thread finds its own pixel:", fontsize=14,
            weight="bold")
    code = ("x = blockIdx.x * blockDim.x + threadIdx.x\n"
            "  = 4 * 16 + 9 = 73\n"
            "y = blockIdx.y * blockDim.y + threadIdx.y\n"
            "  = 3 * 16 + 5 = 53\n"
            "if (x >= W || y >= H) return;  // edge guard")
    ax.text(106, 46.5, code, family="monospace", fontsize=12.2,
            va="center", linespacing=1.45)
    ax.add_patch(Rectangle((106, 38), 2, 2, fc=BAD, ec="none"))
    ax.text(109, 39, "thread (9, 5) in block (4, 3) -> pixel (73, 53)",
            fontsize=12, va="center")

    # SM mapping
    ax.text(104, 31, "Blocks are scheduled onto SMs", fontsize=14,
            weight="bold")
    for k in range(4):
        box(ax, 104 + k * 13.4, 14, 12, 14, "", fc=GPU_L, ec=GPU, lw=1.5)
        ax.text(110 + k * 13.4, 25.5, f"SM {k if k < 3 else 39}",
                ha="center", fontsize=12, weight="bold", color=GPU)
        for b in range(2):
            ax.add_patch(Rectangle((105.2 + k * 13.4 + b * 5.4, 16), 4.6,
                                   6.5, fc=GPU, ec="white"))
    ax.text(143.5, 29, "...", fontsize=20, ha="center", color=GPU)
    ax.text(104, 10.5, "T4: max 1024 threads (32 warps) per SM, so up "
            "to 4 blocks\nof 256 are resident; schedulers swap warps "
            "to hide latency.", fontsize=12, va="center")
    ax.text(4, 5, "8K: 480 x 270 = 129,600 blocks x 256 threads = "
            "33,177,600 threads, one per pixel. Threads in a block share "
            "an SM (and shared memory); blocks are independent.",
            fontsize=13)
    save(fig, "D2_cuda_hierarchy.png")


# ---------------------------------------------------------------- D3
def d3_gds():
    fig, ax = canvas(
        "D3  GPUDirect Storage: skipping the CPU bounce buffer",
        "Data path only. The CPU still runs the control path (open, "
        "register, submit) in both cases.")

    def panel(x0, title, color, gds):
        box(ax, x0, 30, 74, 47, "", fc="#FBFBFB", ec=color, lw=2.5)
        ax.text(x0 + 37, 73.5, title, ha="center", fontsize=18,
                weight="bold", color=color)
        box(ax, x0 + 28, 61, 18, 8, "CPU", fc=HOST_L, ec=HOST)
        box(ax, x0 + 2, 47, 18, 10, "NVMe SSD\nor NVMe-oF", fc=STOR_L,
            ec=STOR)
        box(ax, x0 + 27, 47, 20, 10, "PCIe switch /\nroot complex",
            fc=BUS_L, ec=BUS, fs=13)
        box(ax, x0 + 54, 47, 18, 10, "GPU memory\n(GDDR/HBM)", fc=GPU_L,
            ec=GPU)
        box(ax, x0 + 26, 32.5, 22, 9, "DDR5 sysmem\nbounce buffer",
            fc=HOST_L if not gds else "#F1F1F1",
            ec=HOST if not gds else "#BBBBBB",
            tcolor=INK if not gds else "#AAAAAA", fs=13.5)
        if not gds:
            arrow(ax, (x0 + 20, 52), (x0 + 27, 52), color=BAD, lw=4)
            arrow(ax, (x0 + 33, 47), (x0 + 33, 41.5), color=BAD, lw=4)
            arrow(ax, (x0 + 41, 41.5), (x0 + 41, 47), color=BAD, lw=4)
            arrow(ax, (x0 + 47, 52), (x0 + 54, 52), color=BAD, lw=4)
            ax.text(x0 + 17, 44, "DMA 1: disk -> RAM", ha="center",
                    fontsize=12, color=BAD)
            ax.text(x0 + 60, 44, "DMA 2: RAM -> GPU", ha="center",
                    fontsize=12, color=BAD)
            arrow(ax, (x0 + 46, 65), (x0 + 60, 57), color=HOST, lw=2,
                  ls="--")
            ax.text(x0 + 50, 66.5, "read(), then cudaMemcpy()",
                    fontsize=12, color=HOST)
            txt = ("Data crosses PCIe twice and lands in DDR5 on the way.\n"
                   "Uses DDR5 bandwidth and CPU time; many GPUs share\n"
                   "one host memory system, so it saturates first.")
        else:
            arrow(ax, (x0 + 20, 52), (x0 + 27, 52), color=GPU, lw=4.5)
            arrow(ax, (x0 + 47, 52), (x0 + 54, 52), color=GPU, lw=4.5)
            ax.text(x0 + 37, 44, "one DMA: storage -> GPU memory",
                    ha="center", fontsize=12.5, color=GPU,
                    bbox=dict(fc="#FBFBFB", ec="none", pad=1))
            arrow(ax, (x0 + 46, 65), (x0 + 60, 57), color=HOST, lw=2,
                  ls="--")
            ax.text(x0 + 50, 66.5, "cuFileRead(): control only",
                    fontsize=12, color=HOST)
            txt = ("Storage DMA writes straight into GPU memory.\n"
                   "No bounce buffer, lower CPU load. Needs the nvidia-fs\n"
                   "driver, a supported filesystem and Linux.")
        ax.text(x0 + 37, 26, txt, ha="center", va="top", fontsize=12.5)

    panel(4, "Traditional path (POSIX read + cudaMemcpy)", BAD, False)
    panel(82, "GPUDirect Storage path (cuFile API)", GPU, True)

    ax.text(80, 18, "Published results: NVIDIA reports 2x to 8x higher "
            "bandwidth and 3.8x lower end-to-end latency [Thompson and "
            "Newburn, 2019];\nan HDF5 study measured about 2x read and "
            "write rates vs POSIX I/O [Ravi et al., 2020].",
            ha="center", va="center", fontsize=12, color=GREY,
            linespacing=1.4)

    # Verdict panel
    box(ax, 4, 2, 152, 13, "", fc="#FFFDF5", ec=BUS, lw=2)
    ax.text(6, 12.5, "Verdict for image rotation", fontsize=15,
            weight="bold", color=BUS, va="center")
    ax.text(6, 7.5, "Helps: huge batches of large raw frames streamed "
            "from NVMe or network storage, where storage I/O, the bounce "
            "copy or CPU load is the bottleneck.\nLittle or no help: image "
            "already in RAM, single images, JPEG/PNG decoded on the CPU "
            "(unless nvJPEG), unsupported FS or GPU (compatibility mode).",
            fontsize=12.5, va="center", linespacing=1.5)
    save(fig, "D3_gpudirect_storage.png")


# ---------------------------------------------------------------- D4
def d4_inverse_mapping():
    fig, ax = canvas(
        "D4  Inverse mapping: each output pixel asks where it came from",
        "One thread per destination pixel, one write each: no holes, "
        "no write races, no atomics")

    import math

    # Forward mapping problem: push each source pixel through R and
    # count how many land on each destination cell.
    box(ax, 3, 28, 46, 49, "", fc="#FFF9F8", ec=BAD, lw=2)
    ax.text(26, 73.5, "Forward mapping (not used)", ha="center",
            fontsize=15, weight="bold", color=BAD)
    ax.text(26, 70, "src pixel -> R -> nearest dst cell", ha="center",
            fontsize=12, color=BAD)
    n_src, n_dst, cell, gx0, gy0 = 8, 12, 3.3, 6.2, 29.5
    th = math.radians(30)
    hits = {}
    c0 = (n_dst - 1) / 2
    for i in range(n_src):
        for j in range(n_src):
            dx, dy = i - (n_src - 1) / 2, j - (n_src - 1) / 2
            fx = c0 + math.cos(th) * dx - math.sin(th) * dy
            fy = c0 + math.sin(th) * dx + math.cos(th) * dy
            key = (round(fx), round(fy))
            hits[key] = hits.get(key, 0) + 1
    half = (n_src - 1) / 2 + 0.5
    corners = []
    for dx, dy in [(-half, -half), (half, -half), (half, half),
                   (-half, half)]:
        corners.append((c0 + math.cos(th) * dx - math.sin(th) * dy,
                        c0 + math.sin(th) * dx + math.cos(th) * dy))
    poly = Polygon([(gx0 + (u + 0.5) * cell, gy0 + (v + 0.5) * cell)
                    for u, v in corners], closed=True, fill=False,
                   ec=INK, lw=1.6, ls="--", zorder=4)
    inside = poly.get_path()
    for i in range(n_dst):
        for j in range(n_dst):
            k = hits.get((i, j), 0)
            ctr = (gx0 + (i + 0.5) * cell, gy0 + (j + 0.5) * cell)
            fc = {0: "white", 1: "#F1B8B0"}.get(k, BAD)
            ax.add_patch(Rectangle((gx0 + i * cell, gy0 + j * cell), cell,
                                   cell, fc=fc, ec="#DDDDDD", lw=0.8))
            if k == 0 and inside.contains_point(ctr):
                ax.text(ctr[0], ctr[1], "x", ha="center", va="center",
                        fontsize=12, color=BAD, weight="bold")
    ax.add_patch(poly)
    legend_items = [("#F1B8B0", "hit once"),
                    (BAD, "hit twice: race"),
                    ("white", "x = hole")]
    for k, (fc, t) in enumerate(legend_items):
        xx = 6.2 + k * 15.5
        ax.add_patch(Rectangle((xx, 25.2 - 0.0), 2.2, 2.2, fc=fc,
                               ec="#999999", lw=0.8))
        ax.text(xx + 2.8, 26.3, t, fontsize=11.5, va="center", color=BAD)

    # Destination grid
    ox, oy, s = 60, 32, 5
    ax.text(ox + 12.5, 73.5, "Destination (output)", ha="center",
            fontsize=15, weight="bold", color=GPU)
    for i in range(5):
        for j in range(7):
            fc = GPU if (i, j) == (2, 3) else GPU_L
            ax.add_patch(Rectangle((ox + i * s, oy + j * s), s, s, fc=fc,
                                   ec="white", lw=1.5))
    ax.text(ox + 2.5 * s, oy + 3.5 * s, "(x,y)", ha="center",
            va="center", color="white", fontsize=12, weight="bold")
    ax.text(ox + 12.5, oy - 3, "thread (x, y) owns this pixel",
            ha="center", fontsize=12.5, color=GPU)

    # Source grid with the sample point and its 4 neighbours
    sx0, sy0, ss = 112, 30, 8.5
    ax.text(sx0 + 2.5 * ss, 73.5, "Source (input)", ha="center",
            fontsize=15, weight="bold", color=HOST)
    for i in range(5):
        for j in range(5):
            ax.add_patch(Rectangle((sx0 + i * ss, sy0 + j * ss), ss, ss,
                                   fc=HOST_L, ec="white", lw=1.5))
    # Row y0 is drawn above row y0+1 because image rows grow downwards.
    left, right = sx0 + 1.5 * ss, sx0 + 2.5 * ss
    top, bottom = sy0 + 3.5 * ss, sy0 + 2.5 * ss
    px, py = left + 0.35 * ss, top - 0.4 * ss
    pts = [(left, top, "p00 (x0, y0)", "right"),
           (right, top, "p10 (x0+1, y0)", "left"),
           (left, bottom, "p01 (x0, y0+1)", "right"),
           (right, bottom, "p11 (x0+1, y0+1)", "left")]
    for x, y, t, side in pts:
        ax.add_patch(plt.Circle((x, y), 0.9, fc=HOST, zorder=4))
        ax.plot([px, x], [py, y], color=HOST, lw=1.2, ls=":", zorder=3)
        dx = -1.4 if side == "right" else 1.4
        ax.text(x + dx, y + 1.8, t, ha=side, fontsize=11.5, color=HOST)
    ax.add_patch(plt.Circle((px, py), 1.1, fc=BAD, zorder=5))
    ax.text(px, py - 2.6, "(sx, sy)", fontsize=12.5, color=BAD,
            weight="bold", ha="center")
    ax.text(sx0 + 2.5 * ss, sy0 - 3, "ax = sx - x0,  ay = sy - y0",
            ha="center", fontsize=12.5, color=HOST)

    arrow(ax, (ox + 3 * s, oy + 3.5 * s), (px - 1.4, py + 0.4), color=BAD,
          lw=3.5, rad=-0.3, label="R^-1 = R^T", lpos=0.5, loff=(0, 6),
          fs=15)

    # Formulas
    box(ax, 3, 2, 154, 19, "", fc="white", ec=INK, lw=1.5)
    ax.text(5, 18.5, "Maths per thread: rotate by t about the centre "
            "(cx, cy), counterclockwise on screen (y flipped because rows "
            "grow downwards)", fontsize=13.5, weight="bold")
    ax.text(5, 10, "dx = x - cx,   dy = y - cy\n"
            "sx = cx + cos(t) dx - sin(t) dy\n"
            "sy = cy + sin(t) dx + cos(t) dy",
            family="monospace", fontsize=13.5, va="center",
            linespacing=1.5)
    ax.text(62, 10, "Nearest: round (sx, sy), copy one pixel.\n"
            "Bilinear: out = (1-ax)(1-ay) p00 + ax(1-ay) p10\n"
            "                + (1-ax) ay p01 + ax ay p11\n"
            "No source pixel -> black (0).",
            fontsize=13, va="center", linespacing=1.4)
    ax.text(123, 10, "Cost per output pixel:\nnearest: 1 gathered read\n"
            "bilinear: 4 gathered reads\nboth memory-bound",
            fontsize=13, va="center", linespacing=1.4, color=GPU)
    save(fig, "D4_inverse_mapping.png")


# ---------------------------------------------------------------- D5
def d5_streams():
    fig, ax = canvas(
        "D5  CUDA streams: overlapping copies with compute",
        "Illustrative timeline (not to scale). Needs pinned memory and "
        "cudaMemcpyAsync; the real gain is measured in the notebook.")

    c = {"H2D": BUS, "K": GPU, "D2H": HOST}
    lab = {"H2D": "H2D", "K": "kernel", "D2H": "D2H"}

    def seg(y, x, w, kind, txt=None):
        ax.add_patch(Rectangle((x, y), w, 5.2, fc=c[kind], ec="white",
                               lw=1.5))
        ax.text(x + w / 2, y + 2.6, txt or lab[kind], ha="center",
                va="center", color="white", fontsize=11.5, weight="bold")

    # Serial
    ax.text(4, 72, "Default stream: one image after another", fontsize=16,
            weight="bold")
    ax.text(4, 66.6, "stream 0", fontsize=13, va="center")
    x = 16
    for i in range(4):
        seg(64, x, 8, "H2D", f"H2D {i}")
        seg(64, x + 8, 3, "K", f"K{i}")
        seg(64, x + 11, 8, "D2H", f"D2H {i}")
        x += 19
    ax.annotate("", xy=(92, 61), xytext=(16, 61),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=1.5))
    ax.text(54, 58.8, "total = sum of every stage", ha="center",
            fontsize=12.5)

    # Streams
    ax.text(4, 52, "4 streams: image i goes to stream i % 4", fontsize=16,
            weight="bold")
    for i in range(4):
        y = 44 - i * 7
        ax.text(4, y + 2.6, f"stream {i}", fontsize=13, va="center")
        x0 = 16 + i * 8
        seg(y, x0, 8, "H2D", f"H2D {i}")
        seg(y, x0 + 8, 3, "K", f"K{i}")
        seg(y, x0 + 11, 8, "D2H", f"D2H {i}")
    ax.annotate("", xy=(59, 20.5), xytext=(16, 20.5),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=1.5))
    ax.text(37.5, 18.3, "about max(H2D, D2H) per image once the pipe "
            "is full", ha="center", fontsize=12.5)

    # Notes
    box(ax, 100, 16, 56, 58, "", fc="#FBFBFB", ec=INK, lw=1.5)
    notes = [
        ("Why it helps", "H2D and D2H use separate copy engines and\n"
         "PCIe is full duplex, so one image uploads\nwhile another "
         "downloads and a third is rotated."),
        ("Why it is capped", "Rotation's kernel is short next to its "
         "copies,\nso copies stay the bottleneck: best case is\nabout "
         "2x (both PCIe directions busy)."),
        ("One image (v5a)", "Output rows for a band may need source rows "
         "\nfrom anywhere, so a band's kernel waits for\nthe H2D chunks "
         "that cover its source rows.\nSmall angles overlap well, large "
         "ones less."),
        ("Rules", "cudaMallocHost buffers, cudaMemcpyAsync,\none buffer "
         "pair per stream, sync at the end."),
    ]
    y = 70.5
    for head, body in notes:
        ax.text(102, y, head, fontsize=14, weight="bold", va="top")
        ax.text(102, y - 3.4, body, fontsize=12.2, va="top",
                linespacing=1.35)
        y -= 14
    for k, (name, col) in enumerate([("H2D copy", BUS), ("kernel", GPU),
                                     ("D2H copy", HOST)]):
        ax.add_patch(Rectangle((16 + k * 24, 8), 3, 3, fc=col))
        ax.text(20 + k * 24, 9.5, name, va="center", fontsize=13)
    save(fig, "D5_streams_timeline.png")


if __name__ == "__main__":
    d1_data_path()
    d2_hierarchy()
    d3_gds()
    d4_inverse_mapping()
    d5_streams()
