#!/usr/bin/env python3
"""
run_experiments.py  (FIT3143 Lab 3, Task 3)

Runs every simulation behind the Task 3 graphs and appends one CSV row per
run (the row is written by the base station itself, see base_station.c).

Written by: Erwyna Soo Wen Xin (36555789)
Team: Erwyna Soo Wen Xin (36555789), Taabish Farooq Bhat (35473932)

Experiments:
  E1 grid  32 grid sizes (4 to 64 nodes) x node versions 1, 2, 3 x 3 seeds
  E2 line  32 line sizes (1x2 to 1x64)   x node versions 1, 2, 3 x 3 seeds
  E3 bs    base station versions 1, 2, 3 x 6 grid sizes x 3 seeds, saturated
           load, so every node reports and the base station gets bursts
  E4 window  predefined period 0.25 to 20 cycles, 7x7 hotspot grid x 3 seeds
  E5 poll    poll sleep 0 to 2000 us on a 4x4 grid x 3 seeds, with CPU time

The script is resumable: a run already in the CSV is skipped, so a crash or
a closed laptop lid only costs the run in progress.

Usage:  python3 scripts/run_experiments.py [E1 E2 E3 E4 E5]
"""
import csv
import os
import resource
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WSN = os.path.join(ROOT, "wsn")
RES = os.path.join(ROOT, "results")
LOGS = os.path.join(ROOT, "logs")
SEEDS = [1, 2, 3]

# 32 grids, 4 to 64 nodes, squares and rectangles mixed so "grid size"
# is not secretly "square side length"
GRIDS = [(2, 2), (2, 3), (3, 3), (2, 5), (3, 4), (2, 7), (4, 4), (3, 6),
         (4, 5), (3, 7), (2, 11), (4, 6), (5, 5), (3, 9), (4, 7), (5, 6),
         (4, 8), (5, 7), (6, 6), (4, 10), (6, 7), (5, 9), (6, 8), (7, 7),
         (5, 10), (6, 9), (7, 8), (6, 10), (8, 8), (4, 15), (5, 12), (2, 31)]
GRIDS.sort(key=lambda g: (g[0] * g[1], g))
LINES = [(1, n) for n in range(2, 66, 2)]          # 32 lines, 1x2 .. 1x64

# Heavy uniform load: 75% of ports busy on average, so about half of all
# node-cycles are congested at every grid size. Same load per node at every
# size means any growth in delay comes from the size, not from more traffic
# per node.
BASE = ["-c", "30", "-p", "100", "-s", "uniform", "-a", "0.6", "-d", "0.2", "-q"]


def done_keys(csv_path, fields):
    if not os.path.exists(csv_path):
        return set()
    with open(csv_path) as f:
        return {tuple(r.get(k, "") for k in fields) for r in csv.DictReader(f)}


def run(rows, cols, extra, csv_path, log_path, tag):
    """One mpirun. Returns (wall seconds, child CPU seconds)."""
    np_ = rows * cols + 1
    cmd = ["mpirun", "--oversubscribe", "-np", str(np_), WSN, str(rows), str(cols)] \
        + extra + ["-r", csv_path, "-o", log_path]
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    t0 = time.time()
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=300)
    wall = time.time() - t0
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)
    status = "ok" if p.returncode == 0 else f"FAIL rc={p.returncode}"
    print(f"  {tag:<40} {rows}x{cols:<3} {wall:5.1f}s  {status}", flush=True)
    if p.returncode != 0:
        print(p.stdout[-2000:])
    return wall, cpu


def log_for(exp, name, seed):
    # keep the seed 1 logs as the submitted evidence, the rest go to /tmp
    d = os.path.join(LOGS, exp) if seed == 1 else os.path.join("/tmp", "wsn_logs", exp)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name + ".log")


def sweep(exp, shapes, csv_name):
    path = os.path.join(RES, csv_name)
    have = done_keys(path, ["rows", "cols", "node_v"])
    # note: seed is not in the CSV, so count rows per (rows, cols, node_v)
    counts = {}
    if os.path.exists(path):
        for r in csv.DictReader(open(path)):
            k = (r["rows"], r["cols"], r["node_v"])
            counts[k] = counts.get(k, 0) + 1
    for (r, c) in shapes:
        for v in (1, 2, 3):
            n_done = counts.get((str(r), str(c), str(v)), 0)
            for seed in SEEDS[n_done:]:
                run(r, c, BASE + ["-V", str(v), "-B", "3", "-S", str(seed)], path,
                    log_for(exp, f"{r}x{c}_v{v}", seed), f"{exp} v{v} seed {seed}")


def e3():
    path = os.path.join(RES, "e3_bs_versions.csv")
    counts = {}
    if os.path.exists(path):
        for r in csv.DictReader(open(path)):
            k = (r["rows"], r["bs_v"])
            counts[k] = counts.get(k, 0) + 1
    for (r, c) in [(3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)]:
        for b in (1, 2, 3):
            n_done = counts.get((str(r), str(b)), 0)
            for seed in SEEDS[n_done:]:
                extra = ["-c", "30", "-p", "100", "-s", "saturated", "-q", "-V", "2",
                         "-B", str(b), "-S", str(seed)]
                run(r, c, extra, path, log_for("e3_bs", f"{r}x{c}_b{b}", seed), f"E3 bs v{b} seed {seed}")


def e4():
    path = os.path.join(RES, "e4_window.csv")
    counts = {}
    if os.path.exists(path):
        for r in csv.DictReader(open(path)):
            k = float(r["window_cycles"])
            counts[k] = counts.get(k, 0) + 1
    # hotspot on 7x7: a 13 node busy diamond in the middle, so neighbouring
    # nodes report close together and the window actually decides answers
    # (under uniform load reports were too rare for W to matter at all)
    for w in [0.25, 0.5, 1, 2, 3, 4, 6, 8, 12, 20]:
        for seed in SEEDS[counts.get(float(w), 0):]:
            extra = ["-c", "40", "-p", "100", "-s", "hotspot", "-q", "-C", "1",
                     "-V", "2", "-B", "3", "-w", str(w), "-S", str(seed)]
            run(7, 7, extra, path, log_for("e4_window", f"w{w}", seed), f"E4 window {w} seed {seed}")


def e5():
    path = os.path.join(RES, "e5_poll.csv")
    cpu_path = os.path.join(RES, "e5_poll_cpu.csv")
    have = set()
    if os.path.exists(cpu_path):
        have = {(r["poll_us"], r["node_v"], r["seed"]) for r in csv.DictReader(open(cpu_path))}
    new = not os.path.exists(cpu_path)
    with open(cpu_path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["poll_us", "node_v", "seed", "wall_s", "cpu_s"])
        for poll in [0, 20, 50, 100, 200, 500, 1000, 2000]:
            for v in (1, 2):
                for seed in SEEDS:
                    if (str(poll), str(v), str(seed)) in have:
                        continue
                    extra = BASE + ["-V", str(v), "-B", "3", "-P", str(poll), "-S", str(seed)]
                    wall, cpu = run(4, 4, extra, path, log_for("e5_poll", f"p{poll}_v{v}", seed),
                                    f"E5 poll {poll} v{v} seed {seed}")
                    w.writerow([poll, v, seed, f"{wall:.3f}", f"{cpu:.3f}"])
                    f.flush()


if __name__ == "__main__":
    os.makedirs(RES, exist_ok=True)
    todo = sys.argv[1:] or ["E1", "E2", "E3", "E4", "E5"]
    t0 = time.time()
    for e in todo:
        print(f"== {e}", flush=True)
        if e == "E1": sweep("e1_grid", GRIDS, "e1_grid.csv")
        if e == "E2": sweep("e2_line", LINES, "e2_line.csv")
        if e == "E3": e3()
        if e == "E4": e4()
        if e == "E5": e5()
    print(f"all done in {(time.time() - t0) / 60:.1f} min")
