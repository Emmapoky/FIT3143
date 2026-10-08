"""Clean slide diagrams: shapes and a few BIG labels only. All explanation lives in
Canva bullets, never inside the picture. 1920x1080 PNGs, text >= 34pt at 120 dpi."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clean")
os.makedirs(OUT, exist_ok=True)
BLUE, NAVY, LIGHT = "#2563EB", "#0B2A5B", "#DCE8FF"
GREEN, GREEN_L = "#2E8B57", "#DDF1E4"
ORANGE, ORANGE_L = "#D9820B", "#FCEFD6"
RED, RED_L = "#C0392B", "#F8E0DD"
GREY = "#6B7280"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": NAVY})


def canvas():
    fig = plt.figure(figsize=(16, 9), dpi=120, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 160); ax.set_ylim(0, 90); ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text="", fc=LIGHT, ec=BLUE, fs=38, tc=NAVY, lw=4, bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=2",
                                fc=fc, ec=ec, lw=lw))
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                color=tc, weight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, p0, p1, color=NAVY, lw=7, rad=0.0, both=False):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="<|-|>" if both else "-|>",
                                 mutation_scale=45, color=color, lw=lw,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=3, shrinkB=3))


def label(ax, x, y, t, fs=38, color=NAVY, bold=True, ha="center"):
    ax.text(x, y, t, ha=ha, va="center", fontsize=fs, color=color,
            weight="bold" if bold else "normal", linespacing=1.25)


def grid(ax, x, y, n, m, cell, fc="white", ec=BLUE, lw=2.5, hl=None, hlc=BLUE):
    for i in range(n):
        for j in range(m):
            c = hlc if hl and (i, j) in hl else fc
            ax.add_patch(Rectangle((x + j * cell, y + (n - 1 - i) * cell), cell, cell,
                                   fc=c, ec=ec, lw=lw))


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=120, facecolor="white")
    plt.close(fig)


# 1. inverse mapping ---------------------------------------------------------
fig, ax = canvas()
label(ax, 38, 80, "Output image", fs=44)
grid(ax, 10, 18, 6, 6, 9.3, fc=GREEN_L, ec=GREEN, hl={(3, 2)}, hlc=GREEN)
label(ax, 38, 8, "one thread per pixel", fs=34, bold=False)
label(ax, 122, 80, "Source image", fs=44)
grid(ax, 94, 18, 6, 6, 9.3, fc=LIGHT, ec=BLUE, hl={(2, 3)}, hlc=BLUE)
label(ax, 122, 8, "read one pixel", fs=34, bold=False)
arrow(ax, (47, 40), (97, 52), color=RED, rad=-0.25)
label(ax, 80, 63, "rotate back", fs=40, color=RED)
save(fig, "inverse_mapping.png")

# 2. host <-> device data path -----------------------------------------------
fig, ax = canvas()
box(ax, 6, 52, 46, 28, "CPU\nmemory")
box(ax, 108, 52, 46, 28, "GPU\nmemory", fc=GREEN_L, ec=GREEN)
arrow(ax, (54, 66), (106, 66), color=ORANGE, both=True)
label(ax, 80, 74, "PCIe", fs=44, color=ORANGE)
label(ax, 80, 58, "12.3 GB/s", fs=40, color=ORANGE)
label(ax, 131, 44, "320 GB/s inside", fs=34, color=GREEN)
box(ax, 6, 10, 70, 22, "Pageable:\nextra staging copy", fc=RED_L, ec=RED, fs=34, tc=RED)
box(ax, 84, 10, 70, 22, "Pinned:\ndirect DMA", fc=GREEN_L, ec=GREEN, fs=34, tc=GREEN)
save(fig, "data_path.png")

# 3. CUDA hierarchy ----------------------------------------------------------
fig, ax = canvas()
label(ax, 30, 82, "Grid", fs=46)
grid(ax, 6, 22, 5, 6, 8.6, fc="white", ec=BLUE, hl={(2, 3)}, hlc=BLUE)
label(ax, 32, 12, "480 x 270 blocks", fs=36, bold=False)
arrow(ax, (58, 50), (74, 50))
label(ax, 100, 82, "Block", fs=46)
grid(ax, 78, 28, 8, 8, 5.4, fc=LIGHT, ec=GREEN, lw=2, hl={(3, 4)}, hlc=GREEN)
label(ax, 100, 18, "16 x 16 threads", fs=36, bold=False)
label(ax, 100, 8, "= 8 warps of 32", fs=36, bold=False)
box(ax, 130, 42, 26, 18, "1 thread\n= 1 pixel", fc=GREEN_L, ec=GREEN, fs=30, tc=GREEN)
arrow(ax, (123, 51), (129, 51), color=GREEN)
save(fig, "cuda_hierarchy.png")

# 4. GDS ---------------------------------------------------------------------
fig, ax = canvas()
label(ax, 80, 82, "Traditional", fs=40, color=RED, ha="center")
box(ax, 6, 56, 34, 18, "NVMe", fc="#ECE7F4", ec="#6B5B95", fs=36)
box(ax, 63, 56, 34, 18, "CPU RAM", fc=RED_L, ec=RED, fs=36)
box(ax, 120, 56, 34, 18, "GPU", fc=GREEN_L, ec=GREEN, fs=36)
arrow(ax, (41, 65), (62, 65), color=RED); arrow(ax, (98, 65), (119, 65), color=RED)
label(ax, 80, 40, "GPUDirect Storage", fs=40, color=GREEN)
box(ax, 6, 12, 34, 18, "NVMe", fc="#ECE7F4", ec="#6B5B95", fs=36)
box(ax, 120, 12, 34, 18, "GPU", fc=GREEN_L, ec=GREEN, fs=36)
arrow(ax, (41, 21), (119, 21), color=GREEN, lw=9)
label(ax, 80, 27, "direct DMA", fs=34, color=GREEN)
save(fig, "gds.png")

# 5. streams timeline --------------------------------------------------------
fig, ax = canvas()
label(ax, 80, 82, "Serial", fs=40, ha="center")
x = 6
for k in range(3):
    for wdt, c in ((14, BLUE), (6, GREEN), (14, ORANGE)):
        ax.add_patch(Rectangle((x, 56), wdt, 14, fc=c, ec="white", lw=2)); x += wdt
label(ax, 80, 44, "4 streams overlap", fs=40, color=GREEN)
for s in range(3):
    x0 = 6 + s * 20
    for wdt, c in ((14, BLUE), (6, GREEN), (14, ORANGE)):
        ax.add_patch(Rectangle((x0, 24 - s * 9 + 8), wdt, 7, fc=c, ec="white", lw=2)); x0 += wdt
for i, (t, c) in enumerate((("copy in", BLUE), ("kernel", GREEN), ("copy out", ORANGE))):
    ax.add_patch(Rectangle((40 + i * 33, 3), 5, 5, fc=c, ec="white"))
    label(ax, 47 + i * 33, 5.5, t, fs=30, bold=False, ha="left")
save(fig, "streams.png")

# 6. data residency ----------------------------------------------------------
fig, ax = canvas()
box(ax, 6, 22, 56, 50, "Country A\nGPU nodes", fs=40)
box(ax, 98, 22, 56, 50, "Country B\nGPU nodes", fc=GREEN_L, ec=GREEN, fs=40)
ax.plot([80, 80], [8, 82], color=RED, lw=6, ls="--")
arrow(ax, (63, 52), (97, 52), color=RED, both=True)
label(ax, 80, 78, "border", fs=40, color=RED)
label(ax, 80, 40, "gradients\ncross", fs=34, color=RED)
save(fig, "residency.png")
print("ok", os.listdir(OUT))
