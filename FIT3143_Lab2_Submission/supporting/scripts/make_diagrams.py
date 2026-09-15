####################################################################
# make_diagrams.py
# ------------------------------------------------------------------
# FIT3143 Lab #2 Task 4: the three explanatory diagrams the deck
# needs that are not plots of measured data.
#
# Written by: Erwyna Soo Wen Xin (36555789)
#
# Erwyna: graphs 1 to 10 come out of measurements, so make_graphs.py
# builds those. These three are drawings of how the code is put
# together, so they live here. Same dark colours as the graphs so the
# slides look like one set.
#
# Run: python3 make_diagrams.py
####################################################################
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

OUT = "graphs"
os.makedirs(OUT, exist_ok=True)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'

BG, TEXT, SUB, GRID = '#0F172A', '#F8FAFC', '#94A3B8', '#334155'
RANKC = ['#FDCB6E', '#00D2D3', '#00B894', '#FF7675']
LIVE3 = ['#FDCB6E', '#00D2D3', '#54A0FF']   # p = 3 row, kept clear of the red used for the idle rank
DEAD  = '#FF4757'


def frame(title, subtitle, w=11.0, h=6.2):
    fig, ax = plt.subplots(figsize=(w, h), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(title, fontsize=15, fontweight='bold', color=TEXT, pad=26, loc='left')
    ax.text(0.0, 1.03, subtitle, transform=ax.transAxes, fontsize=10, color=SUB)
    return fig, ax


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), facecolor=BG)
    plt.close(fig)
    print("  wrote", name)


# =====================================================================
# Diagram 1: the cyclic stride, and why p = 3 breaks
# =====================================================================
fig, ax = frame('How the candidates are handed out',
                'Rank r takes 3 + 2r, then steps by 2p. Top: p = 4, even. Bottom: p = 3, one rank idle.')
ax.set_xlim(0, 24); ax.set_ylim(0, 10)

nums = [3 + 2 * i for i in range(20)]

# ---- p = 4, balanced ----
ax.text(0, 8.9, 'p = 4', fontsize=13, fontweight='bold', color=TEXT)
ax.text(2.6, 8.95, 'no odd factor, so every rank gets a fair mix', fontsize=9.5, color=SUB)
for i, n in enumerate(nums):
    r = i % 4
    ax.add_patch(Rectangle((i * 1.15 + 0.1, 7.3), 1.0, 1.1,
                           facecolor=RANKC[r], edgecolor='none', zorder=3))
    ax.text(i * 1.15 + 0.6, 7.85, str(n), ha='center', va='center',
            fontsize=8.5, fontweight='bold', color='#0F172A', zorder=4)
    ax.text(i * 1.15 + 0.6, 7.0, f'r{r}', ha='center', va='center',
            fontsize=7.5, color=SUB, zorder=4)

# ---- p = 3, broken ----
ax.text(0, 5.3, 'p = 3', fontsize=13, fontweight='bold', color=TEXT)
ax.text(2.6, 5.35, 'stride 6, so rank 0 only ever sees multiples of 3', fontsize=9.5, color=SUB)
for i, n in enumerate(nums):
    r = i % 3
    dead = (n % 3 == 0)
    ax.add_patch(Rectangle((i * 1.15 + 0.1, 3.7), 1.0, 1.1,
                           facecolor=DEAD if dead else LIVE3[r],
                           edgecolor='none', alpha=0.40 if dead else 1.0, zorder=3))
    ax.text(i * 1.15 + 0.6, 4.25, str(n), ha='center', va='center', fontsize=8.5,
            fontweight='bold', color='#0F172A', zorder=4)
    ax.text(i * 1.15 + 0.6, 3.4, f'r{r}', ha='center', va='center',
            fontsize=7.5, color=SUB, zorder=4)

ax.text(0.1, 2.4,
        'Rank 0 holds 3, 9, 15, 21 ...  all multiples of 3, so apart from 3 itself is_prime rejects each one on its first check.',
        fontsize=10.5, color=DEAD, fontweight='bold')
ax.text(0.1, 1.7,
        'Measured at n = 130,000,000:  rank 0 finished in 0.012 s having found 2 primes.',
        fontsize=10.5, color=TEXT)
ax.text(0.1, 1.05,
        'Ranks 1 and 2 took 7.6 s each and found 3.69 million each.',
        fontsize=10.5, color=TEXT)
ax.text(0.1, 0.3,
        'In general, for any odd prime d dividing p, one rank in d is idle:  p_eff = p (1 - 1/d).',
        fontsize=10.5, color=SUB, style='italic')
save(fig, 'diagram1_stride_partition.png')

# =====================================================================
# Diagram 2: Gatherv offset management
# =====================================================================
fig, ax = frame('Bringing the primes back to the root',
                'MPI_Gather of the counts, then MPI_Gatherv places each block at its own displacement.')
ax.set_xlim(0, 12); ax.set_ylim(0, 8)

counts = [1844654, 1844589, 1844669, 1844275]
w = 2.3
gap = 0.35
x0 = 0.4

# local arrays, one per rank
tops = []
x = x0
for r in range(4):
    ax.add_patch(Rectangle((x, 6.15), w, 0.95, facecolor=RANKC[r], edgecolor='none', zorder=3))
    ax.text(x + w / 2, 6.63, f'rank {r}', ha='center', va='center',
            fontsize=11.5, fontweight='bold', color='#0F172A', zorder=4)
    ax.text(x + w / 2, 7.62, f'{counts[r]:,}', ha='center', fontsize=10,
            fontweight='bold', color=TEXT)
    ax.text(x + w / 2, 7.28, 'primes found', ha='center', fontsize=8.5, color=SUB)
    tops.append(x + w / 2)
    x += w + gap

# root array directly underneath, short arrows in the gap
y = 4.35
x = x0
disp = 0
for r in range(4):
    ax.add_patch(Rectangle((x, y), w, 0.95, facecolor=RANKC[r], edgecolor='none', zorder=3))
    ax.text(x + w / 2, y + 0.48, f'disp {disp:,}', ha='center', va='center',
            fontsize=9.5, fontweight='bold', color='#0F172A', zorder=4)
    ax.add_patch(FancyArrowPatch((tops[r], 6.10), (x + w / 2, y + 1.02),
                                 arrowstyle='-|>', mutation_scale=13,
                                 color=RANKC[r], lw=1.7, alpha=0.85, zorder=2))
    disp += counts[r]
    x += w

ax.add_patch(Rectangle((x0, y), 4 * w, 0.95, facecolor='none',
                       edgecolor=TEXT, lw=1.7, zorder=5))
ax.text(x0, 3.85, 'One contiguous array on the root:  7,378,187 primes',
        fontsize=11, color=TEXT, fontweight='bold')

# the three steps, below everything, nothing crossing them
ax.text(x0, 3.05, 'Step 1', fontsize=10.5, color=RANKC[0], fontweight='bold')
ax.text(x0 + 1.05, 3.05, 'MPI_Gather sends one integer per rank, so the root learns the four counts.',
        fontsize=10.5, color=TEXT)
ax.text(x0, 2.45, 'Step 2', fontsize=10.5, color=RANKC[1], fontweight='bold')
ax.text(x0 + 1.05, 2.45, 'The root turns the counts into displacements:  disp[i] = disp[i-1] + count[i-1]',
        fontsize=10.5, color=TEXT)
ax.text(x0, 1.85, 'Step 3', fontsize=10.5, color=RANKC[2], fontweight='bold')
ax.text(x0 + 1.05, 1.85, 'MPI_Gatherv writes every block straight into its own slice, in one call.',
        fontsize=10.5, color=TEXT)

ax.text(x0, 1.05,
        'The blocks arrive interleaved rather than sorted, because the split was cyclic, so the root then qsorts.',
        fontsize=10, color=SUB)
ax.text(x0, 0.45,
        'Measured cost of the whole exchange: 0.005 s at p = 1, 0.036 s at p = 28. A shared memory copy, not network traffic.',
        fontsize=10, color=SUB, style='italic')
save(fig, 'diagram2_gatherv_offsets.png')

# =====================================================================
# Diagram 3: the hybrid, two levels
# =====================================================================
fig, ax = frame('Two levels of parallelism in Task 2',
                'MPI strides across processes. OpenMP hands out chunks dynamically inside each one.')
ax.set_xlim(0, 12); ax.set_ylim(0, 8)

ax.add_patch(Rectangle((0.4, 6.6), 11.2, 0.9, facecolor=GRID, edgecolor='none', zorder=2))
ax.text(6.0, 7.05, 'All odd candidates below n', ha='center', va='center',
        fontsize=11.5, fontweight='bold', color=TEXT, zorder=3)

for pi in range(2):
    px = 0.4 + pi * 5.85
    ax.add_patch(Rectangle((px, 3.1), 5.35, 2.9, facecolor='#1E293B',
                           edgecolor=RANKC[pi], lw=1.8, zorder=2))
    ax.text(px + 2.67, 5.62, f'MPI process {pi}', ha='center', fontsize=11.5,
            fontweight='bold', color=RANKC[pi], zorder=3)
    ax.text(px + 2.67, 5.18, f'takes 3 + {2*pi}, stepping by 4', ha='center',
            fontsize=9, color=SUB, zorder=3)
    ax.add_patch(FancyArrowPatch((px + 2.67, 6.55), (px + 2.67, 6.05),
                                 arrowstyle='-|>', mutation_scale=14,
                                 color=RANKC[pi], lw=1.8, zorder=3))
    for ti in range(3):
        tx = px + 0.35 + ti * 1.62
        ax.add_patch(Rectangle((tx, 3.5), 1.42, 1.4, facecolor=RANKC[pi],
                               alpha=0.30, edgecolor='none', zorder=3))
        ax.text(tx + 0.71, 4.35, f'thread {ti}', ha='center', fontsize=9.5,
                fontweight='bold', color=TEXT, zorder=4)
        ax.text(tx + 0.71, 3.85, 'own buffer', ha='center', fontsize=8, color=SUB, zorder=4)

ax.text(0.4, 2.45, 'schedule(dynamic, 1000)   a thread that draws a cheap chunk comes straight back for another,',
        fontsize=10.5, color=TEXT)
ax.text(0.4, 1.95, 'so threads self balance at runtime in a way the fixed MPI stride cannot.',
        fontsize=10.5, color=TEXT)
ax.text(0.4, 1.25, 'Each thread writes its own pre-allocated buffer, so there is no lock and no false sharing on the hot path.',
        fontsize=10, color=SUB)
ax.text(0.4, 0.6, 'Only the MPI stride can leave a process idle: with 6 workers, 2 x 3 took 3.39 s but 3 x 2 took 4.72 s.',
        fontsize=10, color='#00B894', fontweight='bold')
save(fig, 'diagram3_hybrid_layout.png')

print("done")
