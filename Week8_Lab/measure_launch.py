####################################################################
# measure_launch.py
# ------------------------------------------------------------------
# FIT3143 Lab #2 Task 3: measures what mpirun costs before our code
# starts, by taking the external and internal clock from the SAME run
# and subtracting. Paired samples, because comparing a best-of-N
# external time against a single internal time gives nonsense.
#
# Written by: Erwyna Soo Wen Xin (36555789)
#
# Erwyna: this is the one number that explains why Open MPI loses to
# OpenMP at small n. It is a fixed cost, it does not shrink when the
# problem shrinks, so as a fraction of the run it grows without bound
# as n falls.
#
# Run: python3 measure_launch.py [n] [procs] [reps]
####################################################################
import subprocess, time, re, sys, statistics

n     = sys.argv[1] if len(sys.argv) > 1 else "130000000"
procs = sys.argv[2] if len(sys.argv) > 2 else "14"
reps  = int(sys.argv[3]) if len(sys.argv) > 3 else 6

ds = []
for _ in range(reps):
    t0 = time.time()
    out = subprocess.run(["mpirun", "--oversubscribe", "-np", procs, "./build/mpi", n],
                         capture_output=True, text=True).stdout
    t1 = time.time()
    inner = float(re.search(r'Total Wall Clock Time: ([0-9.]+)', out).group(1))
    ds.append((t1 - t0) - inner)

med = statistics.median(ds)
with open("launch_overhead.txt", "w") as fh:
    fh.write(f"{med:.6f}\n")

print(f"mpirun launch + MPI_Init overhead, {procs} processes, n = {int(n):,}")
print(f"  samples: {[f'{d:.3f}' for d in ds]}")
print(f"  median:  {med:.3f} s   min: {min(ds):.3f} s")
print("  written to launch_overhead.txt")
