#!/usr/bin/env python3
"""
make_graphs.py  (FIT3143 Lab 3, Task 3)

Turns results/*.csv into the Task 3 graphs and summary tables.

  graph1_grid_all_types.png     every message type's delay vs grid size (32 grids)
  graph2_line_all_types.png     every message type's delay vs line size (32 lines)
  graph3_grid_vs_line.png       the two topologies on the same axes
  graph4_bs_versions.png        base station versions 1/2/3 under bursts
  graph5_node_versions_cost.png messages per node-cycle and blocking, node v1/v2/v3
  graph6_window.png             base station answers vs predefined period
  graph7_poll.png               poll interval: latency vs CPU
  per_type/<grid|line>_<type>.png   one graph per message type (appendix)
  results/summary_*.csv         the numbers behind every graph, averaged over seeds

Every point is the mean of 3 seeds; the shaded band is min to max of those 3.

Written by: Erwyna Soo Wen Xin (36555789)
Team: Erwyna Soo Wen Xin (36555789), Taabish Farooq Bhat (35473932)
"""
import csv
import os
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "graphs")
PER = os.path.join(OUT, "per_type")
os.makedirs(PER, exist_ok=True)

BG, PANEL, TEXT, SUB, GRIDC = "#1B1838", "#221F47", "#FFFFFF", "#B3AFD6", "#3A3670"
VCOL = {"1": "#FF7A7A", "2": "#2ED3D3", "3": "#FFC928"}
VNAME_NODE = {"1": "node v1 blocking", "2": "node v2 nonblocking", "3": "node v3 collective"}
VNAME_BS = {"1": "BS v1 probe + blocking send", "2": "BS v2 Irecv(ANY_SOURCE)", "3": "BS v3 persistent + Testsome"}
CORES = 14   # this laptop; past 13 nodes there are more processes than cores

TYPES = [("req", "Neighbour request (one way)"), ("reply", "Neighbour reply (one way)"),
         ("query_rtt", "Neighbour exchange round trip"), ("nbr_collective", "MPI_Neighbor_allgather (v3)"),
         ("report", "Report to base station (one way)"), ("response", "Base station answer (one way)"),
         ("report_rtt", "Report round trip"), ("terminate", "Termination message (one way)")]

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.facecolor": PANEL, "figure.facecolor": BG,
                     "axes.edgecolor": GRIDC, "axes.labelcolor": TEXT, "xtick.color": SUB,
                     "ytick.color": SUB, "text.color": TEXT, "axes.grid": True, "grid.color": GRIDC,
                     "grid.linewidth": 0.6, "legend.facecolor": PANEL, "legend.edgecolor": GRIDC,
                     "legend.labelcolor": TEXT})


def load(name):
    p = os.path.join(RES, name)
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []


def agg(rows, key, col, by="node_v"):
    """{version: [(x, mean, lo, hi, n)]} for column col, grouped by x = key(row)."""
    g = defaultdict(list)
    for r in rows:
        v = float(r[col])
        if col.endswith("_mean_us") and float(r[col.replace("_mean_us", "_n")]) == 0:
            continue                          # no message of this type in that run
        g[(r[by], key(r))].append(v)
    out = defaultdict(list)
    for (ver, x), vals in sorted(g.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        out[ver].append((x, sum(vals) / len(vals), min(vals), max(vals), len(vals)))
    return out


def plot_series(ax, series, names, unit=1.0, marker="o"):
    for ver in sorted(series):
        pts = series[ver]
        xs = [p[0] for p in pts]
        ax.fill_between(xs, [p[2] / unit for p in pts], [p[3] / unit for p in pts],
                        color=VCOL[ver], alpha=0.18, lw=0)
        ax.plot(xs, [p[1] / unit for p in pts], marker=marker, ms=3.2, lw=1.8, color=VCOL[ver], label=names[ver])


def style(ax, title, xlabel, ylabel, cores=True):
    ax.set_title(title, fontsize=11, color=TEXT, loc="left", fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=9.5)
    ax.set_ylabel(ylabel, fontsize=9.5)
    if cores:
        ax.axvline(CORES - 0.5, color=SUB, lw=0.9, ls=":")


def header(fig, title, sub):
    fig.text(0.012, 0.985, title, fontsize=16, fontweight="bold", color="#FFC928", va="top")
    fig.text(0.012, 0.915, sub, fontsize=10, color=SUB, va="top")


def nodes(r):
    return int(r["nodes"])


def save(fig, path):
    fig.savefig(path, facecolor=BG, dpi=200)
    plt.close(fig)
    print("wrote", path)


def all_types(rows, tag, fname, label):
    fig, axes = plt.subplots(2, 4, figsize=(17, 8.6))
    fig.subplots_adjust(left=0.05, right=0.99, top=0.84, bottom=0.08, wspace=0.28, hspace=0.42)
    header(fig, f"Communication delay of every message type vs {label} size",
           f"{len(set(r['nodes'] for r in rows))} {label} sizes x node v1/v2/v3 x 3 seeds, base station v3, "
           "uniform heavy load (75% ports busy). Dotted line: more MPI processes than the laptop's 14 cores.")
    for ax, (t, title) in zip(axes.flat, TYPES):
        s = agg(rows, nodes, f"{t}_mean_us")
        plot_series(ax, s, VNAME_NODE, unit=1000.0)
        style(ax, title, "charging nodes", "mean delay (ms)")
    axes.flat[0].legend(fontsize=8.5, loc="upper left")
    save(fig, os.path.join(OUT, fname))
    # one graph per type, for the appendix
    for t, title in TYPES:
        fig, ax = plt.subplots(figsize=(8, 4.6))
        fig.subplots_adjust(left=0.1, right=0.98, top=0.86, bottom=0.13)
        s = agg(rows, nodes, f"{t}_mean_us")
        if not s:
            plt.close(fig)
            continue
        plot_series(ax, s, VNAME_NODE, unit=1000.0)
        mx = agg(rows, nodes, f"{t}_max_us")
        for ver in sorted(mx):
            ax.plot([p[0] for p in mx[ver]], [p[1] / 1000 for p in mx[ver]], ls="--", lw=0.9, color=VCOL[ver], alpha=0.7)
        style(ax, f"{title} vs {label} size", "charging nodes", "delay (ms)  solid = mean, dashed = worst")
        ax.legend(fontsize=8)
        save(fig, os.path.join(PER, f"{tag}_{t}.png"))


def grid_vs_line(grid, line):
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.6))
    fig.subplots_adjust(left=0.05, right=0.99, top=0.8, bottom=0.12, wspace=0.25)
    header(fig, "2D grid vs line topology, same number of nodes (node v2, base station v3)",
           "A line node has at most 2 neighbours instead of 4, so it sends fewer requests, but more of its"
           " neighbourhood is full at once, so it goes to the base station more often.")
    for ax, (col, title, unit, yl) in zip(axes, [("query_rtt_mean_us", "Neighbour exchange round trip", 1000, "ms"),
                                                 ("report_rtt_mean_us", "Report round trip", 1000, "ms"),
                                                 ("reports", "Reports per run (load on the base station)", 1, "reports")]):
        for rows, name, c in ((grid, "2D grid", "#2ED3D3"), (line, "line", "#FF7A7A")):
            s = agg([r for r in rows if r["node_v"] == "2"], nodes, col)
            pts = s.get("2", [])
            if not pts:
                continue
            ax.fill_between([p[0] for p in pts], [p[2] / unit for p in pts], [p[3] / unit for p in pts], color=c, alpha=0.18, lw=0)
            ax.plot([p[0] for p in pts], [p[1] / unit for p in pts], marker="o", ms=3, lw=1.8, color=c, label=name)
        style(ax, title, "charging nodes", yl)
        ax.legend(fontsize=9)
    save(fig, os.path.join(OUT, "graph3_grid_vs_line.png"))


def bs_versions(rows):
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.6))
    fig.subplots_adjust(left=0.05, right=0.99, top=0.8, bottom=0.12, wspace=0.25)
    header(fig, "Base station versions under bursts (saturated load: every node reports every few cycles)",
           "6 grid sizes x 3 base station versions x 3 seeds, node v2. Lower is better.")
    for ax, (col, title, unit, yl, logy) in zip(axes, [
            ("report_mean_us", "Report delay, one way (mean)", 1000, "ms", False),
            ("report_max_us", "Report delay, one way (worst)", 1000, "ms", True),
            ("bs_process_mean_us", "Base station time per report", 1, "microseconds", False)]):
        s = agg(rows, nodes, col, by="bs_v")
        plot_series(ax, s, VNAME_BS, unit=unit, marker="s")
        style(ax, title, "charging nodes", yl)
        if logy:
            ax.set_yscale("log")
    axes[0].legend(fontsize=8.5)
    save(fig, os.path.join(OUT, "graph4_bs_versions.png"))


def node_cost(grid):
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.6))
    fig.subplots_adjust(left=0.05, right=0.99, top=0.8, bottom=0.12, wspace=0.25)
    header(fig, "What each node version costs (32 grid sizes, 3 seeds)",
           "v3 needs no request when congested, but pays a collective every cycle; v1 is the only one that blocks.")
    per_cycle = [dict(r, mpc=str(float(r["msgs"]) / max(1.0, float(r["cycles"])))) for r in grid]
    s = agg(per_cycle, nodes, "mpc")
    plot_series(axes[0], s, VNAME_NODE)
    style(axes[0], "Messages per node-cycle (whole system)", "charging nodes", "messages / node / cycle")
    s = agg(grid, nodes, "blocked_s_per_node")
    plot_series(axes[1], s, VNAME_NODE, unit=1e-3)
    style(axes[1], "Comms thread blocked inside MPI", "charging nodes", "ms per node per 3 s run")
    s = agg(grid, nodes, "late_max_ms")
    plot_series(axes[2], s, VNAME_NODE)
    style(axes[2], "Worst cycle start lateness", "charging nodes", "ms")
    axes[0].legend(fontsize=8.5)
    save(fig, os.path.join(OUT, "graph5_node_versions_cost.png"))


def window(rows):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.8, bottom=0.13, wspace=0.25)
    header(fig, "Base station predefined period (window W) on a 7x7 hotspot grid",
           "Longer W = more past reports count, so more answers become 'no nodes nearby'. 3 seeds per point.")
    g = defaultdict(list)
    for r in rows:
        rep = max(1, int(r["reports"]))
        g[float(r["window_cycles"])].append((int(r["resp_cand"]) / rep * 100, int(r["resp_none_nearby"]) / rep * 100,
                                             int(r["resp_none_anywhere"]) / rep * 100, int(r["reports"])))
    ws = sorted(g)
    for i, (name, c) in enumerate([("candidates sent", "#2BD99F"), ("none nearby", "#FF7A7A"), ("none anywhere", "#B3AFD6")]):
        axes[0].plot(ws, [sum(v[i] for v in g[w]) / len(g[w]) for w in ws], marker="o", color=c, lw=2, label=name)
    style(axes[0], "Share of base station answers", "window W (cycles of 10 simulated s)", "% of reports", cores=False)
    axes[0].set_xscale("log")
    axes[0].legend(fontsize=9)
    axes[1].plot(ws, [sum(v[3] for v in g[w]) / len(g[w]) for w in ws], marker="o", color="#FFC928", lw=2)
    style(axes[1], "Reports per run", "window W (cycles)", "reports", cores=False)
    axes[1].set_xscale("log")
    save(fig, os.path.join(OUT, "graph6_window.png"))


def poll(rows, cpu_rows):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.8, bottom=0.13, wspace=0.25)
    header(fig, "Polling interval: the latency we buy with CPU (4x4 grid, base station v3)",
           "poll_us is how long a rank sleeps between MPI_Iprobe / MPI_Test rounds. 3 seeds per point.")
    # x axis is the poll interval, which is not in the base station CSV, so pair rows with the CPU log in order
    for v in ("1", "2"):
        vr = [r for r in cpu_rows if r["node_v"] == v]
        xs = sorted({int(r["poll_us"]) for r in vr})
        rr = [r for r in rows if r["node_v"] == v]
        if len(rr) != len(vr):
            continue
        pairs = list(zip(vr, rr))
        lat = [sum(float(b["report_rtt_mean_us"]) for a, b in pairs if int(a["poll_us"]) == x) / 3 / 1000 for x in xs]
        qrt = [sum(float(b["query_rtt_mean_us"]) for a, b in pairs if int(a["poll_us"]) == x) / 3 / 1000 for x in xs]
        cpu = [sum(float(a["cpu_s"]) for a, b in pairs if int(a["poll_us"]) == x) / 3 for x in xs]
        xs_plot = [max(x, 5) for x in xs]
        axes[0].plot(xs_plot, qrt, marker="o", color=VCOL[v], lw=2, label=f"{VNAME_NODE[v]}: query round trip")
        axes[0].plot(xs_plot, lat, marker="s", color=VCOL[v], lw=1.4, ls="--", label=f"{VNAME_NODE[v]}: report round trip")
        axes[1].plot(xs_plot, cpu, marker="o", color=VCOL[v], lw=2, label=VNAME_NODE[v])
    style(axes[0], "Delay", "poll interval (us, 0 plotted at 5)", "ms", cores=False)
    style(axes[1], "CPU time for the whole 3 s run (17 processes)", "poll interval (us)", "CPU seconds", cores=False)
    for ax in axes:
        ax.set_xscale("log")
        ax.legend(fontsize=8)
    save(fig, os.path.join(OUT, "graph7_poll.png"))


def summary(rows, name, by="node_v"):
    cols = ["req", "reply", "query_rtt", "nbr_collective", "report", "response", "report_rtt", "terminate", "bs_process"]
    g = defaultdict(list)
    for r in rows:
        g[(int(r["rows"]), int(r["cols"]), r[by])].append(r)
    p = os.path.join(RES, name)
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rows", "cols", "nodes", by, "seeds", "reports", "msgs"] + [f"{c}_mean_us" for c in cols] + [f"{c}_max_us" for c in cols])
        for (rr, cc, v), rs in sorted(g.items(), key=lambda kv: (kv[0][0] * kv[0][1], kv[0])):
            def m(col, f=max):
                vals = [float(x[col]) for x in rs if float(x[col.rsplit("_", 2)[0] + "_n"]) > 0] if col.endswith("_us") else [float(x[col]) for x in rs]
                return (sum(vals) / len(vals)) if (vals and f is None) else (f(vals) if vals else 0)
            w.writerow([rr, cc, rr * cc, v, len(rs), f"{m('reports', None):.1f}", f"{m('msgs', None):.0f}"]
                       + [f"{m(c + '_mean_us', None):.1f}" for c in cols] + [f"{m(c + '_max_us'):.1f}" for c in cols])
    print("wrote", p)


if __name__ == "__main__":
    grid, line = load("e1_grid.csv"), load("e2_line.csv")
    if grid:
        all_types(grid, "grid", "graph1_grid_all_types.png", "grid")
        node_cost(grid)
        summary(grid, "summary_e1_grid.csv")
    if line:
        all_types(line, "line", "graph2_line_all_types.png", "line")
        summary(line, "summary_e2_line.csv")
    if grid and line:
        grid_vs_line(grid, line)
    if load("e3_bs_versions.csv"):
        bs_versions(load("e3_bs_versions.csv"))
        summary(load("e3_bs_versions.csv"), "summary_e3_bs_versions.csv", by="bs_v")
    if load("e4_window.csv"):
        window(load("e4_window.csv"))
    if load("e5_poll.csv") and load("e5_poll_cpu.csv"):
        poll(load("e5_poll.csv"), load("e5_poll_cpu.csv"))
