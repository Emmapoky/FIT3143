#!/usr/bin/env python3
"""
run_partition_comparison.py

FIT3143 Lab 2, side experiment for Task 1. Builds partition_variants.c three
times (cyclic stride, block split, chunks of 1000) and times each one at
n = 130,000,000 on 2, 3, 4, 6, 7, 8, 12 and 14 MPI processes. Keeps the
fastest of 2 runs of the whole mpirun command, the same rule as
run_benchmarks.sh, and writes partition_comparison.csv.

    python3 run_partition_comparison.py

Team: Erwyna Soo Wen Xin (36555789) and Taabish Farooq Bhat (35473932).
Written with Claude (Anthropic) on 16 September 2026.
"""
import csv, re, subprocess, time

N = 130000000
PROCS = [2, 3, 4, 6, 7, 8, 12, 14]
NAMES = {0: "stride (submitted)", 1: "block", 2: "chunked 1000"}

for v in NAMES:
    subprocess.run(["mpicc", "-O2", f"-DPARTITION={v}", f'-DOUTNAME="primes_v{v}.txt"',
                    "partition_variants.c", "-o", f"pv{v}", "-lm"], check=True)

rows = []
for p in PROCS:
    for v, name in NAMES.items():
        best = None
        for _ in range(2):
            t0 = time.perf_counter()
            out = subprocess.run(["mpirun", "--oversubscribe", "-np", str(p), f"./pv{v}", str(N)],
                                 capture_output=True, text=True, check=True).stdout
            wall = time.perf_counter() - t0
            internal = float(re.search(r"Total Wall Clock Time: ([\d.]+)", out).group(1))
            slowest = float(re.search(r"Computation Time: ([\d.]+)", out).group(1))
            ratio = float(re.search(r"Slowest rank / average rank: ([\d.]+)", out).group(1))
            primes = int(re.search(r"Total Primes Found: (\d+)", out).group(1))
            if best is None or wall < best[0]:
                best = (wall, internal, slowest, ratio, primes)
        rows.append([p, name, *[round(x, 4) for x in best[:4]], best[4]])
        print(rows[-1], flush=True)

with open("partition_comparison.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["procs", "partition", "wall_s", "internal_s", "slowest_search_s", "slowest_over_average", "primes"])
    w.writerows(rows)
print("wrote partition_comparison.csv")
