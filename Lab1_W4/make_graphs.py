
#!/usr/bin/env python3
####################################################################
# make_graphs.py
# ------------------------------------------------------------------
# FIT3143 Lab #1 Task 4: draws the eight graphs the spec asks for,
# plus one extra showing the two workload distribution comparisons
# from results_extra.csv.
#
# Written by: Erwyna Soo Wen Xin (36555789)
#
# Run: python3 make_graphs.py
####################################################################

import csv
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# One colour per version so they stay the same on every graph
SERIAL  = "#2a78d6"
PTHREAD = "#eb6834"
OMP     = "#1baf7a"
INK     = "#0b0b0b"
INK2    = "#52514e"
MUTED   = "#898781"
GRID    = "#e1e0d9"
AXIS    = "#c3c2b7"
PAPER   = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor":  PAPER,
    "axes.facecolor":    PAPER,
    "savefig.facecolor": PAPER,
    "font.family":       "sans-serif",
    "font.sans-serif":   ["DejaVu Sans"],
    "font.size":         10.5,
    "axes.edgecolor":    AXIS,
    "axes.linewidth":    0.9,
    "axes.labelcolor":   INK2,
    "axes.titlesize":    12.5,
    "axes.titleweight":  "bold",
    "axes.titlecolor":   INK,
    "xtick.color":       MUTED,
    "ytick.color":       MUTED,
    "xtick.labelsize":   9.5,
    "ytick.labelsize":   9.5,
    "grid.color":        GRID,
    "grid.linewidth":    0.8,
    "legend.frameon":    False,
    "legend.fontsize":   10,
    "figure.dpi":        160,
})

OUT = "graphs"
os.makedirs(OUT, exist_ok=True)


def read_csv(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f"{path} has no data rows. Run ./run_benchmarks.sh first.")
    return rows


def column(rows, path, key, cast=float):
    """Read one column, refusing to continue if any cell is blank.

    An earlier version of this script quietly turned blanks into 0.0. That drew
    a flat line at zero instead of failing, so a benchmark run that had not
    actually collected the OpenMP timings still produced graphs that looked
    finished. Blank data is a broken run, so say so and stop."""
    out = []
    for i, r in enumerate(rows, start=2):
        raw = (r.get(key) or "").strip()
        if not raw:
            raise SystemExit(
                f"{path} line {i}: column '{key}' is empty. "
                f"The benchmark run did not collect this series, so the graphs "
                f"would be wrong. Re-run ./run_benchmarks.sh and check it "
                f"finishes without errors.")
        out.append(cast(raw))
    return out


def tidy(ax, xlabel, ylabel):
    ax.grid(True, axis="y")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlabel(xlabel, fontsize=10.5, labelpad=8)
    ax.set_ylabel(ylabel, fontsize=10.5, labelpad=8)


def millions(x, _pos):
    return f"{x / 1e6:g}M"


def label_end(ax, xs, ys, colour, text, dy=0):
    """Put the final value on the end of a line so it can be read off the graph
    without needing the table."""
    ax.annotate(text, xy=(xs[-1], ys[-1]), xytext=(6, dy),
                textcoords="offset points", color=colour, fontsize=9.5,
                fontweight="bold", va="center", ha="left", annotation_clip=False)


def save(fig, name, note=None):
    if note:
        fig.text(0.125, 0.905, note, fontsize=9.5, color=MUTED, ha="left")
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight", pad_inches=0.28)
    plt.close(fig)
    print("  saved", name)


# --- load the results -----------------------------------------------------
BY_N = "results_by_n.csv"
by_n   = read_csv(BY_N)
ns     = column(by_n, BY_N, "n", int)
s_n    = column(by_n, BY_N, "serial_s")
p_n    = column(by_n, BY_N, "pthread_s")
o_n    = column(by_n, BY_N, "omp_s")
sp_p_n = [s / p for s, p in zip(s_n, p_n)]
sp_o_n = [s / o for s, o in zip(s_n, o_n)]

BY_T = "results_by_threads.csv"
by_t   = read_csv(BY_T)
ts     = column(by_t, BY_T, "threads", int)
s_ref  = float(by_t[0]["serial_s"])
p_t    = column(by_t, BY_T, "pthread_s")
o_t    = column(by_t, BY_T, "omp_s")
sp_p_t = [s_ref / p for p in p_t]
sp_o_t = [s_ref / o for o in o_t]

CORES = int(os.environ.get("CORES", max(ts) // 2 if max(ts) > 1 else 1))
N_FIXED = int(os.environ.get("N_FIXED", 30000000))
FIXED_LABEL = f"n held at {N_FIXED:,}."
print(f"loaded {len(ns)} values of n and {len(ts)} thread counts, cores = {CORES}")


# --- Graph 1: run time serial vs POSIX Threads, increasing n --------------
fig, ax = plt.subplots(figsize=(7.2, 4.3))
ax.plot(ns, s_n, color=SERIAL,  lw=2, marker="o", ms=3.5, label="Serial (Task 1)")
ax.plot(ns, p_n, color=PTHREAD, lw=2, marker="o", ms=3.5, label="POSIX Threads (Task 2)")
label_end(ax, ns, s_n, SERIAL,  f"{s_n[-1]:.1f}s", dy=5)
label_end(ax, ns, p_n, PTHREAD, f"{p_n[-1]:.1f}s", dy=-5)
tidy(ax, "n (search limit)", "Computation time (seconds)")
ax.xaxis.set_major_formatter(FuncFormatter(millions))
ax.set_title("Graph 1: Run time, serial vs POSIX Threads, increasing n", pad=26)
ax.legend(loc="upper left", ncols=2, bbox_to_anchor=(0, 1.02))
save(fig, "graph1_runtime_serial_vs_pthread_by_n.png", f"{CORES} threads. Lower is better.")

# --- Graph 2: speedup of POSIX Threads, increasing n ----------------------
fig, ax = plt.subplots(figsize=(7.2, 4.3))
ax.axhline(1.0, color=AXIS, lw=1)
ax.axhline(CORES, color=MUTED, lw=1.2, ls="--")
ax.annotate(f"ideal speedup ({CORES}x)", xy=(ns[-1], CORES), xytext=(-2, 9),
            textcoords="offset points", color=MUTED, fontsize=9, ha="right")
ax.plot(ns, sp_p_n, color=PTHREAD, lw=2, marker="o", ms=3.5)
label_end(ax, ns, sp_p_n, PTHREAD, f"{sp_p_n[-1]:.2f}x")
tidy(ax, "n (search limit)", "Speedup over serial")
ax.xaxis.set_major_formatter(FuncFormatter(millions))
ax.set_ylim(0, max(CORES * 1.25, max(sp_p_n) * 1.2))
ax.set_title("Graph 2: Speedup of POSIX Threads, increasing n", pad=26)
save(fig, "graph2_speedup_pthread_by_n.png",
     f"{CORES} threads. Speedup = serial time divided by parallel time.")

# --- Graph 3: run time serial vs POSIX Threads, increasing threads --------
fig, ax = plt.subplots(figsize=(7.2, 4.3))
ax.plot(ts, [s_ref] * len(ts), color=SERIAL, lw=2, label="Serial (Task 1), one thread")
ax.plot(ts, p_t, color=PTHREAD, lw=2, marker="o", ms=4.5, label="POSIX Threads (Task 2)")
ax.axvline(CORES, color=MUTED, lw=1.2, ls="--")
ax.annotate(f"{CORES} cores", xy=(CORES, s_ref * 0.06), xytext=(6, 0),
            textcoords="offset points", color=MUTED, fontsize=9)
label_end(ax, ts, [s_ref] * len(ts), SERIAL,  f"{s_ref:.1f}s", dy=5)
label_end(ax, ts, p_t, PTHREAD, f"{p_t[-1]:.1f}s", dy=-5)
tidy(ax, "Number of threads", "Computation time (seconds)")
ax.set_xticks(ts)
ax.set_ylim(0, s_ref * 1.15)
ax.set_title("Graph 3: Run time, serial vs POSIX Threads, increasing threads", pad=26)
ax.legend(loc="upper right", bbox_to_anchor=(1, 1.02))
save(fig, "graph3_runtime_serial_vs_pthread_by_threads.png",
     f"{FIXED_LABEL} Lower is better.")

# --- Graph 4: speedup of POSIX Threads, increasing threads ---------------
fig, ax = plt.subplots(figsize=(7.2, 4.3))
ax.plot(ts, ts, color=MUTED, lw=1.2, ls="--")
ax.annotate("ideal speedup", xy=(ts[len(ts)//2], ts[len(ts)//2]), xytext=(4, -12),
            textcoords="offset points", color=MUTED, fontsize=9)
ax.axvline(CORES, color=AXIS, lw=1.2)
ax.annotate(f"{CORES} cores", xy=(CORES, 0.15), xytext=(6, 0),
            textcoords="offset points", color=MUTED, fontsize=9)
ax.plot(ts, sp_p_t, color=PTHREAD, lw=2, marker="o", ms=4.5)
label_end(ax, ts, sp_p_t, PTHREAD, f"{sp_p_t[-1]:.2f}x")
tidy(ax, "Number of threads", "Speedup over serial")
ax.set_xticks(ts)
ax.set_ylim(0, max(ts) * 1.08)
ax.set_title("Graph 4: Speedup of POSIX Threads, increasing threads", pad=26)
save(fig, "graph4_speedup_pthread_by_threads.png",
     f"{FIXED_LABEL} Speedup stops improving once threads pass the core count.")

# --- Graph 5: run time serial vs OpenMP, increasing n --------------------
fig, ax = plt.subplots(figsize=(7.2, 4.3))
ax.plot(ns, s_n, color=SERIAL, lw=2, marker="o", ms=3.5, label="Serial (Task 1)")
ax.plot(ns, o_n, color=OMP,    lw=2, marker="o", ms=3.5, label="OpenMP (Task 3)")
label_end(ax, ns, s_n, SERIAL, f"{s_n[-1]:.1f}s", dy=5)
label_end(ax, ns, o_n, OMP,    f"{o_n[-1]:.1f}s", dy=-5)
tidy(ax, "n (search limit)", "Computation time (seconds)")
ax.xaxis.set_major_formatter(FuncFormatter(millions))
ax.set_title("Graph 5: Run time, serial vs OpenMP, increasing n", pad=26)
ax.legend(loc="upper left", ncols=2, bbox_to_anchor=(0, 1.02))
save(fig, "graph5_runtime_serial_vs_omp_by_n.png", f"{CORES} threads. Lower is better.")

# --- Graph 6: speedup of OpenMP, increasing n ----------------------------
fig, ax = plt.subplots(figsize=(7.2, 4.3))
ax.axhline(1.0, color=AXIS, lw=1)
ax.axhline(CORES, color=MUTED, lw=1.2, ls="--")
ax.annotate(f"ideal speedup ({CORES}x)", xy=(ns[-1], CORES), xytext=(-2, 9),
            textcoords="offset points", color=MUTED, fontsize=9, ha="right")
ax.plot(ns, sp_o_n, color=OMP, lw=2, marker="o", ms=3.5)
label_end(ax, ns, sp_o_n, OMP, f"{sp_o_n[-1]:.2f}x")
tidy(ax, "n (search limit)", "Speedup over serial")
ax.xaxis.set_major_formatter(FuncFormatter(millions))
ax.set_ylim(0, max(CORES * 1.25, max(sp_o_n) * 1.2))
ax.set_title("Graph 6: Speedup of OpenMP, increasing n", pad=26)
save(fig, "graph6_speedup_omp_by_n.png",
     f"{CORES} threads. Speedup = serial time divided by parallel time.")

# --- Graph 7: POSIX Threads vs OpenMP, increasing n ----------------------
fig, ax = plt.subplots(figsize=(7.2, 4.3))
ax.plot(ns, p_n, color=PTHREAD, lw=2, marker="o", ms=3.5, label="POSIX Threads (Task 2)")
ax.plot(ns, o_n, color=OMP,     lw=2, marker="o", ms=3.5, label="OpenMP (Task 3)")
label_end(ax, ns, p_n, PTHREAD, f"{p_n[-1]:.2f}s", dy=-11)
label_end(ax, ns, o_n, OMP,     f"{o_n[-1]:.2f}s", dy=11)
tidy(ax, "n (search limit)", "Computation time (seconds)")
ax.xaxis.set_major_formatter(FuncFormatter(millions))
ax.set_title("Graph 7: Run time, POSIX Threads vs OpenMP, increasing n", pad=26)
ax.legend(loc="upper left", ncols=2, bbox_to_anchor=(0, 1.02))
save(fig, "graph7_runtime_pthread_vs_omp_by_n.png", f"{CORES} threads. Lower is better.")

# --- Graph 8: POSIX Threads vs OpenMP, increasing threads ---------------
fig, ax = plt.subplots(figsize=(7.2, 4.3))
ax.plot(ts, p_t, color=PTHREAD, lw=2, marker="o", ms=4.5, label="POSIX Threads (Task 2)")
ax.plot(ts, o_t, color=OMP,     lw=2, marker="o", ms=4.5, label="OpenMP (Task 3)")
ax.axvline(CORES, color=MUTED, lw=1.2, ls="--")
ax.annotate(f"{CORES} cores", xy=(CORES, min(min(p_t), min(o_t)) * 0.55),
            xytext=(6, 0), textcoords="offset points", color=MUTED, fontsize=9)
ax.set_ylim(0, max(max(p_t), max(o_t)) * 1.12)
label_end(ax, ts, p_t, PTHREAD, f"{p_t[-1]:.2f}s", dy=-11)
label_end(ax, ts, o_t, OMP,     f"{o_t[-1]:.2f}s", dy=11)
tidy(ax, "Number of threads", "Computation time (seconds)")
ax.set_xticks(ts)
ax.set_title("Graph 8: Run time, POSIX Threads vs OpenMP, increasing threads", pad=26)
ax.legend(loc="upper right", bbox_to_anchor=(1, 1.02))
save(fig, "graph8_runtime_pthread_vs_omp_by_threads.png",
     f"{FIXED_LABEL} Lower is better.")

# --- Graph 9 (extra): the two workload distribution comparisons ---------
if os.path.exists("results_extra.csv"):
    rows     = read_csv("results_extra.csv")
    labels   = [r["label"] for r in rows]
    times    = column(rows, "results_extra.csv", "time_s")
    base     = float(rows[0]["serial_s"])
    speeds   = [base / t for t in times]
    # our own two versions in orange, the OpenMP schedules in green
    colours = [PTHREAD if lb.startswith("pthread") else OMP for lb in labels]
    pretty  = [lb.replace("pthread ", "Task 2\n").replace("omp ", "Task 3\n")
               for lb in labels]

    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    bars = ax.bar(range(len(speeds)), speeds, color=colours, width=0.62, zorder=3)
    ax.axhline(1.0, color=AXIS, lw=1)
    ax.annotate("no speedup", xy=(len(speeds) - 0.4, 1.0), xytext=(0, 6),
                textcoords="offset points", color=MUTED, fontsize=9, ha="right")
    for b, sp in zip(bars, speeds):
        ax.annotate(f"{sp:.2f}x", xy=(b.get_x() + b.get_width() / 2, sp),
                    xytext=(0, 5), textcoords="offset points", ha="center",
                    fontsize=10, fontweight="bold", color=INK2)
    ax.set_xticks(range(len(pretty)))
    ax.set_xticklabels(pretty, fontsize=9.5)
    tidy(ax, "", "Speedup over serial")
    ax.set_ylim(0, max(speeds) * 1.28)
    ax.set_title("Extra: how we shared the work out, measured", pad=26)
    save(fig, "graph9_workload_distribution.png",
         f"n = {N_FIXED:,}, {CORES} threads. Same search every time, only the sharing changes.")

print("\nAll graphs are in the graphs folder.")
