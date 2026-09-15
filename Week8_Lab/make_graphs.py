####################################################################
# make_graphs.py
# ------------------------------------------------------------------
# FIT3143 Lab #2 Tasks 3 and 4: builds the seven required graphs and
# three supporting ones from our measured CSVs, and works out the
# Amdahl parameters that graphs 6, 7 and 10 are drawn from.
#
# Written by: Erwyna Soo Wen Xin (36555789)
#
# Team:
#   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
#   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
#
# Erwyna: same dark theme as our Week 4 graphs. Every graph is saved at
# 300 dpi on a solid background, sized to fit a 16:9 slide without
# being stretched.
#
# Run: python3 make_graphs.py
####################################################################
import csv, os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "graphs"
os.makedirs(OUT, exist_ok=True)

plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'

BG    = '#0F172A'
PANEL = '#1E293B'
TEXT  = '#F8FAFC'
SUB   = '#94A3B8'
GRID  = '#334155'

C_SERIAL = '#FF4757'
C_PTH    = '#00D2D3'
C_OMP    = '#5F27CD'
C_MPI    = '#FDCB6E'
C_HYB    = '#00B894'
C_THEORY = '#54A0FF'
C_IDEAL  = '#8395A7'


def read(path):
    with open(path) as f:
        return [ {k: v for k, v in row.items()} for row in csv.DictReader(f) ]


def f(row, key):
    return float(row[key])


def style(ax, title, subtitle, xlabel, ylabel):
    ax.set_facecolor(BG)
    ax.grid(True, linestyle=':', alpha=0.6, color=GRID, zorder=0)
    ax.set_title(title, fontsize=15, fontweight='bold', color=TEXT, pad=26, loc='left')
    ax.text(0.0, 1.03, subtitle, transform=ax.transAxes, fontsize=10, color=SUB)
    ax.set_xlabel(xlabel, fontsize=11, fontweight='bold', color=TEXT, labelpad=10)
    ax.set_ylabel(ylabel, fontsize=11, fontweight='bold', color=TEXT, labelpad=10)
    ax.tick_params(colors=TEXT, labelsize=10)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


def legend(ax, loc='upper left'):
    leg = ax.legend(frameon=True, facecolor=PANEL, edgecolor=GRID, fontsize=9.5, loc=loc)
    for t in leg.get_texts():
        t.set_color(TEXT)
    return leg


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), facecolor=BG)
    plt.close(fig)
    print("  wrote", name)


def newfig(w=11.0, h=6.2):
    return plt.subplots(figsize=(w, h), facecolor=BG)


# =====================================================================
# Load
# =====================================================================
by_n     = read("results_by_n.csv")
by_procs = read("results_by_procs.csv")
hyb_t    = read("results_hybrid_t.csv")
hyb_tot  = read("results_hybrid_total.csv")
ph1      = read("phases_task1.csv")
ph2      = read("phases_task2.csv")
phs      = read("phases_serial.csv")

W_FIXED = 14
HP, HT = 2, 7
NFIX = int(by_procs[0].get('n', 0)) if 'n' in by_procs[0] else None

# =====================================================================
# GRAPH 1: run time vs n
# =====================================================================
ns  = [f(r, 'n') / 1e6 for r in by_n]
fig, ax = newfig()
ax.plot(ns, [f(r, 'serial_s')  for r in by_n], color=C_SERIAL, marker='o', lw=2.6, ms=5, label='Week 4 Task 1: Serial (1 process)')
ax.plot(ns, [f(r, 'pthread_s') for r in by_n], color=C_PTH,    marker='s', lw=2.6, ms=5, label=f'Week 4 Task 2: POSIX Threads ({W_FIXED} threads)')
ax.plot(ns, [f(r, 'omp_s')     for r in by_n], color=C_OMP,    marker='^', lw=2.6, ms=5, label=f'Week 4 Task 3: OpenMP ({W_FIXED} threads)')
ax.plot(ns, [f(r, 'mpi_s')     for r in by_n], color=C_MPI,    marker='D', lw=2.8, ms=5, label=f'Week 8 Task 1: Open MPI ({W_FIXED} processes)')
ax.plot(ns, [f(r, 'hybrid_s')  for r in by_n], color=C_HYB,    marker='v', lw=2.8, ms=5, label=f'Week 8 Task 2: Hybrid ({HP} proc x {HT} threads)')
style(ax, 'Graph 1  Run time against problem size',
      'Overall wall clock, whole command including mpirun launch, sort and file write. Fastest of repeated runs.',
      'Problem size n (millions)', 'Run time (seconds)')
legend(ax)
save(fig, 'graph1_runtime_vs_n.png')

# =====================================================================
# GRAPH 2: empirical speedup vs n
# =====================================================================
fig, ax = newfig()
for key, col, mk, lab in [('pthread_s', C_PTH, 's', f'POSIX Threads ({W_FIXED} threads)'),
                          ('omp_s',     C_OMP, '^', f'OpenMP ({W_FIXED} threads)'),
                          ('mpi_s',     C_MPI, 'D', f'Open MPI ({W_FIXED} processes)'),
                          ('hybrid_s',  C_HYB, 'v', f'Hybrid ({HP} proc x {HT} threads)')]:
    ax.plot(ns, [f(r, 'serial_s') / f(r, key) for r in by_n], color=col, marker=mk, lw=2.6, ms=5, label=lab)
ax.axhline(1.0, color=C_IDEAL, ls='--', lw=1.4)
ax.text(ns[0], 1.06, 'speedup = 1, no gain over serial', color=SUB, fontsize=9)
style(ax, 'Graph 2  Empirical speedup against problem size',
      'Speedup = Week 4 serial wall clock / parallel wall clock, at a fixed width of 14 workers.',
      'Problem size n (millions)', 'Empirical speedup')
legend(ax)
save(fig, 'graph2_speedup_vs_n.png')

# =====================================================================
# GRAPH 3: empirical speedup vs width
# =====================================================================
ws = [int(f(r, 'width')) for r in by_procs]
fig, ax = newfig()
ax.plot(ws, ws, color=C_IDEAL, ls='--', lw=1.6, label='Linear (ideal) speedup')
ax.plot(ws, [f(r, 'serial_s') / f(r, 'pthread_s') for r in by_procs], color=C_PTH, marker='s', lw=2.6, ms=5, label='POSIX Threads')
ax.plot(ws, [f(r, 'serial_s') / f(r, 'omp_s')     for r in by_procs], color=C_OMP, marker='^', lw=2.6, ms=5, label='OpenMP')
ax.plot(ws, [f(r, 'serial_s') / f(r, 'mpi_s')     for r in by_procs], color=C_MPI, marker='D', lw=2.8, ms=5, label='Open MPI')
ax.axvline(14, color=SUB, ls=':', lw=1.4)
ax.text(14.3, 0.5, '14 physical cores', color=SUB, fontsize=9, rotation=90, va='bottom')
style(ax, 'Graph 3  Empirical speedup against width',
      'Width = MPI processes for Open MPI, threads for POSIX/OpenMP. Same n throughout.',
      'Number of processes / threads', 'Empirical speedup vs Week 4 serial')
legend(ax)
save(fig, 'graph3_speedup_vs_width.png')

# =====================================================================
# GRAPH 4: hybrid vs MPI, threads growing at fixed process count
# =====================================================================
ts = [int(f(r, 'threads')) for r in hyb_t]
serial_fixed = f(by_procs[0], 'serial_s')
fig, ax = newfig()
ax.plot(ts, [serial_fixed / f(r, 'hybrid_4proc_s') for r in hyb_t], color=C_HYB, marker='v', lw=2.8, ms=6, label='Task 2 hybrid: 4 MPI processes x t threads')
ax.plot(ts, [serial_fixed / f(r, 'mpi_4proc_s')    for r in hyb_t], color=C_MPI, marker='D', lw=2.8, ms=6, ls='--', label='Task 1 Open MPI: 4 MPI processes (t has no effect)')
style(ax, 'Graph 4  Hybrid against pure Open MPI as threads are added',
      'MPI process count held at 4 for both. Only the hybrid can use the extra threads.',
      'OpenMP threads per MPI process', 'Empirical speedup vs Week 4 serial')
legend(ax)
save(fig, 'graph4_hybrid_vs_mpi_threads.png')

# =====================================================================
# GRAPH 5: hybrid vs OpenMP / POSIX at matched total width
# =====================================================================
hyb_tot.sort(key=lambda r: (int(f(r, 'width')), int(f(r, 'procs'))))
labels = [f"{int(f(r,'procs'))}x{int(f(r,'threads'))}\n({int(f(r,'width'))})" for r in hyb_tot]
x = range(len(hyb_tot))
fig, ax = newfig(12.0, 6.4)
ax.plot(x, [serial_fixed / f(r, 'hybrid_s')  for r in hyb_tot], color=C_HYB, marker='v', lw=2.8, ms=6, label='Task 2 hybrid (p processes x t threads)')
ax.plot(x, [serial_fixed / f(r, 'omp_s')     for r in hyb_tot], color=C_OMP, marker='^', lw=2.4, ms=5, label='OpenMP at p x t threads')
ax.plot(x, [serial_fixed / f(r, 'pthread_s') for r in hyb_tot], color=C_PTH, marker='s', lw=2.4, ms=5, label='POSIX Threads at p x t threads')
ax.plot(x, [serial_fixed / f(r, 'mpi_s')     for r in hyb_tot], color=C_MPI, marker='D', lw=2.4, ms=5, label='Open MPI at p x t processes')
ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=8.5)
style(ax, 'Graph 5  Matched width: same number of workers, four ways of arranging them',
      'Every point on a column commands the same total worker count. Bracketed number is p x t.',
      'Hybrid configuration, processes x threads (total width)', 'Empirical speedup vs Week 4 serial')
legend(ax)
save(fig, 'graph5_matched_width.png')

# =====================================================================
# Amdahl's Law
# ---------------------------------------------------------------------
# Erwyna: the fractions come from the p = 1 run of the parallel program
# itself, not from the Week 4 serial program. That is the honest
# baseline for Amdahl, because Amdahl asks what fraction of THIS code
# can be spread out, and Taabish's search loop is a different (faster)
# primality test than my Week 4 one. Mixing the two would fold an
# algorithmic win into what is supposed to be a parallelism measurement.
# The Week 4 comparison is still there, it is what graphs 2, 3, 4 and 5
# are about; this is a separate question.
#
#   S(p) = 1 / ( r_s + r_p / p + kappa(p) )
#
#   r_p      = comp(1) / T(1)             the search loop, the only part that spreads
#   r_s      = (sort+write)(1) / T(1)     qsort and fprintf on the root, never spreads
#   kappa(p) = (bcast+gather)(p) / T(1)   MEASURED at every p
#
# Erwyna: kappa here is small, because every rank is on one machine and
# MPI_Gatherv is a shared memory copy rather than network traffic. That
# is worth saying out loud: on this hardware communication is NOT what
# stops the speedup. What stops it is the load imbalance below.
#
# THE EFFECTIVE PROCESS COUNT.
# The stride partition gives rank r the numbers 3 + 2r + 2pk. For any
# odd prime d dividing p, 2pk is 0 mod d, so every number rank r ever
# tests is congruent to 3 + 2r modulo d. The rank whose class is 0 mod d
# therefore receives ONLY multiples of d, and is_prime rejects those on
# its first iteration. One rank in d does no work at all.
#
# So the code does not really have p workers, it has
#
#   p_eff = p * (1 - 1/d),   d = smallest odd prime factor of p
#   p_eff = p                when p is a power of two
#
# and Amdahl evaluated at p_eff, rather than at p, is what the machine
# actually delivers. This is measured, not assumed: comp_min_s in
# phases_task1.csv shows the idle rank directly, and comp_max/comp_mean
# comes out at 1/(1 - 1/d) to two decimal places at every width.
# =====================================================================
def smallest_odd_factor(p):
    q = p
    while q % 2 == 0:
        q //= 2
    if q == 1:
        return None            # p is a power of two, the partition is even
    d = 3
    while d * d <= q:
        if q % d == 0:
            return d
        d += 2
    return q


def p_effective(p):
    d = smallest_odd_factor(p)
    return p if d is None else p * (1.0 - 1.0 / d)


ph1.sort(key=lambda r: int(f(r, 'procs')))
base1 = next(r for r in ph1 if int(f(r, 'procs')) == 1)
T1 = f(base1, 'total_s')
rp1 = f(base1, 'comp_s') / T1
rs1 = (f(base1, 'sort_s') + f(base1, 'write_s')) / T1

p1_w    = [int(f(r, 'procs')) for r in ph1]
p1_emp  = [T1 / f(r, 'total_s') for r in ph1]
p1_kap  = [(f(r, 'bcast_s') + f(r, 'gather_s')) / T1 for r in ph1]
p1_th   = [1.0 / (rs1 + rp1 / w + k) for w, k in zip(p1_w, p1_kap)]
p1_eff  = [1.0 / (rs1 + rp1 / p_effective(w) + k) for w, k in zip(p1_w, p1_kap)]

fig, ax = newfig()
ax.plot(p1_w, p1_w,   color=C_IDEAL,  ls='--', lw=1.5, label='Linear (ideal) speedup')
ax.plot(p1_w, p1_th,  color=C_THEORY, ls=':', marker='o', lw=2.4, ms=4,
        label='Amdahl at p, assuming the partition is even')
ax.plot(p1_w, p1_eff, color=C_HYB,    marker='^', lw=2.6, ms=5,
        label='Amdahl at p_eff, using the measured idle rank')
ax.plot(p1_w, p1_emp, color=C_MPI,    marker='D', lw=2.8, ms=5, label='Empirical (measured)')
ax.axvline(14, color=SUB, ls=':', lw=1.4)
ax.text(14.3, 0.5, '14 physical cores', color=SUB, fontsize=9, rotation=90, va='bottom')
style(ax, 'Graph 6  Task 1 Open MPI: empirical against theoretical speedup',
      f'r_p = {rp1:.4f}, r_s = {rs1:.4f}, kappa measured at every p. The saw tooth is the partition, not noise.',
      'Number of MPI processes', 'Speedup relative to the same code at p = 1')
legend(ax)
save(fig, 'graph6_amdahl_task1.png')

# =====================================================================
# GRAPH 7: hybrid, empirical vs theoretical
# =====================================================================
ph2.sort(key=lambda r: (int(f(r, 'procs')) * int(f(r, 'threads')), int(f(r, 'procs'))))
b2 = ph2[0]
w2base = int(f(b2, 'procs')) * int(f(b2, 'threads'))
T2 = f(b2, 'total_s')
rp2 = f(b2, 'comp_s') / T2
rs2 = (f(b2, 'sort_s') + f(b2, 'write_s')) / T2

# Erwyna: the hybrid dodges most of the residue-class problem, because
# only the MPI stride is congruence bound. Inside a rank, OpenMP hands
# out chunks dynamically, so a thread that draws a cheap chunk simply
# comes back for another one. Only the process count carries the flaw,
# which is why 2 x 7 beats 7 x 2 even though both command 14 workers.
w2   = [int(f(r, 'procs')) * int(f(r, 'threads')) for r in ph2]
lab2 = [f"{int(f(r,'procs'))}x{int(f(r,'threads'))}" for r in ph2]
eff2 = [p_effective(int(f(r, 'procs'))) * int(f(r, 'threads')) for r in ph2]
emp2 = [T2 / f(r, 'total_s') for r in ph2]
kap2 = [(f(r, 'bcast_s') + f(r, 'gather_s') + f(r, 'merge_s')) / T2 for r in ph2]
th2  = [1.0 / (rs2 + rp2 / w + k) for w, k in zip(w2, kap2)]
the2 = [1.0 / (rs2 + rp2 / e + k) for e, k in zip(eff2, kap2)]

x = range(len(ph2))
fig, ax = newfig(12.0, 6.4)
ax.plot(x, w2,   color=C_IDEAL,  ls='--', lw=1.5, label='Linear (ideal) speedup')
ax.plot(x, th2,  color=C_THEORY, ls=':', marker='o', lw=2.4, ms=4, label='Amdahl at p x t')
ax.plot(x, the2, color=C_OMP,    marker='^', lw=2.4, ms=5, label='Amdahl at p_eff x t')
ax.plot(x, emp2, color=C_HYB,    marker='v', lw=2.8, ms=6, label='Empirical (measured)')
ax.set_xticks(list(x)); ax.set_xticklabels([f"{l}\n({w})" for l, w in zip(lab2, w2)], fontsize=8.5)
style(ax, 'Graph 7  Task 2 hybrid: empirical against theoretical speedup',
      f'r_p = {rp2:.4f}, r_s = {rs2:.4f}. Only the process count is congruence bound; OpenMP schedules dynamically.',
      'Hybrid configuration, processes x threads (total width)', 'Speedup relative to a single worker')
legend(ax)
save(fig, 'graph7_amdahl_task2.png')

# =====================================================================
# Supporting figure 8: where the time actually goes
# =====================================================================
fig, ax = newfig()
wsx    = [str(int(f(r, 'procs'))) for r in ph1]
comp   = [f(r, 'comp_s') - f(r, 'comp_min_s') for r in ph1]
busy   = [f(r, 'comp_min_s') for r in ph1]
comms  = [f(r, 'bcast_s') + f(r, 'gather_s') for r in ph1]
srt    = [f(r, 'sort_s') for r in ph1]
wrt    = [f(r, 'write_s') for r in ph1]
bot = [0.0] * len(ph1)
for vals, col, lab in [(busy,  C_MPI,    'Search, work every rank shares (parallel)'),
                       (comp,  '#E17055', 'Search, imbalance carried by the busiest rank'),
                       (comms, C_SERIAL, 'Bcast + Gatherv (communication)'),
                       (srt,   C_OMP,    'qsort on root (serial)'),
                       (wrt,   C_PTH,    'File write on root (serial)')]:
    ax.bar(wsx, vals, bottom=bot, color=col, label=lab, zorder=3)
    bot = [b + v for b, v in zip(bot, vals)]
style(ax, 'Where the time goes in Task 1 as processes are added',
      'Measured phase split from task1_instr.c. Communication is barely visible; imbalance is not.',
      'Number of MPI processes', 'Time (seconds)')
legend(ax, loc='upper right')
save(fig, 'graph8_phase_breakdown.png')

# =====================================================================
# Supporting figure 9: the per rank evidence
# =====================================================================
try:
    rb = read("rank_balance.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.0, 5.6), facecolor=BG)
    for ax_, pp in [(a1, 3), (a2, 4)]:
        rows = [r for r in rb if int(f(r, 'procs')) == pp]
        rr   = [str(int(f(r, 'rank'))) for r in rows]
        tt   = [f(r, 'comp_s') for r in rows]
        cols = [C_SERIAL if t < max(tt) * 0.1 else C_MPI for t in tt]
        ax_.bar(rr, tt, color=cols, zorder=3)
        for i, (t, r) in enumerate(zip(tt, rows)):
            ax_.text(i, t, f"  {int(f(r,'primes_found')):,}\n  primes", ha='center',
                     va='bottom', fontsize=8, color=TEXT)
        d = smallest_odd_factor(pp)
        style(ax_, f'p = {pp}', 
              ('every rank is locked to one residue class mod %d' % d) if d
              else 'p is a power of two, no odd factor, even split',
              'MPI rank', 'Search time (seconds)')
        ax_.set_ylim(0, max(tt) * 1.35)
    fig.suptitle('Why the saw tooth: per rank search time and primes found',
                 fontsize=15, fontweight='bold', color=TEXT, x=0.02, ha='left', y=0.99)
    save(fig, 'graph9_rank_balance.png')
except OSError:
    print("  (rank_balance.csv not found, skipping graph 9)")

# =====================================================================
# Supporting figure 10: theoretical against empirical speedup as n grows
# ---------------------------------------------------------------------
# Erwyna: graphs 6 and 7 hold n still and grow the process count. The
# spec also asks for the theoretical speedup as n grows, so this graph
# uses run_phases_by_n.py, which runs every n twice: on one worker to
# get r_p and r_s at that n, and on 14 workers (14 processes, or 2 x 7
# for the hybrid) to get kappa and the measured speedup. Same formula
# as graphs 6 and 7, with the fractions measured again at every n.
# =====================================================================
def model_by_n(rows, width_of, comm_of, eff_width_of):
    out = []
    for nval in sorted({int(f(r, 'n')) for r in rows}):
        at_n = [r for r in rows if int(f(r, 'n')) == nval]
        one  = [r for r in at_n if width_of(r) == 1]
        wide = [r for r in at_n if width_of(r) > 1]
        if not one or not wide:
            continue
        b, w = one[0], wide[0]
        T  = f(b, 'total_s')
        rp = f(b, 'comp_s') / T
        rs = (f(b, 'sort_s') + f(b, 'write_s')) / T
        k  = comm_of(w) / T
        p  = width_of(w)
        pe = eff_width_of(w)
        out.append((nval, rp, rs, k, p,
                    1.0 / (rs + rp / p + k),
                    1.0 / (rs + rp / pe + k),
                    T / f(w, 'total_s')))
    return out


try:
    bn1 = read("phases_by_n_task1.csv")
    bn2 = read("phases_by_n_task2.csv")
    m1 = model_by_n(bn1, lambda r: int(f(r, 'procs')),
                    lambda r: f(r, 'bcast_s') + f(r, 'gather_s'),
                    lambda r: p_effective(int(f(r, 'procs'))))
    m2 = model_by_n(bn2, lambda r: int(f(r, 'procs')) * int(f(r, 'threads')),
                    lambda r: f(r, 'bcast_s') + f(r, 'gather_s') + f(r, 'merge_s'),
                    lambda r: p_effective(int(f(r, 'procs'))) * int(f(r, 'threads')))

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.0, 5.8), facecolor=BG)
    x1 = [r[0] / 1e6 for r in m1]
    a1.plot(x1, [r[5] for r in m1], color=C_THEORY, ls=':', marker='o', lw=2.2, ms=4,
            label='Amdahl at p = 14')
    a1.plot(x1, [r[6] for r in m1], color=C_HYB, marker='^', lw=2.4, ms=4,
            label='Amdahl at p_eff = 12 (2 of the 14 ranks idle)')
    a1.plot(x1, [r[7] for r in m1], color=C_MPI, marker='D', lw=2.6, ms=4,
            label='Empirical (measured)')
    style(a1, 'Task 1: 14 MPI processes', 'r_p, r_s and kappa measured again at every n',
          'Problem size n (millions)', 'Speedup relative to one process')
    legend(a1)
    x2 = [r[0] / 1e6 for r in m2]
    a2.plot(x2, [r[5] for r in m2], color=C_THEORY, ls=':', marker='o', lw=2.2, ms=4,
            label='Amdahl at 2 x 7 = 14 workers')
    a2.plot(x2, [r[7] for r in m2], color=C_HYB, marker='v', lw=2.6, ms=4,
            label='Empirical (measured)')
    style(a2, 'Task 2: 2 processes x 7 threads', 'Same method for the hybrid',
          'Problem size n (millions)', 'Speedup relative to one worker')
    legend(a2)
    fig.suptitle('Graph 10  Theoretical against empirical speedup as n grows',
                 fontsize=15, fontweight='bold', color=TEXT, x=0.02, ha='left', y=0.99)
    save(fig, 'graph10_amdahl_vs_n.png')

    with open("amdahl_by_n.csv", "w") as fh:
        fh.write("model,n,r_p,r_s,kappa,workers,S_amdahl,S_amdahl_peff,S_empirical\n")
        for tag, rows in [("task1_mpi", m1), ("task2_hybrid", m2)]:
            for nval, rp, rs, k, p, sa, se, sm in rows:
                fh.write(f"{tag},{nval},{rp:.6f},{rs:.6f},{k:.6f},{p},{sa:.4f},{se:.4f},{sm:.4f}\n")
    print("  wrote amdahl_by_n.csv")
except OSError:
    print("  (phases_by_n_*.csv not found, run run_phases_by_n.py first, skipping graph 10)")

# =====================================================================
# Numbers for the slides
# =====================================================================
with open("amdahl_summary.csv", "w") as fh:
    fh.write("model,r_p,r_s,T_baseline_s\n")
    fh.write(f"task1_mpi,{rp1:.6f},{rs1:.6f},{T1:.6f}\n")
    fh.write(f"task2_hybrid,{rp2:.6f},{rs2:.6f},{T2:.6f}\n")
    fh.write("\nmodel,width,p_eff,kappa,S_amdahl,S_amdahl_peff,S_empirical\n")
    for w, k, t, e, m in zip(p1_w, p1_kap, p1_th, p1_eff, p1_emp):
        fh.write(f"task1_mpi,{w},{p_effective(w):.2f},{k:.6f},{t:.4f},{e:.4f},{m:.4f}\n")
    for l, w, ef, k, t, e, m in zip(lab2, w2, eff2, kap2, th2, the2, emp2):
        fh.write(f"task2_hybrid,{l}({w}),{ef:.2f},{k:.6f},{t:.4f},{e:.4f},{m:.4f}\n")

best_n = max(by_n, key=lambda r: f(r, 'serial_s') / f(r, 'mpi_s'))
best_w = max(by_procs, key=lambda r: f(r, 'serial_s') / f(r, 'mpi_s'))

print("")
print("=" * 62)
print("NUMBERS FOR THE SLIDES")
print("=" * 62)
print(f"Serial baseline at the fixed n:            {serial_fixed:.3f} s")
print(f"Task 1 parallel fraction   r_p:            {rp1:.4f}")
print(f"Task 1 serial fraction     r_s:            {rs1:.4f}")
print(f"Task 1 Amdahl ceiling as p -> inf:         {1.0/rs1:.2f}x")
print(f"Task 1 kappa at p=28 (communication):      {p1_kap[-1]:.5f}")
print(f"Task 2 parallel fraction   r_p:            {rp2:.4f}")
print(f"Task 2 serial fraction     r_s:            {rs2:.4f}")
print(f"Best MPI speedup vs Week 4 serial, over n: {f(best_n,'serial_s')/f(best_n,'mpi_s'):.2f}x at n={int(f(best_n,'n')):,}")
print(f"Best MPI speedup vs serial, over width:    {f(best_w,'serial_s')/f(best_w,'mpi_s'):.2f}x at p={int(f(best_w,'width'))}")
try:
    launch = float(open("launch_overhead.txt").read().strip())
    print(f"mpirun launch + MPI_Init overhead:         {launch:.3f} s (paired, measure_launch.py)")
except OSError:
    print("mpirun launch overhead:                    run measure_launch.py")
print("-" * 62)
print("Imbalance: comp_max/comp_mean against 1/(1-1/d)")
for r in ph1:
    w = int(f(r, 'procs')); d = smallest_odd_factor(w)
    pred = 1.0 if d is None else 1.0 / (1.0 - 1.0 / d)
    print(f"  p={w:3d}  d={str(d) if d else '2^k':>3}  measured {f(r,'comp_s')/f(r,'comp_mean_s'):.2f}  predicted {pred:.2f}")
print("=" * 62)
