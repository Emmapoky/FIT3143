####################################################################
# run_phases_by_n.py
# ------------------------------------------------------------------
# FIT3143 Lab #2 Task 3: the same phase split as run_phases.py, but
# sweeping n instead of the process count. The spec asks for the
# theoretical speedup with a growing problem size as well as a growing
# process count, and r_p and r_s both move with n, so they have to be
# measured at every n rather than reused from n = 130 million.
#
# Written by: Erwyna Soo Wen Xin (36555789)
#
# Team:
#   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
#   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
#
# Erwyna: for every n I run each instrument twice, back to back. Once
# on a single worker to get r_p and r_s for that n, and once at 14
# workers (14 processes for Task 1, 2 x 7 for Task 2) to get kappa and
# the measured speedup. 14 is our core count and the same width as
# graphs 1 and 2, so these line up with those graphs.
#
# Run: python3 run_phases_by_n.py
#      (needs ./build/mpi_instr and ./build/hybrid_instr)
####################################################################
import subprocess, os

N_MIN, N_STEP, N_MAX = 10_000_000, 4_000_000, 130_000_000
MPIRUN = ["mpirun", "--oversubscribe"]


def run(cmd, env=None):
    e = dict(os.environ); e.update(env or {})
    return subprocess.run(cmd, capture_output=True, text=True, env=e).stdout


def best(cmd, env=None, reps=1):
    """Keep the PHASE line from the fastest run, judged on total, which
    is always the third field from the end."""
    bl, bv = None, None
    for _ in range(reps):
        for line in run(cmd, env).splitlines():
            if line.startswith("PHASE,"):
                v = float(line.split(",")[-3])
                if bv is None or v < bv:
                    bv, bl = v, line
    return bl[len("PHASE,"):] if bl else None


H1 = "n,procs,threads,primes,bcast_s,comp_s,imbal_s,gather_s,sort_s,write_s,total_s,comp_min_s,comp_mean_s"
H2 = "n,procs,threads,primes,bcast_s,comp_s,merge_s,imbal_s,gather_s,sort_s,write_s,total_s,comp_min_s,comp_mean_s"

with open("phases_by_n_task1.csv", "w") as f1, open("phases_by_n_task2.csv", "w") as f2:
    f1.write(H1 + "\n")
    f2.write(H2 + "\n")
    for n in range(N_MIN, N_MAX + 1, N_STEP):
        # one worker, then 14 workers, for the same n
        for p, reps in [(1, 1), (14, 2)]:
            r = best(MPIRUN + ["-np", str(p), "./build/mpi_instr", str(n)], reps=reps)
            if r:
                f1.write(r + "\n"); f1.flush()
        for p, t, reps in [(1, 1, 1), (2, 7, 2)]:
            r = best(MPIRUN + ["-x", "OMP_NUM_THREADS", "-np", str(p), "./build/hybrid_instr", str(n)],
                     env={"OMP_NUM_THREADS": str(t)}, reps=reps)
            if r:
                f2.write(r + "\n"); f2.flush()
        print(f"  n = {n:,} done", flush=True)

print("done")
