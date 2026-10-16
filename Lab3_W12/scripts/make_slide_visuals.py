#!/usr/bin/env python3
"""
make_slide_visuals.py  (FIT3143 Lab 3, Task 4 slides)

Every picture on the deck, drawn at the exact pixel size it is placed at on
a 1920 x 1080 slide, so the text inside it is never below 30 px on screen.

How the 30 px rule is kept: a figure is (W/100) x (H/100) inches for a slot
of W x H slide pixels, so 1 inch = 100 slide px, and 1 pt = 100/72 px. The
smallest font used anywhere is MIN = 22 pt = 30.6 px. Saved at dpi 200 so it
stays sharp on a projector.

  slides/v01_architecture.png ... v05_shutdown.png   diagrams
  slides/c01_topology.png ...                       code cards (real line numbers)
  slides/g01_node_versions.png ...                  graphs from results/*.csv
  slides/a01_... appendix graphs

Written by: Erwyna Soo Wen Xin (36555789)
Team: Erwyna Soo Wen Xin (36555789), Taabish Farooq Bhat (35473932)
"""
import csv
import os
import sys
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "graphs", "slides")
RES = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

MIN = 22          # pt; 22 pt = 30.6 px on the slide
MID = 25
BIG = 28
NAVY, PANEL, WHITE, SUB = "#1C1333", "#2E2856", "#FFFFFF", "#C9C5EA"
YEL, CYAN, CORAL, GREEN, GREY = "#FFC928", "#2ED3D3", "#FF7A7A", "#2BD99F", "#6E6A9E"
VCOL = {"1": CORAL, "2": CYAN, "3": YEL}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": MIN})


def px(v):
    return v / 100.0


def canvas(w, h):
    fig = plt.figure(figsize=(px(w), px(h)), dpi=100, facecolor=NAVY)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, fc=PANEL, ec=None, lw=3, r=18, z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec or fc, lw=lw, zorder=z))


def arrow(ax, x1, y1, x2, y2, c=WHITE, lw=3, style="-|>", ls="-", ms=30, rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=ms, color=c,
                                 lw=lw, linestyle=ls, zorder=3, connectionstyle=f"arc3,rad={rad}"))


def t(ax, x, y, s, size=MIN, c=WHITE, ha="left", va="center", bold=False, mono=False, z=5):
    ax.text(x, y, s, fontsize=size, color=c, ha=ha, va=va, zorder=z,
            fontweight="bold" if bold else "normal", family="DejaVu Sans Mono" if mono else "DejaVu Sans")


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("wrote", p)


# ===================================================================== diagrams
def v01_architecture():
    W, H = 1000, 800
    fig, ax = canvas(W, H)
    s, g = 170, 70
    x0, y0 = 50, 120
    pos = {}
    for r in range(3):
        for c in range(3):
            pos[(r, c)] = (x0 + c * (s + g), y0 + (2 - r) * (s + g))
    for (r, c), (x, y) in pos.items():
        if c < 2:
            ax.plot([x + s, x + s + g], [y + s / 2] * 2, color=CYAN, lw=6, zorder=1)
        if r < 2:
            ax.plot([x + s / 2] * 2, [y, y - g], color=CYAN, lw=6, zorder=1)
    for (r, c), (x, y) in pos.items():
        n = r * 3 + c
        box(ax, x, y, s, s, fc=PANEL, ec=YEL, lw=4)
        t(ax, x + s / 2, y + s - 42, f"Node {n}", MID, ha="center", bold=True)
        t(ax, x + s / 2, y + s - 82, f"({r},{c})", MIN, SUB, ha="center")
        for p in range(6):
            ax.add_patch(Rectangle((x + 16 + p * 24, y + 18), 18, 50,
                                   fc=CORAL if (p + n) % 3 else GREEN, ec="none", zorder=4))
    bx, by = 790, 330
    box(ax, bx, by, 190, 200, fc=YEL)
    t(ax, bx + 95, by + 140, "Base", MID, NAVY, ha="center", bold=True)
    t(ax, bx + 95, by + 100, "station", MID, NAVY, ha="center", bold=True)
    t(ax, bx + 95, by + 45, "rank 9", MIN, NAVY, ha="center")
    for r in range(3):
        x, y = pos[(r, 2)]
        arrow(ax, x + s + 6, y + s / 2, bx - 6, by + 100, c=YEL, lw=3, style="<|-|>", ls="--")
    t(ax, 50, 60, "grid links = MPI_Cart_shift neighbours", MIN, CYAN)
    t(ax, 50, 22, "dashed = any node to base station", MIN, YEL)
    save(fig, "v01_architecture.png")


def v02_node():
    W, H = 1000, 800
    fig, ax = canvas(W, H)
    box(ax, 40, 470, 300, 280, fc=YEL)
    t(ax, 190, 700, "Thread 0", BIG, NAVY, ha="center", bold=True)
    t(ax, 190, 640, "comms", MID, NAVY, ha="center")
    t(ax, 190, 570, "only MPI", MIN, NAVY, ha="center")
    t(ax, 190, 520, "caller", MIN, NAVY, ha="center")
    box(ax, 390, 470, 570, 280, fc=PANEL, ec=CYAN, lw=4)
    t(ax, 675, 705, "shared array", BIG, CYAN, ha="center", bold=True)
    for p in range(6):
        x = 420 + p * 88
        busy = p % 3 != 0
        ax.add_patch(Rectangle((x, 545), 72, 90, fc=CORAL if busy else GREEN, ec="none", zorder=4))
        t(ax, x + 36, 590, "1" if busy else "0", MID, NAVY, ha="center", bold=True)
        t(ax, x + 36, 510, f"p{p}", MIN, SUB, ha="center")
    arrow(ax, 340, 610, 390, 610, c=CYAN, style="<|-|>", lw=4)
    for p in range(6):
        x = 40 + p * 155
        box(ax, x, 170, 140, 170, fc=GREEN)
        t(ax, x + 70, 290, f"T{p + 1}", MID, NAVY, ha="center", bold=True)
        t(ax, x + 70, 230, f"port {p}", MIN, NAVY, ha="center")
        arrow(ax, x + 70, 345, 420 + p * 88 + 36, 470, c=GREEN, lw=3, ms=22)
    t(ax, 500, 100, "1 = in use, 0 = free", MIN, SUB, ha="center")
    t(ax, 500, 45, "each port writes ONLY its own slot", MIN, WHITE, ha="center", bold=True)
    save(fig, "v02_node.png")


def v03_sequence():
    W, H = 1000, 800
    fig, ax = canvas(W, H)
    cols = {"N": 150, "NB": 500, "BS": 850}
    names = {"N": "Full node", "NB": "Neighbours", "BS": "Base station"}
    for k, x in cols.items():
        box(ax, x - 130, 700, 260, 80, fc=YEL if k == "BS" else PANEL, ec=YEL, lw=3)
        t(ax, x, 740, names[k], MIN, NAVY if k == "BS" else WHITE, ha="center", bold=True)
        ax.plot([x, x], [30, 700], color=GREY, lw=2, ls=":", zorder=1)

    def msg(y, a, b, label, c):
        arrow(ax, cols[a], y, cols[b], y, c=c, lw=4)
        t(ax, (cols[a] + cols[b]) / 2, y + 30, label, MIN, c, ha="center", bold=True)

    msg(610, "N", "NB", "1  REQ x4", CYAN)
    msg(500, "NB", "N", "2  REPLY x4", CYAN)
    box(ax, 30, 335, 470, 105, fc=PANEL, ec=GREEN, lw=3)
    t(ax, 50, 410, "neighbour has room?", MIN, GREEN, bold=True)
    t(ax, 50, 365, "yes: send EVs there, done", MIN)
    msg(250, "N", "BS", "3  all full: REPORT (1 msg)", YEL)
    msg(110, "BS", "N", "4  RESPONSE", YEL)
    save(fig, "v03_sequence.png")


def v04_rule():
    W, H = 1000, 800
    fig, ax = canvas(W, H)
    s, g, x0, y0 = 190, 25, 40, 110
    for r in range(3):
        for c in range(3):
            n = r * 3 + c
            x, y = x0 + c * (s + g), y0 + (2 - r) * (s + g)
            col = YEL if n == 0 else CORAL if n in (1, 3) else GREEN if n in (2, 4, 6) else PANEL
            box(ax, x, y, s, s, fc=col)
            t(ax, x + s / 2, y + s / 2, str(n), 40, NAVY if col != PANEL else WHITE, ha="center", bold=True)
    lx = 720
    for i, (c, a, b) in enumerate([(YEL, "0", "reports"), (CORAL, "1, 3", "neighbours"),
                                   (GREEN, "2, 4, 6", "2 hop ring")]):
        y = 640 - i * 150
        ax.add_patch(Rectangle((lx, y - 25), 50, 50, fc=c, ec="none", zorder=4))
        t(ax, lx + 70, y + 15, a, MID, WHITE, bold=True)
        t(ax, lx + 70, y - 28, b, MIN, SUB)
    t(ax, 40, 50, "node 0 is full and reports to the base station", MIN, SUB)
    save(fig, "v04_rule.png")


def v05_shutdown():
    W, H = 1740, 300
    fig, ax = canvas(W, H)
    steps = [("1  TERMINATE", "BS -> all nodes"), ("2  finish", "own query/report"),
             ("3  ACK", "node -> BS"), ("4  SHUTDOWN", "after all n ACKs")]
    for i, (a, b) in enumerate(steps):
        x = 20 + i * 435
        box(ax, x, 40, 380, 220, fc=CORAL if i in (0, 3) else PANEL, ec=CORAL, lw=4)
        t(ax, x + 190, 185, a, BIG, NAVY if i in (0, 3) else CORAL, ha="center", bold=True)
        t(ax, x + 190, 105, b, MIN, NAVY if i in (0, 3) else WHITE, ha="center")
        if i < 3:
            arrow(ax, x + 383, 150, x + 452, 150, c=CORAL, lw=5)
    save(fig, "v05_shutdown.png")


# =================================================================== code cards
def grab(fname, start, end, keep=None):
    lines = open(os.path.join(ROOT, fname)).read().split("\n")
    i0 = next(i for i, l in enumerate(lines) if start in l)
    i1 = next(i for i in range(i0, len(lines)) if end in lines[i])
    out = []
    for i in range(i0, i1 + 1):
        s = lines[i].strip()
        if not s or s.startswith("//") or s.startswith("/*") or s.startswith("*"):
            continue
        if keep and not any(k in lines[i] for k in keep):
            continue
        txt = lines[i].rstrip()
        if "//" in txt and not s.startswith("#"):
            txt = txt[:txt.index("//")].rstrip()
        out.append((i + 1, txt))
    return out


def code_card(name, caption, rows, W):
    """W = slot width in slide px. Font MIN pt mono: about 18.4 px per char."""
    rows = [(n, x.strip()) for n, x in rows]
    maxc = int((W - 130) / 18.6)
    wrapped = []
    for n, x in rows:
        while len(x) > maxc:
            cut = x.rfind(",", 0, maxc)
            cut = cut + 1 if cut > maxc // 2 else maxc
            wrapped.append((n, x[:cut]))
            n, x = None, "      " + x[cut:].lstrip()
        wrapped.append((n, x))
    lh = 44
    H = 80 + lh * len(wrapped) + 20
    fig, ax = canvas(W, H)
    t(ax, 20, H - 38, caption, MIN, YEL, bold=True)
    for i, (n, x) in enumerate(wrapped):
        y = H - 100 - i * lh
        if n is not None:
            t(ax, 20, y, f"{n:>3}", MIN, GREY, mono=True)
        c = YEL if x.strip().startswith("#pragma") else CYAN if "MPI_" in x else WHITE
        t(ax, 110, y, x, MIN, c, mono=True)
    save(fig, name)
    return H


def cards():
    sizes = {}
    sizes["c01"] = code_card("c01_topology.png", "main.c: base station out, grid in", [
        *grab("main.c", "MPI_Comm_split(MPI_COMM_WORLD", "MPI_Comm_split(MPI_COMM_WORLD"),
        *grab("main.c", "int dims[2] = { cfg.rows", "MPI_Cart_create(node_comm")], 1740)
    sizes["c02"] = code_card("c02_neighbours.png", "node.c: neighbours from the topology", [
        *grab("node.c", "MPI_Cart_shift(grid_comm, 0, 1", "MPI_Cart_shift(grid_comm, 1, 1")], 1740)
    sizes["c03"] = code_card("c03_omp.png", "node.c: k ports + 1 comms thread", [
        *grab("node.c", "#pragma omp parallel num_threads", "int tid = omp_get_thread_num();"),
        *grab("node.c", "comm_loop(n);           //", "port_loop(n, tid - 1);")], 1000)
    sizes["c04"] = code_card("c04_v2.png", "node.c, version 2: post receives, send, keep going", [
        *grab("node.c", "MPI_Irecv(&n->q_in[i]", "MPI_Irecv(&n->q_in[i]"),
        *grab("node.c", "MPI_Isend(&n->q_out[i]", "MPI_Isend(&n->q_out[i]"),
        *grab("node.c", "MPI_Testall(n->n_nb, n->q_rreq", "MPI_Testall(n->n_nb, n->q_rreq")], 1740)
    sizes["c05"] = code_card("c05_bs_v3.png", "base_station.c, version 3: persistent + Testsome", [
        *grab("base_station.c", "MPI_Recv_init(&b->rep_buf[i]", "MPI_Recv_init(&b->rep_buf[i]"),
        *grab("base_station.c", "MPI_Testsome(b->n, b->rep_req", "MPI_Testsome(b->n, b->rep_req"),
        *grab("base_station.c", "MPI_Start(&b->rep_req[idx[j]]);", "MPI_Start(&b->rep_req[idx[j]]);")], 1740)
    sizes["c06"] = code_card("c06_rule.png", "base_station.c: the window rule", [
        *grab("base_station.c", "if (n_nb > 0 && n_recent == n_nb) {", "rs->status = RESP_NONE_NEARBY;"),
        *grab("base_station.c", "for (int d = 2; d <= max_d; d++) {", "for (int d = 2; d <= max_d; d++) {"),
        *grab("base_station.c", "if (known_full(b, c, t, window)) continue;", "if (known_full(b, c, t, window)) continue;")], 1000)
    print(sizes)


# ======================================================================= graphs
def load(name):
    p = os.path.join(RES, name)
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []


def series(rows, col, by="node_v", x="nodes", skip_zero=True):
    g = defaultdict(list)
    for r in rows:
        if skip_zero and col.endswith("_mean_us") and float(r[col.replace("_mean_us", "_n")]) == 0:
            continue
        g[(r[by], int(r[x]))].append(float(r[col]))
    out = defaultdict(list)
    for (v, xx), vals in sorted(g.items(), key=lambda k: (k[0][0], k[0][1])):
        out[v].append((xx, sum(vals) / len(vals), min(vals), max(vals)))
    return out


def chart(W, H, ncols=1, left=0.13, bottom=0.17, top=0.9, wspace=0.3):
    fig, axes = plt.subplots(1, ncols, figsize=(px(W), px(H)), dpi=100, facecolor=NAVY)
    fig.subplots_adjust(left=left, right=0.98, top=top, bottom=bottom, wspace=wspace)
    axes = axes if ncols > 1 else [axes]
    for a in axes:
        a.set_facecolor(PANEL)
        for s in a.spines.values():
            s.set_color(GREY)
        a.tick_params(colors=WHITE, labelsize=MIN, length=6)
        a.grid(color=GREY, alpha=0.4, lw=1)
        a.xaxis.label.set_color(WHITE)
        a.yaxis.label.set_color(WHITE)
        a.xaxis.label.set_size(MIN)
        a.yaxis.label.set_size(MIN)
        a.locator_params(nbins=5)
    return fig, axes


def line(a, pts, c, label, unit=1000.0, band=True, ls="-"):
    xs = [p[0] for p in pts]
    if band:
        a.fill_between(xs, [p[2] / unit for p in pts], [p[3] / unit for p in pts], color=c, alpha=0.2, lw=0)
    a.plot(xs, [p[1] / unit for p in pts], color=c, lw=4, label=label, ls=ls, marker="o", ms=6)


def legend(a, loc="upper left"):
    lg = a.legend(fontsize=MIN, loc=loc, frameon=True, facecolor=NAVY, edgecolor=GREY)
    for tx in lg.get_texts():
        tx.set_color(WHITE)


def title(a, s, c=YEL):
    a.set_title(s, fontsize=MID, color=c, loc="left", fontweight="bold", pad=14)


def g_node_versions(grid):
    # averages over all 32 grid sizes x 3 seeds
    agg = defaultdict(lambda: defaultdict(list))
    for r in grid:
        v = r["node_v"]
        agg[v]["blocked"].append(float(r["blocked_s_per_node"]) * 1000)
        agg[v]["mpc"].append(float(r["msgs"]) / max(1.0, float(r["cycles"])))
    fig, axes = chart(1000, 800, ncols=2, left=0.12, bottom=0.12, top=0.86, wspace=0.45)
    vs = ["1", "2", "3"]
    for a, key, ttl in ((axes[0], "blocked", "blocked in MPI\n(ms per node)"),
                        (axes[1], "mpc", "messages per\nnode per cycle")):
        vals = [sum(agg[v][key]) / len(agg[v][key]) for v in vs]
        bars = a.bar(["v1", "v2", "v3"], vals, color=[VCOL[v] for v in vs])
        for b, val in zip(bars, vals):
            a.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{val:.2f}", ha="center", va="bottom",
                   fontsize=MIN, color=WHITE)
        title(a, ttl)
        a.set_ylim(0, max(vals) * 1.25 + 1e-9)
    save(fig, "g01_node_versions.png")
    return {v: {k: sum(x) / len(x) for k, x in agg[v].items()} for v in vs}


def g_bs_versions(rows):
    fig, axes = chart(1000, 800, left=0.15, bottom=0.15, top=0.9)
    a = axes[0]
    s = series(rows, "report_mean_us", by="bs_v")
    names = {"1": "v1 probe", "2": "v2 Irecv", "3": "v3 persistent"}
    for v in ("1", "2", "3"):
        line(a, s[v], VCOL[v], names[v])
    a.set_xlabel("charging nodes (saturated load)")
    a.set_ylabel("report delay, mean (ms)")
    legend(a)
    save(fig, "g02_bs_versions.png")


def g_grid(grid):
    fig, axes = chart(1000, 800, left=0.15, bottom=0.15, top=0.9)
    a = axes[0]
    v2 = [r for r in grid if r["node_v"] == "2"]
    line(a, series(v2, "query_rtt_mean_us")["2"], CYAN, "neighbour round trip")
    line(a, series(v2, "report_rtt_mean_us")["2"], YEL, "report round trip")
    a.axvline(13.5, color=WHITE, ls=":", lw=2)
    a.set_xlabel("charging nodes in the grid")
    a.set_ylabel("mean delay (ms)")
    legend(a)
    save(fig, "g03_grid.png")


def g_line(grid, line_rows):
    fig, axes = chart(1000, 800, left=0.15, bottom=0.15, top=0.9)
    a = axes[0]
    for rows, nm, c, ls in ((grid, "grid", CYAN, "-"), (line_rows, "line", CORAL, "--")):
        v2 = [r for r in rows if r["node_v"] == "2"]
        line(a, series(v2, "query_rtt_mean_us")["2"], c, f"{nm}: neighbour", band=False, ls=ls)
        line(a, series(v2, "report_rtt_mean_us")["2"], c, f"{nm}: report", band=False, ls=":")
    a.set_xlabel("charging nodes")
    a.set_ylabel("mean round trip (ms)")
    legend(a)
    save(fig, "g04_line.png")


def g_extra(win, poll, cpu):
    fig, axes = chart(1740, 600, ncols=2, left=0.07, bottom=0.2, top=0.86, wspace=0.28)
    a = axes[0]
    g = defaultdict(list)
    for r in win:
        rep = max(1, int(r["reports"]))
        g[float(r["window_cycles"])].append(int(r["resp_none_nearby"]) / rep * 100)
    ws = sorted(g)
    a.plot(ws, [sum(g[w]) / len(g[w]) for w in ws], color=CORAL, lw=4, marker="o", ms=8)
    a.set_xscale("log")
    a.set_xlabel("window W (cycles)")
    title(a, "% answers 'none nearby'")
    a = axes[1]
    for v in ("1", "2"):
        vr = [r for r in cpu if r["node_v"] == v]
        rr = [r for r in poll if r["node_v"] == v]
        if len(vr) != len(rr):
            continue
        xs = sorted({int(r["poll_us"]) for r in vr})
        pairs = list(zip(vr, rr))
        lat = [sum(float(b["query_rtt_mean_us"]) for q, b in pairs if int(q["poll_us"]) == x) / 3 / 1000 for x in xs]
        cpus = [sum(float(q["cpu_s"]) for q, b in pairs if int(q["poll_us"]) == x) / 3 for x in xs]
        if v == "2":
            a.plot(cpus, lat, color=CYAN, lw=4, marker="o", ms=8)
            for x, cx, ly in zip(xs, cpus, lat):
                if x in (0, 50, 200, 2000):
                    a.annotate(f"{x} us", (cx, ly), textcoords="offset points", xytext=(10, 8),
                               fontsize=MIN, color=WHITE)
    a.set_xlabel("CPU seconds per 3 s run")
    title(a, "v2 neighbour round trip (ms)")
    save(fig, "g05_extra.png")


def appendix(rows, tag, label):
    groups = [("one way delays", [("req", "request"), ("reply", "reply"), ("report", "report"), ("response", "answer")]),
              ("round trips + others", [("query_rtt", "neighbour RTT"), ("report_rtt", "report RTT"),
                                        ("nbr_collective", "v3 collective"), ("terminate", "terminate")])]
    for gi, (gname, types) in enumerate(groups):
        fig, axes = chart(1740, 800, ncols=4, left=0.06, bottom=0.14, top=0.86, wspace=0.42)
        for a, (col, nm) in zip(axes, types):
            s = series(rows, f"{col}_mean_us")
            for v in sorted(s):
                line(a, s[v], VCOL[v], f"v{v}", band=False)
            title(a, nm, WHITE)
            a.set_xlabel("nodes")
            a.locator_params(nbins=4)
        axes[0].set_ylabel("mean delay (ms)")
        legend(axes[0])
        save(fig, f"a{tag}{gi + 1}_{label}.png")


if __name__ == "__main__":
    what = sys.argv[1:] or ["diagrams", "cards", "graphs"]
    if "diagrams" in what:
        v01_architecture(); v02_node(); v03_sequence(); v04_rule(); v05_shutdown()
    if "cards" in what:
        cards()
    if "graphs" in what:
        grid, ln = load("e1_grid.csv"), load("e2_line.csv")
        if grid:
            print(g_node_versions(grid))
            g_grid(grid)
            appendix(grid, "1", "grid")
        if load("e3_bs_versions.csv"):
            g_bs_versions(load("e3_bs_versions.csv"))
        if grid and ln:
            g_line(grid, ln)
            appendix(ln, "2", "line")
        if load("e4_window.csv") and load("e5_poll.csv"):
            g_extra(load("e4_window.csv"), load("e5_poll.csv"), load("e5_poll_cpu.csv"))
