import matplotlib.pyplot as plt

# ---------------------------------------------------------
# GLOBAL AESTHETIC & THEME SETUP (STUDIO DARK MODE)
# ---------------------------------------------------------
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'

COLOR_BG     = '#0F172A'  # Deep Slate Dark Canvas
COLOR_PANEL  = '#1E293B'  # Lighter Slate Panel
COLOR_TEXT   = '#F8FAFC'  # Crisp White
COLOR_SUB    = '#94A3B8'  # Muted Gray
COLOR_GRID   = '#334155'  # Soft Dark Gridlines

# Vibrant Neon Palette
C_SERIAL  = '#FF4757'  # Coral Red
C_PTH     = '#00D2D3'  # Neon Teal / Cyan
C_OMP     = '#5F27CD'  # Deep Violet / Indigo
C_OMP_ALT = '#54A0FF'  # Electric Blue
C_IDEAL   = '#6C5CE7'  # Purple Accent

# Real Benchmark Data recorded from your terminal runs
n_labels = ['100,000', '1,000,000', '10,000,000']
threads  = [1, 2, 4, 8]

serial_times = [0.002767, 0.060426, 1.361119]

pth_times = {
    100000:   [0.003140, 0.002155, 0.001715, 0.002307],
    1000000:  [0.058656, 0.035198, 0.026954, 0.014248],
    10000000: [1.410183, 0.709423, 0.543915, 0.309347]
}

omp_times = {
    100000:   [0.002987, 0.002938, 0.001629, 0.001937],
    1000000:  [0.060262, 0.034161, 0.028925, 0.016757],
    10000000: [1.473122, 0.747188, 0.455161, 0.294874]
}

def style_axis(ax, title, subtitle, xlabel, ylabel):
    ax.set_facecolor(COLOR_BG)
    ax.grid(True, linestyle=':', alpha=0.6, color=COLOR_GRID, zorder=0)
    
    # Custom Title & Subtitle Styling
    ax.set_title(title, fontsize=14, fontweight='bold', color=COLOR_TEXT, pad=25, loc='left')
    ax.text(0.0, 1.03, subtitle, transform=ax.transAxes, fontsize=9.5, color=COLOR_SUB)
    
    ax.set_xlabel(xlabel, fontsize=10.5, fontweight='bold', color=COLOR_TEXT, labelpad=10)
    ax.set_ylabel(ylabel, fontsize=10.5, fontweight='bold', color=COLOR_TEXT, labelpad=10)
    
    ax.tick_params(colors=COLOR_TEXT, labelsize=9.5)
    
    # Borderless Spines
    for spine in ax.spines.values():
        spine.set_color(COLOR_GRID)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

def create_legend(ax, loc='upper left'):
    leg = ax.legend(frameon=True, facecolor=COLOR_PANEL, edgecolor=COLOR_GRID, fontsize=9, loc=loc)
    for text in leg.get_texts():
        text.set_color(COLOR_TEXT)
    return leg

# ---------------------------------------------------------
# GRAPH 1: Runtime vs n (Serial vs POSIX Threads)
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 5), facecolor=COLOR_BG)
pth_8t = [pth_times[100000][3], pth_times[1000000][3], pth_times[10000000][3]]

ax.plot(n_labels, serial_times, color=C_SERIAL, marker='o', linewidth=2.8, markersize=8, label='Task 1: Serial Code', zorder=3)
ax.plot(n_labels, pth_8t, color=C_PTH, marker='s', linewidth=2.8, markersize=8, label='Task 2: Pthreads (8 Threads)', zorder=4)

for i, (s, p) in enumerate(zip(serial_times, pth_8t)):
    ax.annotate(f"{s:.3f}s", (i, s), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8.5, fontweight='bold', color=C_SERIAL)
    ax.annotate(f"{p:.3f}s", (i, p), textcoords="offset points", xytext=(0, -18), ha='center', fontsize=8.5, fontweight='bold', color=C_PTH)

style_axis(ax, 'Graph 1: Execution Time vs Input Size (n)', 'Comparing Serial vs POSIX Threads (8 Threads) performance scale', 'Input Size (n)', 'Runtime (Seconds)')
create_legend(ax)
plt.tight_layout()
plt.savefig('graph1_pthreads_runtime_vs_n.png')
plt.close()

# ---------------------------------------------------------
# GRAPH 2: Speedup vs n (POSIX Threads)
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 5), facecolor=COLOR_BG)
sp_2t = [serial_times[i] / pth_times[n_val][1] for i, n_val in enumerate([100000, 1000000, 10000000])]
sp_4t = [serial_times[i] / pth_times[n_val][2] for i, n_val in enumerate([100000, 1000000, 10000000])]
sp_8t = [serial_times[i] / pth_times[n_val][3] for i, n_val in enumerate([100000, 1000000, 10000000])]

ax.plot(n_labels, sp_2t, color='#FF9F43', marker='o', linewidth=2.5, label='Pthreads (2 Threads)', zorder=3)
ax.plot(n_labels, sp_4t, color='#00FECA', marker='^', linewidth=2.5, label='Pthreads (4 Threads)', zorder=4)
ax.plot(n_labels, sp_8t, color='#10AC84', marker='s', linewidth=2.8, label='Pthreads (8 Threads)', zorder=5)

for i, val in enumerate(sp_8t):
    ax.annotate(f"{val:.2f}x", (i, val), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9, fontweight='bold', color='#10AC84')

style_axis(ax, 'Graph 2: POSIX Threads Speedup vs Input Size (n)', 'Demonstrating how workload scaling unlocks parallel speedup', 'Input Size (n)', 'Speedup Factor (T1 / Tp)')
create_legend(ax, loc='upper left')
plt.tight_layout()
plt.savefig('graph2_pthreads_speedup_vs_n.png')
plt.close()

# ---------------------------------------------------------
# GRAPH 3: Runtime vs Threads (Serial vs POSIX Threads)
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 5), facecolor=COLOR_BG)
pth_10m = pth_times[10000000]

ax.axhline(y=serial_times[2], color=C_SERIAL, linestyle='--', linewidth=2, label='Task 1: Serial Baseline (1.361s)', zorder=2)
ax.plot(threads, pth_10m, color=C_PTH, marker='o', linewidth=2.8, markersize=8, label='Task 2: POSIX Threads (n = 10M)', zorder=4)

for p, t in zip(threads, pth_10m):
    ax.annotate(f"{t:.3f}s", (p, t), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9, fontweight='bold', color=C_PTH)

ax.set_xticks(threads)
style_axis(ax, 'Graph 3: Execution Time vs Thread Count', 'Target: n = 10,000,000 | Evaluating POSIX Threads scaling efficiency', 'Number of Threads', 'Runtime (Seconds)')
create_legend(ax, loc='upper right')
plt.tight_layout()
plt.savefig('graph3_pthreads_runtime_vs_threads.png')
plt.close()

# ---------------------------------------------------------
# GRAPH 4: Speedup vs Threads (POSIX Threads)
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 5), facecolor=COLOR_BG)
sp_100k = [serial_times[0] / t for t in pth_times[100000]]
sp_1m   = [serial_times[1] / t for t in pth_times[1000000]]
sp_10m  = [serial_times[2] / t for t in pth_times[10000000]]

ax.plot(threads, threads, color=COLOR_SUB, linestyle='--', linewidth=1.8, label='Ideal Linear Speedup', zorder=1)
ax.plot(threads, sp_100k, color='#FF9F43', marker='o', linewidth=2, label='n = 100,000', zorder=3)
ax.plot(threads, sp_1m,   color='#54A0FF', marker='^', linewidth=2, label='n = 1,000,000', zorder=4)
ax.plot(threads, sp_10m,  color=C_PTH,     marker='s', linewidth=2.8, label='n = 10,000,000', zorder=5)

for p, val in zip(threads, sp_10m):
    ax.annotate(f"{val:.2f}x", (p, val), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9, fontweight='bold', color=C_PTH)

ax.set_xticks(threads)
style_axis(ax, 'Graph 4: POSIX Threads Speedup vs Thread Count', 'Comparison of actual speedup curves against ideal linear scaling', 'Number of Threads', 'Speedup Factor (T1 / Tp)')
create_legend(ax, loc='upper left')
plt.tight_layout()
plt.savefig('graph4_pthreads_speedup_vs_threads.png')
plt.close()

# ---------------------------------------------------------
# GRAPH 5: Runtime vs n (Serial vs OpenMP)
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 5), facecolor=COLOR_BG)
omp_8t = [omp_times[100000][3], omp_times[1000000][3], omp_times[10000000][3]]

ax.plot(n_labels, serial_times, color=C_SERIAL, marker='o', linewidth=2.8, markersize=8, label='Task 1: Serial Code', zorder=3)
ax.plot(n_labels, omp_8t, color=C_OMP_ALT, marker='s', linewidth=2.8, markersize=8, label='Task 3: OpenMP (8 Threads)', zorder=4)

for i, (s, o) in enumerate(zip(serial_times, omp_8t)):
    ax.annotate(f"{s:.3f}s", (i, s), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8.5, fontweight='bold', color=C_SERIAL)
    ax.annotate(f"{o:.3f}s", (i, o), textcoords="offset points", xytext=(0, -18), ha='center', fontsize=8.5, fontweight='bold', color=C_OMP_ALT)

style_axis(ax, 'Graph 5: OpenMP Execution Time vs Input Size (n)', 'Comparing Serial vs OpenMP Dynamic Loop Scheduling (8 Threads)', 'Input Size (n)', 'Runtime (Seconds)')
create_legend(ax)
plt.tight_layout()
plt.savefig('graph5_openmp_runtime_vs_n.png')
plt.close()

# ---------------------------------------------------------
# GRAPH 6: Speedup vs n (OpenMP)
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 5), facecolor=COLOR_BG)
omp_sp_2t = [serial_times[i] / omp_times[n_val][1] for i, n_val in enumerate([100000, 1000000, 10000000])]
omp_sp_4t = [serial_times[i] / omp_times[n_val][2] for i, n_val in enumerate([100000, 1000000, 10000000])]
omp_sp_8t = [serial_times[i] / omp_times[n_val][3] for i, n_val in enumerate([100000, 1000000, 10000000])]

ax.plot(n_labels, omp_sp_2t, color='#A3CB38', marker='o', linewidth=2.5, label='OpenMP (2 Threads)', zorder=3)
ax.plot(n_labels, omp_sp_4t, color='#12CBC4', marker='^', linewidth=2.5, label='OpenMP (4 Threads)', zorder=4)
ax.plot(n_labels, omp_sp_8t, color=C_OMP_ALT, marker='s', linewidth=2.8, label='OpenMP (8 Threads)', zorder=5)

for i, val in enumerate(omp_sp_8t):
    ax.annotate(f"{val:.2f}x", (i, val), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9, fontweight='bold', color=C_OMP_ALT)

style_axis(ax, 'Graph 6: OpenMP Speedup vs Input Size (n)', 'Evaluating OpenMP dynamic load balancing performance scaling', 'Input Size (n)', 'Speedup Factor (T1 / Tp)')
create_legend(ax, loc='upper left')
plt.tight_layout()
plt.savefig('graph6_openmp_speedup_vs_n.png')
plt.close()

# ---------------------------------------------------------
# GRAPH 7: Runtime vs n (POSIX Threads vs OpenMP)
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 5), facecolor=COLOR_BG)

ax.plot(n_labels, pth_8t, color=C_PTH, marker='o', linewidth=2.8, markersize=8, label='Task 2: POSIX Threads (8 Threads)', zorder=3)
ax.plot(n_labels, omp_8t, color=C_OMP_ALT, marker='s', linestyle='--', linewidth=2.8, markersize=8, label='Task 3: OpenMP (8 Threads)', zorder=4)

for i, (p, o) in enumerate(zip(pth_8t, omp_8t)):
    ax.annotate(f"{p:.3f}s", (i, p), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8.5, fontweight='bold', color=C_PTH)
    ax.annotate(f"{o:.3f}s", (i, o), textcoords="offset points", xytext=(0, -18), ha='center', fontsize=8.5, fontweight='bold', color=C_OMP_ALT)

style_axis(ax, 'Graph 7: Pthreads vs OpenMP Runtime across Input Size (n)', 'Direct paradigm comparison at maximum thread concurrency (8 Threads)', 'Input Size (n)', 'Runtime (Seconds)')
create_legend(ax, loc='upper left')
plt.tight_layout()
plt.savefig('graph7_pthreads_vs_openmp_runtime_n.png')
plt.close()

# ---------------------------------------------------------
# GRAPH 8: Runtime vs Threads (POSIX Threads vs OpenMP)
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 5), facecolor=COLOR_BG)
omp_10m = omp_times[10000000]

ax.plot(threads, pth_10m, color=C_PTH, marker='o', linewidth=2.8, markersize=8, label='Task 2: POSIX Threads', zorder=3)
ax.plot(threads, omp_10m, color=C_OMP_ALT, marker='s', linestyle='--', linewidth=2.8, markersize=8, label='Task 3: OpenMP (Dynamic)', zorder=4)

for p, pt, ot in zip(threads, pth_10m, omp_10m):
    if p in [4, 8]:
        ax.annotate(f"{pt:.3f}s", (p, pt), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8.5, fontweight='bold', color=C_PTH)
        ax.annotate(f"{ot:.3f}s", (p, ot), textcoords="offset points", xytext=(0, -18), ha='center', fontsize=8.5, fontweight='bold', color=C_OMP_ALT)

ax.set_xticks(threads)
style_axis(ax, 'Graph 8: Pthreads vs OpenMP Runtime across Thread Counts', 'Target: n = 10,000,000 | Comparing manual thread management vs compiler pragmas', 'Number of Threads', 'Runtime (Seconds)')
create_legend(ax, loc='upper right')
plt.tight_layout()
plt.savefig('graph8_pthreads_vs_openmp_threads.png')
plt.close()

print("All 8 custom graphs generated successfully!")