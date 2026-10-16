#!/usr/bin/env python3
"""
make_diagrams.py  (FIT3143 Lab 3, Task 4 slides)

Draws the architecture diagrams for the deck in the deck's navy and yellow:
  diagram1_architecture.png   grid of MPI processes + base station, one node opened up
  diagram2_node_inside.png    the OpenMP team inside one node and the shared array
  diagram3_messages.png       message sequence: query, local redirect, report, answer
  diagram4_base_station.png   base station loop and the 2 hop window rule
  diagram5_shutdown.png       two phase graceful shutdown
  diagram6_versions.png       the 3 + 3 versions we built and what each one changes

Written by: Erwyna Soo Wen Xin (36555789)
Team: Erwyna Soo Wen Xin (36555789), Taabish Farooq Bhat (35473932)
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "graphs")
os.makedirs(OUT, exist_ok=True)

BG, PANEL, TEXT, SUB = "#1B1838", "#272350", "#FFFFFF", "#B3AFD6"
YEL, CYAN, CORAL, GREEN, GREY = "#FFC928", "#2ED3D3", "#FF7A7A", "#2BD99F", "#5B5788"
FONT = "DejaVu Sans"
plt.rcParams["font.family"] = FONT


def canvas(w, h, title, subtitle=None):
    fig = plt.figure(figsize=(w, h), dpi=220, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    ax.set_facecolor(BG)
    ax.text(0.35, h - 0.45, title, fontsize=17, fontweight="bold", color=YEL, va="center")
    if subtitle:
        ax.text(0.35, h - 0.85, subtitle, fontsize=10.5, color=SUB, va="center")
    return fig, ax


def box(ax, x, y, w, h, fc=PANEL, ec=None, lw=1.6, r=0.12, z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec or fc, lw=lw, zorder=z))


def arrow(ax, x1, y1, x2, y2, c=TEXT, lw=1.6, style="-|>", ls="-", z=3, ms=12, rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=ms,
                                 color=c, lw=lw, linestyle=ls, zorder=z,
                                 connectionstyle=f"arc3,rad={rad}"))


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, facecolor=BG)
    plt.close(fig)
    print("wrote", p)


# ---------------------------------------------------------------- diagram 1
def d1():
    fig, ax = canvas(16, 9, "Architecture: one MPI process per charging node, one for the base station",
                     "mpirun -np rows*cols+1 ./wsn rows cols   |   MPI_Comm_split + MPI_Cart_create(periods = 0,0, reorder = 0)")
    # grid 3x3
    gx, gy, s, gap = 0.7, 1.2, 1.55, 0.75
    pos = {}
    for r in range(3):
        for c in range(3):
            x = gx + c * (s + gap)
            y = gy + (2 - r) * (s + gap)
            pos[(r, c)] = (x, y)
    for (r, c), (x, y) in pos.items():
        for dr, dc in ((0, 1), (1, 0)):
            if (r + dr, c + dc) in pos:
                x2, y2 = pos[(r + dr, c + dc)]
                ax.plot([x + s / 2, x2 + s / 2], [y + s / 2, y2 + s / 2], color=CYAN, lw=3, zorder=1)
    for (r, c), (x, y) in pos.items():
        rank = r * 3 + c
        hot = (r, c) in [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
        box(ax, x, y, s, s, fc=PANEL, ec=CORAL if hot else YEL, lw=2.2)
        ax.text(x + s / 2, y + s - 0.3, f"Node {rank}", ha="center", color=TEXT, fontsize=11.5, fontweight="bold", zorder=4)
        ax.text(x + s / 2, y + s - 0.62, f"({r},{c})", ha="center", color=SUB, fontsize=9.5, zorder=4)
        for p in range(6):
            busy = (p + rank) % 3 != 0 if not hot else p != 5
            ax.add_patch(Rectangle((x + 0.17 + p * 0.205, y + 0.22), 0.17, 0.42,
                                   fc=CORAL if busy else GREEN, ec="none", zorder=4))
    ax.text(gx, gy - 0.5, "Cyan lines: the Cartesian grid. Each node only talks to up, down, left, right",
            color=SUB, fontsize=9.5)
    ax.text(gx, gy - 0.82, "(MPI_Cart_shift gives MPI_PROC_NULL past the edge). Port bars: red = in use, green = free.",
            color=SUB, fontsize=9.5)
    # base station
    bx, by, bw, bh = 9.6, 3.5, 2.6, 2.0
    box(ax, bx, by, bw, bh, fc=YEL)
    ax.text(bx + bw / 2, by + bh - 0.45, "Base station", ha="center", color=BG, fontsize=14, fontweight="bold", zorder=4)
    ax.text(bx + bw / 2, by + bh - 0.85, "last rank, 1 process, 1 thread", ha="center", color=BG, fontsize=9.5, zorder=4)
    ax.text(bx + bw / 2, by + 0.55, "listens, decides,\nanswers, logs", ha="center", color=BG, fontsize=10.5, zorder=4)
    for (r, c), (x, y) in pos.items():
        if (r, c) in [(0, 2), (1, 2), (2, 2)]:
            arrow(ax, x + s, y + s / 2, bx, by + bh / 2 + (1 - r) * 0.6, c=YEL, lw=1.3, style="<|-|>", ls="--")
    ax.text(bx + bw / 2, by - 0.45, "star overlay: any node can\nreach the base station directly", color=SUB, fontsize=9.5, ha="center", va="top")
    # legend
    lx, ly = 12.75, 6.9
    box(ax, lx, 1.0, 3.0, 6.3, fc=PANEL)
    ax.text(lx + 0.2, ly, "Message types", color=YEL, fontsize=12, fontweight="bold")
    items = [(CYAN, "TAG_REQ", "node to neighbour"), (CYAN, "TAG_REPLY", "neighbour to node"),
             (YEL, "TAG_REPORT", "node to base station"), (YEL, "TAG_RESPONSE", "base station to node"),
             (CORAL, "TAG_TERMINATE", "phase 1 stop"), (CORAL, "TAG_ACK", "nothing in flight"),
             (CORAL, "TAG_SHUTDOWN", "phase 2, finalise")]
    for i, (col, t, d) in enumerate(items):
        y = ly - 0.6 - i * 0.75
        ax.add_patch(Rectangle((lx + 0.2, y - 0.1), 0.18, 0.18, fc=col, ec="none", zorder=4))
        ax.text(lx + 0.5, y + 0.02, t, color=TEXT, fontsize=10, fontweight="bold", va="center", family="DejaVu Sans Mono")
        ax.text(lx + 0.5, y - 0.3, d, color=SUB, fontsize=9, va="center")
    save(fig, "diagram1_architecture.png")


# ---------------------------------------------------------------- diagram 2
def d2():
    fig, ax = canvas(16, 9, "Inside one charging node: an OpenMP team of k + 1 threads",
                     "MPI_Init_thread(MPI_THREAD_FUNNELED): only thread 0 ever calls MPI")
    # process boundary
    box(ax, 0.5, 0.6, 15.0, 7.1, fc=PANEL, ec=GREY, lw=1.5)
    ax.text(0.8, 7.3, "MPI process = EV charging node (rank r, coordinates (x, y))", color=SUB, fontsize=10.5)
    # comms thread
    box(ax, 0.9, 3.6, 4.1, 3.3, fc=YEL)
    ax.text(2.95, 6.45, "Thread 0: comms", ha="center", color=BG, fontsize=13.5, fontweight="bold", zorder=4)
    lines = ["every cycle_ms: tick++", "wait until done_tick[p] == tick", "count free ports, log Table 1 row",
             "free <= threshold?  ask neighbours", "Iprobe: answer neighbour requests", "Test: replies, base station answer"]
    for i, l in enumerate(lines):
        ax.text(1.15, 5.95 - i * 0.38, l, color=BG, fontsize=9.6, zorder=4)
    # shared array
    sx, sy = 5.7, 3.6
    box(ax, sx, sy, 4.6, 3.3, fc="#33306A", ec=CYAN, lw=2)
    ax.text(sx + 2.3, sy + 2.9, "Shared array (PortTable)", ha="center", color=CYAN, fontsize=12.5, fontweight="bold", zorder=4)
    for p in range(6):
        x = sx + 0.3 + p * 0.68
        ax.add_patch(Rectangle((x, sy + 1.75), 0.55, 0.65, fc=CORAL if p % 3 else GREEN, ec="none", zorder=4))
        ax.text(x + 0.27, sy + 2.07, "1" if p % 3 else "0", ha="center", va="center", color=BG, fontsize=11, fontweight="bold", zorder=5)
        ax.text(x + 0.27, sy + 1.5, f"p{p}", ha="center", color=SUB, fontsize=8.5, zorder=5)
    ax.text(sx + 0.3, sy + 1.12, "status[p]      1 in use, 0 free", color=TEXT, fontsize=9.5, family="DejaVu Sans Mono", zorder=4)
    ax.text(sx + 0.3, sy + 0.84, "done_tick[p]   last cycle p did", color=TEXT, fontsize=9.5, family="DejaVu Sans Mono", zorder=4)
    ax.text(sx + 0.3, sy + 0.56, "tick, stop, divert   thread 0 only", color=TEXT, fontsize=9.5, family="DejaVu Sans Mono", zorder=4)
    ax.text(sx + 0.3, sy + 0.28, "hist[]  Table 1 availability log", color=TEXT, fontsize=9.5, family="DejaVu Sans Mono", zorder=4)
    arrow(ax, 5.0, 5.3, sx, 5.3, c=CYAN, style="<|-|>", lw=2)
    # port threads
    for p in range(6):
        x = 10.95 + (p % 3) * 1.45
        y = 5.35 if p < 3 else 3.6
        box(ax, x, y, 1.3, 1.45, fc=GREEN)
        ax.text(x + 0.65, y + 1.0, f"Thread {p + 1}", ha="center", color=BG, fontsize=9.5, fontweight="bold", zorder=4)
        ax.text(x + 0.65, y + 0.6, f"port {p}", ha="center", color=BG, fontsize=9.5, zorder=4)
        ax.text(x + 0.65, y + 0.22, "rand_r", ha="center", color=BG, fontsize=8, zorder=4)
    arrow(ax, 10.9, 5.0, sx + 4.6, 5.0, c=GREEN, lw=2)
    ax.text(10.95, 3.25, "each port: one arrival / departure per cycle,", color=SUB, fontsize=9.2)
    ax.text(10.95, 2.95, "writes ONLY its own slot (no lock needed)", color=SUB, fontsize=9.2)
    # bottom notes
    notes = [("Why threads for ports, processes for nodes?", "Port state never leaves the node, so shared memory is cheaper than messages. One process per port would multiply ranks and messages."),
             ("Why no mutex?", "One writer per field. Ports write status[p] then done_tick[p] with #pragma omp atomic write seq_cst, so once thread 0 sees done_tick[p] == tick it also sees that cycle's status."),
             ("Why FUNNELED?", "Port threads never call MPI. FUNNELED is enough and avoids the internal locking MPI_THREAD_MULTIPLE adds to every call.")]
    for i, (h, t) in enumerate(notes):
        y = 2.75 - i * 0.72
        ax.text(0.95, y, h, color=YEL, fontsize=10.2, fontweight="bold")
        ax.text(0.95, y - 0.3, t, color=TEXT, fontsize=9.2)
    save(fig, "diagram2_node_inside.png")


# ---------------------------------------------------------------- diagram 3
def d3():
    fig, ax = canvas(16, 9, "What happens when a node fills up",
                     "Version 2 shown (MPI_Isend / MPI_Irecv). Every message carries its send time, so each type's delay is measured.")
    cols = {"N": 2.0, "A": 5.3, "B": 8.6, "BS": 13.0}
    labels = {"N": "Node 4\n(congested)", "A": "Neighbour 1", "B": "Neighbours 3, 5, 7", "BS": "Base station"}
    for k, x in cols.items():
        box(ax, x - 1.15, 7.0, 2.3, 0.9, fc=YEL if k == "BS" else PANEL, ec=YEL)
        ax.text(x, 7.45, labels[k], ha="center", va="center", color=BG if k == "BS" else TEXT, fontsize=10.5, fontweight="bold", zorder=4)
        ax.plot([x, x], [0.5, 7.0], color=GREY, lw=1.2, ls=":", zorder=1)
    def msg(y, a, b, t, c, sub=None):
        arrow(ax, cols[a], y, cols[b], y, c=c, lw=2)
        xm = (cols[a] + cols[b]) / 2
        ax.text(xm if not t.startswith("TAG_RE") or "B," not in t and "echo" not in t else (cols[a] + cols["B"]) / 2, y + 0.14, t, ha="center", color=c, fontsize=9.6, fontweight="bold", family="DejaVu Sans Mono")
        if sub:
            ax.text(xm, y - 0.3, sub, ha="center", color=SUB, fontsize=8.6)
    ax.text(cols["N"] - 1.6, 6.55, "free <= threshold", color=CORAL, fontsize=9.5, fontweight="bold")
    msg(6.1, "N", "A", "TAG_REQ  40 B, Isend x4", CYAN)
    msg(5.75, "N", "B", "", CYAN)
    msg(5.15, "A", "N", "TAG_REPLY  free ports + echo of t_send", CYAN)
    msg(4.8, "B", "N", "", CYAN)
    # branch box
    box(ax, 0.5, 3.05, 3.5, 1.3, fc="#33306A", ec=GREEN)
    ax.text(0.65, 4.05, "any neighbour > threshold?", color=GREEN, fontsize=9.6, fontweight="bold", zorder=4)
    ax.text(0.65, 3.7, "yes: send EVs there, done.", color=TEXT, fontsize=9.2, zorder=4)
    ax.text(0.65, 3.4, "no message to the base station", color=SUB, fontsize=8.8, zorder=4)
    msg(2.75, "N", "BS", "TAG_REPORT", YEL, "one 176 B derived datatype: time, node, neighbours, msgs, bytes")
    box(ax, cols["BS"] - 1.55, 1.55, 3.1, 0.75, fc="#33306A", ec=YEL)
    ax.text(cols["BS"], 1.92, "window check + ring search", ha="center", color=YEL, fontsize=9.4, zorder=4)
    msg(1.15, "BS", "N", "TAG_RESPONSE", YEL, "all nearest candidates, or 'none nearby'")
    ax.text(0.5, 0.55, "Node forwards the candidates to its EVs (divert), cooldown 2 cycles.", color=SUB, fontsize=9.5)
    # side labels
    ax.text(15.35, 5.6, "query\nround trip", color=CYAN, fontsize=9, ha="center")
    ax.text(15.35, 2.0, "report\nround trip", color=YEL, fontsize=9, ha="center")
    save(fig, "diagram3_messages.png")


# ---------------------------------------------------------------- diagram 4
def d4():
    fig, ax = canvas(16, 9, "Base station: one thread, one loop",
                     "Version 3 (best): persistent receive per node + MPI_Testsome, persistent answers, 1 MB buffered log")
    steps = [("MPI_Testsome", "over n persistent\nMPI_Recv_init"), ("window check", "did every neighbour\nreport in the last W s?"),
             ("ring search", "2 hops, then 3, ...\nskip known full nodes"), ("MPI_Start", "persistent answer\nfrom per node buffer"),
             ("log", "fprintf into 1 MB\nbuffer, re-arm recv")]
    for i, (h, t) in enumerate(steps):
        x = 0.6 + i * 3.05
        box(ax, x, 5.6, 2.7, 1.75, fc=YEL if i == 0 else PANEL, ec=YEL)
        ax.text(x + 1.35, 6.95, h, ha="center", color=BG if i == 0 else YEL, fontsize=11.5, fontweight="bold", zorder=4, family="DejaVu Sans Mono")
        ax.text(x + 1.35, 6.2, t, ha="center", va="center", color=BG if i == 0 else TEXT, fontsize=9.4, zorder=4)
        if i < 4:
            arrow(ax, x + 2.7, 6.45, x + 3.05, 6.45, c=YEL, lw=2)
    arrow(ax, 0.6 + 4 * 3.05 + 1.35, 5.6, 0.6 + 1.35, 5.6, c=GREY, lw=1.5, rad=-0.12)
    ax.text(7.5, 4.45, "no reports: sleep poll_us, then listen again (periodic listening)", color=SUB, fontsize=9.5, ha="center")
    # 2-hop example grid
    gx, gy, s = 1.0, 0.55, 1.05
    names = {}
    for r in range(3):
        for c in range(3):
            n = r * 3 + c
            x, y = gx + c * (s + 0.2), gy + (2 - r) * (s + 0.2)
            col = YEL if n == 0 else (CORAL if n in (1, 3) else (GREEN if n in (2, 4, 6) else PANEL))
            box(ax, x, y, s, s, fc=col, ec=col)
            ax.text(x + s / 2, y + s / 2, str(n), ha="center", va="center", color=BG if col != PANEL else TEXT, fontsize=13, fontweight="bold", zorder=4)
    ax.text(5.1, 3.95, "The spec's example: node 0 reports, its neighbours are 1 and 3", color=YEL, fontsize=11.5, fontweight="bold")
    rules = [(CORAL, "1 AND 3 both reported inside the window W:",
              "their reports already said 2, 4 and 6 are full  ->  'no nodes available nearby'"),
             (GREEN, "at least one of 1 or 3 has NOT reported inside W:",
              "candidates = 2 hop ring {2, 4, 6} minus nodes known full; send ALL of them (tied distance)"),
             (GREY, "every 2 hop node known full:", "widen to 3 hops, 4 hops, ... first ring with a free node wins"),
             (SUB, "cost per report:", "walks only the ring cells (at most 4d), never the whole grid  ->  ~10 us")]
    for i, (c, h, t) in enumerate(rules):
        y = 3.35 - i * 0.78
        ax.add_patch(Rectangle((5.1, y - 0.08), 0.22, 0.22, fc=c, ec="none"))
        ax.text(5.45, y + 0.03, h, color=TEXT, fontsize=10.3, fontweight="bold", va="center")
        ax.text(5.45, y - 0.3, t, color=SUB, fontsize=9.4, va="center")
    save(fig, "diagram4_base_station.png")


# ---------------------------------------------------------------- diagram 5
def d5():
    fig, ax = canvas(16, 5.0, "Graceful shutdown in two phases",
                     "No CTRL+C, no kill: the base station ends the run, and nothing is still in flight at MPI_Finalize")
    xs = [0.6, 4.3, 8.0, 11.7]
    steps = [("1  TERMINATE", "base station -> every node\n(after cycles x cycle_ms)"),
             ("2  stop new work", "ports exit their loop; node\nfinishes its own query / report,\nkeeps answering neighbours"),
             ("3  ACK", "node -> base station once\nnothing of its own is in flight.\nBS keeps answering reports"),
             ("4  SHUTDOWN", "after ALL n ACKs nothing can\nbe moving. Gather stats, cancel\n+ free persistent requests,\nMPI_Comm_free, MPI_Finalize")]
    for i, (h, t) in enumerate(steps):
        box(ax, xs[i], 0.4, 3.4, 3.2, fc=CORAL if i in (0, 3) else PANEL, ec=CORAL)
        ax.text(xs[i] + 0.2, 3.15, h, color=BG if i in (0, 3) else CORAL, fontsize=13, fontweight="bold", zorder=4)
        ax.text(xs[i] + 0.2, 1.75, t, color=BG if i in (0, 3) else TEXT, fontsize=11.2, va="center", zorder=4)
        if i < 3:
            arrow(ax, xs[i] + 3.4, 2.0, xs[i + 1], 2.0, c=CORAL, lw=2.2)
    ax.text(15.3, 4.15, "Why not one 'stop' message? A node could still be waiting on a neighbour's reply,\nor have a report on its way, when the other side finalises.",
            color=SUB, fontsize=9.5, ha="right", va="center")
    save(fig, "diagram5_shutdown.png")


# ---------------------------------------------------------------- diagram 6
def d6():
    fig, ax = canvas(16, 7.4, "Versions we built and compared", "Same decision logic in every version; only the MPI pattern changes")
    head = ["", "How it talks", "Blocks?", "Cost"]
    rows = [("Node v1", "MPI_Send + MPI_Probe / MPI_Recv wait loop", "yes, while waiting", "cycles stall"),
            ("Node v2", "MPI_Isend + MPI_Irecv + MPI_Testall", "never", "poll latency"),
            ("Node v3", "MPI_Neighbor_allgather every cycle", "in the collective", "msgs every cycle"),
            ("BS v1", "MPI_Iprobe, MPI_Recv, MPI_Send, line log", "on each send", "serial queue"),
            ("BS v2", "MPI_Irecv(ANY_SOURCE) + MPI_Isend", "never", "1 report per Test"),
            ("BS v3", "MPI_Recv_init x n + MPI_Testsome + Send_init, 1 MB log", "never", "lowest")]
    xs = [0.5, 2.6, 10.0, 12.8]
    for j, h in enumerate(head):
        ax.text(xs[j], 6.05, h, color=YEL, fontsize=12, fontweight="bold")
    for i, r in enumerate(rows):
        y = 5.3 - i * 0.78
        best = r[0] in ("Node v2", "BS v3")
        box(ax, 0.35, y - 0.3, 15.3, 0.62, fc="#33306A" if best else PANEL, ec=YEL if best else PANEL)
        for j, t in enumerate(r):
            ax.text(xs[j], y, t, color=YEL if (j == 0) else TEXT, fontsize=10.5, va="center", zorder=4,
                    fontweight="bold" if j == 0 else "normal", family="DejaVu Sans Mono" if j == 1 else FONT)
    ax.text(0.5, 0.45, "Outlined rows are the versions we picked as best; Task 3 graphs justify each choice.", color=SUB, fontsize=9.8)
    save(fig, "diagram6_versions.png")


if __name__ == "__main__":
    d1(); d2(); d3(); d4(); d5(); d6()
