#!/usr/bin/env python3
"""
make_code_cards.py  (FIT3143 Lab 3, Task 4 slides)

Renders the code samples for the deck as navy cards. Every line is read from
the submitted source at render time, with its real line number, so a card
can never drift from the code we hand in. Pure comment lines are dropped to
keep the cards short (the gap in the line numbers shows where).

Written by: Erwyna Soo Wen Xin (36555789)
Team: Erwyna Soo Wen Xin (36555789), Taabish Farooq Bhat (35473932)
"""
import os
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "graphs", "code")
os.makedirs(OUT, exist_ok=True)
BG, TEXT, SUB, NUM = "#1B1838", "#FFFFFF", "#B3AFD6", "#6E6A9E"
MPI, OMP, KEY = "#2ED3D3", "#FFC928", "#FF9F9F"


def grab(fname, start, end, keep_comments=False, max_lines=40):
    lines = open(os.path.join(ROOT, fname)).read().split("\n")
    i0 = next(i for i, l in enumerate(lines) if start in l)
    i1 = next(i for i in range(i0, len(lines)) if end in lines[i])
    out = []
    for i in range(i0, i1 + 1):
        t = lines[i].rstrip()
        s = t.strip()
        if not keep_comments and (s.startswith("//") or s.startswith("/*") or s.startswith("*")):
            continue
        if not s:
            continue
        # trailing comments make lines too wide for a slide
        if not keep_comments and "//" in t and not s.startswith("#"):
            t = t[:t.index("//")].rstrip()
        out.append((i + 1, t))
    return out[:max_lines]


def colour(t):
    s = t.strip()
    if s.startswith("#pragma omp"):
        return OMP
    if s.startswith("//"):
        return SUB
    if re.search(r"\bMPI_[A-Z][a-z_]+\(", t):
        return MPI
    if re.search(r"\b(omp_get|omp_set)", t):
        return OMP
    return TEXT


def card(name, fname, caption, rows):
    # strip common indent
    ind = min(len(t) - len(t.lstrip()) for _, t in rows)
    rows = [(n, t[ind:]) for n, t in rows]
    longest = max(len(t) for _, t in rows)
    w = max(7.0, 0.083 * (longest + 6) + 0.6)
    h = 0.62 + 0.26 * len(rows)
    fig = plt.figure(figsize=(w, h), facecolor=BG, dpi=260)
    fig.text(0.28 / w, 1 - 0.3 / h, f"{fname}  |  {caption}", fontsize=9, color=OMP, va="center",
             family="DejaVu Sans", fontweight="bold")
    for i, (n, t) in enumerate(rows):
        y = 1 - (0.68 + 0.26 * i) / h
        fig.text(0.28 / w, y, f"{n:>4}", fontsize=9.2, color=NUM, va="center", family="DejaVu Sans Mono")
        fig.text(0.28 / w + 0.5 / w, y, t, fontsize=9.2, color=colour(t), va="center", family="DejaVu Sans Mono")
    p = os.path.join(OUT, name)
    fig.savefig(p, facecolor=BG)
    plt.close(fig)
    print("wrote", p, len(rows), "lines")


CARDS = [
    ("code01_topology.png", "main.c", "split off the base station, build the grid",
     grab("main.c", "MPI_Comm node_comm, grid_comm", "MPI_Cart_create(node_comm")),
    ("code02_neighbours.png", "node.c", "neighbours from the virtual topology",
     grab("node.c", "MPI_Cart_shift(grid_comm, 0, 1", "MPI_Group_free(&g_world)")),
    ("code03_omp_team.png", "node.c", "k port threads + 1 comms thread, shared array",
     grab("node.c", "omp_set_dynamic(0);", "}   // implicit barrier")),
    ("code04_port_update.png", "node.c", "one charging port, once per cycle",
     grab("node.c", "my_tick = t;", "pt->done_tick[p] = my_tick;")),
    ("code05_v2_nonblocking.png", "node.c", "version 2: post receives, send, keep running",
     grab("node.c", "static void start_nb_exchange", "n->q_active = 1;")
     + grab("node.c", "static void progress_nb", "MPI_Waitall(n->n_nb, n->q_sreq")),
    ("code06_v1_blocking.png", "node.c", "version 1: blocking wait that still answers requests",
     grab("node.c", "static void blocking_wait", "case TAG_REQ: serve_request")),
    ("code07_v3_collective.png", "node.c", "version 3: neighbourhood collective every cycle",
     grab("node.c", "int local = n->term_received", "MPI_Neighbor_allgather(&n->free_now")),
    ("code08_report.png", "node.c", "the report: one derived datatype, one call",
     grab("node.c", "wall_stamp(&r->year", "r->t_detect = now();", max_lines=8)
     + grab("node.c", "MPI_Irecv(&n->resp, 1, n->ts", "MPI_Isend(r, 1, n->tr")),
    ("code09_datatype.png", "common.c", "MPI_Type_create_struct for our structs",
     grab("common.c", "int blocklen[2] = { n_int, n_dbl };", "MPI_Type_free(&tmp);")),
    ("code10_window_rule.png", "base_station.c", "window check, then the 2 hop ring",
     grab("base_station.c", "for (int i = 0; i < 4; i++) {", "n_recent += rec;")
     + grab("base_station.c", "if (n_nb > 0 && n_recent == n_nb) {", "rs->status = RESP_NONE_NEARBY;")
     + grab("base_station.c", "for (int d = 2; d <= max_d; d++) {", "if (known_full(b, c, t, window)) continue;")),
    ("code11_bs_persistent.png", "base_station.c", "version 3: persistent receives + MPI_Testsome",
     grab("base_station.c", "MPI_Recv_init(&b->rep_buf[i]", "MPI_Startall(b->n, b->rep_req);")
     + grab("base_station.c", "MPI_Testsome(b->n, b->rep_req", "MPI_Start(&b->rep_req[idx[j]]);")),
    ("code12_shutdown.png", "node.c + base_station.c", "two phase graceful shutdown",
     grab("node.c", "if (!n->acked && !n->q_active && !n->r_active) {", "n->acked = 1;")
     + grab("base_station.c", "if (phase == 0 && now() >= t_end) { broadcast_tag(b, TAG_TERMINATE, treq", "if (phase == 1 && b->acks == b->n) { broadcast_tag(b, TAG_SHUTDOWN, sreq")),
]

if __name__ == "__main__":
    for c in CARDS:
        card(*c)
