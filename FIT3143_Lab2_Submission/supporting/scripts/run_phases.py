####################################################################
# run_phases.py
# ------------------------------------------------------------------
# FIT3143 Lab #2 Task 3: runs the instrumented programs across the
# width sweep and writes the phase CSVs, plus the per-rank balance
# evidence in rank_balance.csv.
#
# Written by: Erwyna Soo Wen Xin (36555789)
#
# Erwyna: this lives in Python rather than in run_benchmarks.sh
# because picking the fastest of several runs by one field of a CSV
# line is exactly the kind of thing shell quoting gets wrong quietly.
#
# Run: python3 run_phases.py
####################################################################
import subprocess, os, sys

N     = os.environ.get("N_FIXED", "130000000")
REPS  = int(os.environ.get("REPS", "2"))
WIDTHS = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,16,20,24,28]
COMBOS = [(1,1),(2,1),(2,2),(2,3),(2,4),(3,2),(2,6),(4,3),(2,7),(4,4),(7,3),(4,6),(7,4)]
MPIRUN = ["mpirun", "--oversubscribe"]


def run(cmd, env=None):
    e = dict(os.environ); e.update(env or {})
    return subprocess.run(cmd, capture_output=True, text=True, env=e).stdout


def best(cmd, env=None, reps=REPS):
    """Keep the PHASE line from the fastest run. Total is always the
    third field from the end, whatever the phase count."""
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

with open("phases_task1.csv", "w") as fh:
    fh.write(H1 + "\n")
    for w in WIDTHS:
        r = best(MPIRUN + ["-np", str(w), "./build/mpi_instr", N])
        if r:
            fh.write(r + "\n")
        print(f"  task1 p={w}", flush=True)

with open("phases_task2.csv", "w") as fh:
    fh.write(H2 + "\n")
    for p, t in COMBOS:
        r = best(MPIRUN + ["-x", "OMP_NUM_THREADS", "-np", str(p), "./build/hybrid_instr", N],
                 env={"OMP_NUM_THREADS": str(t)})
        if r:
            fh.write(r + "\n")
        print(f"  task2 {p}x{t}", flush=True)

# Per-rank evidence for the residue-class finding.
with open("rank_balance.csv", "w") as fh:
    fh.write("procs,rank,comp_s,primes_found\n")
    for w in [2, 3, 4, 5, 6, 8, 9]:
        out = run(MPIRUN + ["-np", str(w), "./build/mpi_instr", N], env={"RANKDUMP": "1"})
        rows = sorted((l[len("RANK,"):] for l in out.splitlines() if l.startswith("RANK,")),
                      key=lambda l: int(l.split(",")[1]))
        for r in rows:
            fh.write(r + "\n")
        print(f"  rank dump p={w}", flush=True)

print("done")
