#!/usr/bin/env python3
"""
make_partition_graph.py

Draws partition_comparison.png from partition_comparison.csv, in the same
style as make_graphs.py: run time of Task 1 at n = 130,000,000 for three ways
of splitting the odd candidates, at 2 to 14 MPI processes.

    python3 make_partition_graph.py

Team: Erwyna Soo Wen Xin (36555789) and Taabish Farooq Bhat (35473932).
Written with Claude (Anthropic) on 16 September 2026.
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'

BG, PANEL, TEXT, SUB, GRID = '#0F172A', '#1E293B', '#F8FAFC', '#94A3B8', '#334155'
COLOURS = {"stride (submitted)": '#FDCB6E', "block": '#FF7675', "chunked 1000": '#00B894'}
LABELS = {"stride (submitted)": "Cyclic stride (submitted task1.c)",
          "block": "Block split",
          "chunked 1000": "Chunks of 1000 dealt in turn"}
MARKERS = {"stride (submitted)": 'D', "block": 's', "chunked 1000": 'o'}

rows = list(csv.DictReader(open(os.path.join(HERE, "partition_comparison.csv"))))
procs = sorted({int(r["procs"]) for r in rows})

fig, ax = plt.subplots(figsize=(11.0, 6.2), facecolor=BG)
ax.set_facecolor(BG)
ax.grid(True, linestyle=':', alpha=0.6, color=GRID, zorder=0)
for name in LABELS:
    ys = [float(r["wall_s"]) for p in procs for r in rows if int(r["procs"]) == p and r["partition"] == name]
    ax.plot(procs, ys, color=COLOURS[name], marker=MARKERS[name], lw=2.6, ms=6, label=LABELS[name], zorder=3)

# The two points the slide talks about
s3 = next(float(r["wall_s"]) for r in rows if r["procs"] == "3" and r["partition"] == "stride (submitted)")
c3 = next(float(r["wall_s"]) for r in rows if r["procs"] == "3" and r["partition"] == "chunked 1000")
ax.annotate(f"p = 3: stride {s3:.2f} s", (3, s3), xytext=(4.2, s3 + 0.6), color=TEXT, fontsize=9.5,
            arrowprops=dict(arrowstyle='->', color=SUB))
ax.annotate(f"chunks {c3:.2f} s", (3, c3), xytext=(2.05, c3 - 1.3), color=TEXT, fontsize=9.5,
            arrowprops=dict(arrowstyle='->', color=SUB))

ax.set_title("Three ways to split the work, measured", fontsize=15, fontweight='bold', color=TEXT,
             pad=26, loc='left')
ax.text(0.0, 1.03, "Task 1 at n = 130,000,000. Whole mpirun command, fastest of 2 runs. "
        "Same gather, sort and file write in all three.", transform=ax.transAxes, fontsize=10, color=SUB)
ax.set_xlabel("Number of MPI processes", fontsize=11, fontweight='bold', color=TEXT, labelpad=10)
ax.set_ylabel("Run time (seconds)", fontsize=11, fontweight='bold', color=TEXT, labelpad=10)
ax.set_xticks(procs)
ax.tick_params(colors=TEXT, labelsize=10)
for s in ax.spines.values():
    s.set_color(GRID)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
leg = ax.legend(frameon=True, facecolor=PANEL, edgecolor=GRID, fontsize=9.5, loc='upper right')
for t in leg.get_texts():
    t.set_color(TEXT)

fig.tight_layout()
out = os.path.join(HERE, "partition_comparison.png")
fig.savefig(out, facecolor=BG)
print("wrote", out)
