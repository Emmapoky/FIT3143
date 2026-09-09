####################################################################
# make_task3_doc.py
# ------------------------------------------------------------------
# FIT3143 Lab #2 Task 3: writes Task3_Performance_Evaluation.md from
# the measured CSVs, so the write up and the graphs can never drift
# apart from each other or from the data.
#
# Written by: Erwyna Soo Wen Xin (36555789)
#
# Run: python3 make_task3_doc.py   (after run_phases.py and make_graphs.py)
####################################################################
import csv

def read(p):
    with open(p) as f:
        return list(csv.DictReader(f))

def F(r, k):
    return float(r[k])

def smallest_odd_factor(p):
    q = p
    while q % 2 == 0:
        q //= 2
    if q == 1:
        return None
    d = 3
    while d * d <= q:
        if q % d == 0:
            return d
        d += 2
    return q

def p_eff(p):
    d = smallest_odd_factor(p)
    return p if d is None else p * (1.0 - 1.0 / d)

by_n     = read("results_by_n.csv")
by_procs = read("results_by_procs.csv")
hyb_t    = read("results_hybrid_t.csv")
hyb_tot  = read("results_hybrid_total.csv")
ph1      = sorted(read("phases_task1.csv"), key=lambda r: int(F(r, 'procs')))
ph2      = sorted(read("phases_task2.csv"), key=lambda r: (int(F(r,'procs'))*int(F(r,'threads')), int(F(r,'procs'))))
phs      = read("phases_serial.csv")
rb       = read("rank_balance.csv")
launch   = float(open("launch_overhead.txt").read().strip())

NFIX   = int(F(ph1[0], 'n'))
serial = F(by_procs[0], 'serial_s')

b1  = ph1[0]
T1  = F(b1, 'total_s')
rp1 = F(b1, 'comp_s') / T1
rs1 = (F(b1, 'sort_s') + F(b1, 'write_s')) / T1

b2  = ph2[0]
T2  = F(b2, 'total_s')
rp2 = F(b2, 'comp_s') / T2
rs2 = (F(b2, 'sort_s') + F(b2, 'write_s')) / T2

p14 = next(r for r in ph1 if int(F(r, 'procs')) == 14)
p28 = ph1[-1]
ser = phs[0]

def tbl1():
    o = ["| p | d | p_eff | comp max (s) | comp min (s) | kappa(p) | S Amdahl(p) | S Amdahl(p_eff) | S empirical |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in ph1:
        p = int(F(r, 'procs')); d = smallest_odd_factor(p); e = p_eff(p)
        k = (F(r, 'bcast_s') + F(r, 'gather_s')) / T1
        o.append(f"| {p} | {d if d else '2^k'} | {e:.1f} | {F(r,'comp_s'):.3f} | {F(r,'comp_min_s'):.3f} | "
                 f"{k:.5f} | {1/(rs1+rp1/p+k):.2f} | {1/(rs1+rp1/e+k):.2f} | {T1/F(r,'total_s'):.2f} |")
    return "\n".join(o)

def tbl_imbal():
    o = ["| p | smallest odd factor d | measured comp max / comp mean | predicted 1/(1 - 1/d) |",
         "|---|---|---|---|"]
    for r in ph1:
        p = int(F(r, 'procs')); d = smallest_odd_factor(p)
        pred = 1.0 if d is None else 1.0 / (1.0 - 1.0 / d)
        o.append(f"| {p} | {d if d else 'none, power of two'} | {F(r,'comp_s')/F(r,'comp_mean_s'):.2f} | {pred:.2f} |")
    return "\n".join(o)

def tbl2():
    o = ["| p x t | Width | p_eff x t | kappa | S Amdahl | S Amdahl(p_eff) | S empirical |",
         "|---|---|---|---|---|---|---|"]
    for r in ph2:
        p, t = int(F(r, 'procs')), int(F(r, 'threads')); w = p * t; e = p_eff(p) * t
        k = (F(r, 'bcast_s') + F(r, 'gather_s') + F(r, 'merge_s')) / T2
        o.append(f"| {p}x{t} | {w} | {e:.1f} | {k:.5f} | {1/(rs2+rp2/w+k):.2f} | "
                 f"{1/(rs2+rp2/e+k):.2f} | {T2/F(r,'total_s'):.2f} |")
    return "\n".join(o)

def tbl_rank(pp):
    rows = [r for r in rb if int(F(r, 'procs')) == pp]
    o = ["| Rank | Search time (s) | Primes found |", "|---|---|---|"]
    for r in rows:
        o.append(f"| {int(F(r,'rank'))} | {F(r,'comp_s'):.3f} | {int(F(r,'primes_found')):,} |")
    return "\n".join(o)

bn  = max(by_n, key=lambda r: F(r, 'serial_s') / F(r, 'mpi_s'))
bw  = max(by_procs, key=lambda r: F(r, 'serial_s') / F(r, 'mpi_s'))
bwh = max(hyb_tot, key=lambda r: serial / F(r, 'hybrid_s'))
h27 = next(r for r in hyb_tot if int(F(r,'procs')) == 2 and int(F(r,'threads')) == 7)
h73 = next(r for r in hyb_tot if int(F(r,'procs')) == 7 and int(F(r,'threads')) == 3)

DOC = f"""# Task 3, Performance evaluation with Amdahl's Law

**Unit:** FIT3143 Parallel Computing, Semester 2 2026
**Assessment:** Lab 2 (Week 8), Message Passing Interface
**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu)
and Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)
**Task 3 by:** Erwyna Soo Wen Xin

> Supporting document for Task 3, submitted under the "Task 3 (Optional)" line of
> the submission checklist, which asks for any additional notes or documents that
> support the calculations and the experimental design. Every number here is produced by
> `run_benchmarks.sh`, `run_phases.py` and `make_graphs.py` on the machine below
> and is reproducible by re-running them. Some prose was drafted with AI
> assistance; see `AI_Declaration.md`.

---

## 1. Headline finding

The partitioning scheme in Task 1 does not distribute the work evenly, and the
amount by which it fails is predictable in closed form.

`task1.c` gives rank *r* the numbers `3 + 2r + 2pk`. For any odd prime *d*
dividing *p*, the term `2pk` vanishes modulo *d*, so **every number rank *r* ever
tests is congruent to `3 + 2r` modulo *d***. The rank whose class is 0 mod *d*
therefore receives only multiples of *d*, and `is_prime` rejects those on its
first loop iteration. One rank in *d* does effectively no work.

At p = 3, rank 0 spent {[F(r,'comp_s') for r in rb if int(F(r,'procs'))==3 and int(F(r,'rank'))==0][0]:.3f} s and found **2 primes**, while ranks 1 and 2
spent about {[F(r,'comp_s') for r in rb if int(F(r,'procs'))==3 and int(F(r,'rank'))==1][0]:.2f} s each and found about 3.69 million each:

{tbl_rank(3)}

At p = 4, which has no odd factor, the same code splits perfectly:

{tbl_rank(4)}

The consequence is a saw tooth in every speedup curve. The code has, in effect,
not *p* workers but

```
p_eff = p * (1 - 1/d)     d = smallest odd prime factor of p
p_eff = p                 when p is a power of two
```

and the measured imbalance ratio matches `1/(1 - 1/d)` to two decimal places at
every width we tested:

{tbl_imbal()}

This is why p = 3 is *slower* than p = 2 in `results_by_procs.csv`
({F(next(r for r in by_procs if int(F(r,'width'))==3),'mpi_s'):.2f} s against {F(next(r for r in by_procs if int(F(r,'width'))==2),'mpi_s'):.2f} s), and why 2 x 7 beats 7 x 3 in the hybrid
({F(h27,'hybrid_s'):.2f} s against {F(h73,'hybrid_s'):.2f} s) even though both command the same number of workers.

**Recommended fix**, not applied because Task 1 is Taabish's deliverable and we
did not want to present code we had quietly changed: keep the cyclic idea but
break the congruence, either by assigning interleaved *chunks* of candidates
(the chunk of 1000 we used in Week 4 Task 2) instead of single strided values, or
by having every rank skip multiples of 3 globally rather than one rank owning
them. Either restores `p_eff = p`.

---

## 2. The machine and the measurement method

| | |
|---|---|
| CPU | Apple M3 Max, 14 cores |
| MPI | Open MPI (Homebrew), single node, shared memory transport |
| Compiler | `-O2` for all five programs, so the comparison is about the parallelism, not the optimiser |
| Fixed problem size | n = {NFIX:,} ({int(F(b1,'primes')):,} primes) |
| n sweep | 31 values, {int(F(by_n[0],'n')):,} to {int(F(by_n[-1],'n')):,} |
| Width sweep | 1 to 28, i.e. up to twice the core count |
| Repetitions | fastest of repeated runs, not the mean |

**Why fastest, not mean.** A slow run means something else took a core. A fast run
cannot be faster than the work genuinely takes. The minimum is the closest thing to
a noise-free measurement available without a quiet machine.

**Why the whole command is timed.** Every headline run time in `results_*.csv` is
the wall clock of the entire command as the shell sees it, `mpirun` included. The
rubric asks for an overall speedup including communication, computation, sorting
and file writing, and launching 14 processes is time a user genuinely waits for.
Using the program's internal timer instead would hand Open MPI a free
**{launch:.3f} s** that the serial version never gets, that is the paired
measurement from `measure_launch.py`, and it is a fixed cost that does not shrink
with n, which is exactly why Open MPI loses to OpenMP at small n in Graph 1.

---

## 3. Experimental design: separating the serial and parallel parts

Amdahl's Law needs two numbers a single end-to-end stopwatch cannot give: the
fraction of the work that can be spread out, and the fraction that cannot. We
built three instrumented programs to get them.

| File | What it is |
|---|---|
| `serial_instr.c` | Week 4 Task 1, unchanged, plus a timer around the file write. Week 4 deliberately stopped its clock before writing; Lab 2 needs the write included. |
| `task1_instr.c` | Taabish's `task1.c`, unchanged, with per-phase timers. |
| `task2_instr.c` | Taabish's `task2.c`, unchanged, with the thread-merge phase timed on its own. |

Four design decisions we would defend in Q&A:

**(a) The instrument is separate from the thing measured.** The `MPI_Reduce` calls
that collect phase times cost time themselves. Leaving them in `task1.c` would
make our submitted Task 1 slower than the code we are claiming.

**(b) Phase times are the MAX across ranks, not rank 0's own.** A collective
finishes when the slowest rank arrives, so the maximum is what the wall clock
feels. Rank 0's value would have hidden the imbalance in section 1 entirely.

**(c) Every instrumented run opens with `MPI_Barrier`.** This is the trap
demonstrated in the Week 7 extra class, where an `MPI_Recv` appeared to take four
seconds when it was really waiting for the sender to finish reading a file. Without
a barrier, ranks clearing `MPI_Init` early start their clocks early and charge
launch skew to "communication".

**(d) A second `MPI_Barrier` sits between the search and the gather.** This one was
added after a first round of measurements reported `gather` times of over seven
seconds, which was obviously not the cost of a shared-memory copy. Idle ranks were
sitting inside `MPI_Gather` waiting for the busy ones, and that waiting was being
billed as communication. The barrier drains the wait into its own phase, `imbal_s`.
After the change, `gather` fell to {F(b1,'gather_s'):.4f} s at p = 1 and
{F(p28,'gather_s'):.4f} s at p = 28, the real cost, while `imbal_s` carries the
seconds. **Load imbalance and communication want completely different fixes, so a
measurement that confuses them is worse than useless.**

### Phases

| Phase | Scales with p? | Role |
|---|---|---|
| `bcast`, n out to every rank | grows slightly | communication, kappa |
| `comp`, the search loop | **yes** | parallel fraction, r_p |
| `merge` (hybrid only), thread buffers into one rank buffer | grows with threads | charged to kappa |
| `imbal`, barrier wait after the search | grows with imbalance | diagnostic, not additive |
| `gather`, `MPI_Gather` + `MPI_Gatherv` | grows with p | communication, kappa |
| `sort`, `qsort` on the root | no | serial fraction, r_s |
| `write`, {int(F(b1,'primes')):,} lines of `fprintf` | no | serial fraction, r_s |

`imbal` is deliberately not added into the total. The elapsed time from the start
of the search to the barrier release is `comp_max`; for the fastest rank that is
`comp_min + imbal`. Adding both would double count. Confirmed on the data:
bcast + comp + gather + sort + write reproduces `total_s` at every width.

---

## 4. The model

```
S(p) = 1 / ( r_s  +  r_p / p  +  kappa(p) )

  r_p      = comp(1) / T(1)              the search loop, the only part that spreads
  r_s      = (sort + write)(1) / T(1)    qsort and fprintf on the root, never spreads
  kappa(p) = (bcast + gather)(p) / T(1)  MEASURED at every p, not assumed
```

**On the baseline.** The fractions come from the p = 1 run of the parallel program
itself, not from the Week 4 serial program. Taabish's Week 8 search uses a 6k±1
primality test while the Week 4 serial uses `d += 2`, so the Week 8 code is already
about 1.4x faster per candidate before a single process is added ({F(next(r for r in by_procs if int(F(r,'width'))==1),'mpi_s'):.2f} s against
{serial:.2f} s at the same n). Deriving r_p and r_s against the Week 4 program would
fold that algorithmic win into what is meant to be a measurement of parallelism.
The Week 4 comparison the specification asks for is still made in full; it is what
Graphs 2, 3, 4 and 5 show. This section answers a different question.

**On kappa.** Most textbook treatments set kappa to zero. We measure it, following
the method from the Week 7 extra class. The finding is that on this hardware
**kappa is negligible**: {(F(p28,'bcast_s')+F(p28,'gather_s'))/T1:.5f} of the runtime even at p = 28. Every rank is on
one machine, so `MPI_Gatherv` is a shared-memory copy rather than network traffic.
Communication is not what stops the speedup here; the partition is. On CAAS across
two compute nodes we would expect kappa to be orders of magnitude larger and to
become the dominant term.

---

## 5. Measured parameters

### Task 1, Open MPI

| Parameter | Value |
|---|---|
| T(1), the whole program at one process | {T1:.3f} s |
| Parallel fraction r_p | **{rp1:.4f}** |
| Serial fraction r_s | **{rs1:.4f}** |
| Amdahl ceiling, 1 / r_s as p goes to infinity | **{1/rs1:.2f}x** |
| Phase split at p = 1 | comp {F(b1,'comp_s'):.3f}, sort {F(b1,'sort_s'):.3f}, write {F(b1,'write_s'):.3f} |
| Phase split at p = 14 | comp {F(p14,'comp_s'):.3f}, gather {F(p14,'gather_s'):.4f}, sort {F(p14,'sort_s'):.3f}, write {F(p14,'write_s'):.3f} |

{tbl1()}

### Task 2, hybrid Open MPI + OpenMP

| Parameter | Value |
|---|---|
| T(1 worker) | {T2:.3f} s |
| Parallel fraction r_p | **{rp2:.4f}** |
| Serial fraction r_s | **{rs2:.4f}** |

{tbl2()}

The hybrid partly escapes the residue problem. Only the MPI stride is congruence
bound; inside a rank OpenMP hands out chunks with `schedule(dynamic, 1000)`, so a
thread that draws a cheap chunk simply comes back for another. This is why the
hybrid's best configurations use few processes and many threads.

---

## 6. Empirical results

| Measurement | Value |
|---|---|
| Week 4 serial at n = {NFIX:,} | {serial:.3f} s |
| Best Open MPI speedup over the n sweep | {F(bn,'serial_s')/F(bn,'mpi_s'):.2f}x at n = {int(F(bn,'n')):,} |
| Best Open MPI speedup over the width sweep | {F(bw,'serial_s')/F(bw,'mpi_s'):.2f}x at p = {int(F(bw,'width'))} |
| Best hybrid speedup | {serial/F(bwh,'hybrid_s'):.2f}x at {int(F(bwh,'procs'))} x {int(F(bwh,'threads'))} |
| Best POSIX Threads speedup | {max(serial/F(r,'pthread_s') for r in by_procs):.2f}x |
| Best OpenMP speedup | {max(serial/F(r,'omp_s') for r in by_procs):.2f}x |
| `mpirun` launch + `MPI_Init` overhead | {launch:.3f} s, fixed, independent of n |
| Serial write phase | {F(ser,'write_s'):.3f} s of {F(ser,'total_s'):.3f} s total |

Every parallel version plateaus around 7x rather than 14x. Two reasons, and we
would give both: the M3 Max's 14 cores are 10 performance cores plus 4 efficiency
cores, so the last four workers run at a fraction of the speed of the first ten;
and past p = 14 there are more runnable processes than cores, so adding more only
adds scheduling.

---

## 7. Answers to the questions the specification asks

**How does the actual speedup compare against the theoretical speedup?**
Plain Amdahl at *p* overshoots badly, because it assumes the partition divides the
work into *p* equal shares and it does not. Amdahl evaluated at `p_eff` reproduces
the saw tooth in the measurement, which tells us the imbalance is the dominant
error term rather than noise. The residual gap that `p_eff` still does not explain
is core heterogeneity and, past p = 14, oversubscription, neither of which is in
the model, and both of which are properties of the machine rather than the code.

**Will more MPI processes always increase the speedup?**
No, and we can show three separate reasons from our own data. First, r_s is a hard
floor: no number of processes makes the root's `qsort` or its {int(F(b1,'primes')):,} line
file write any faster, capping us at {1/rs1:.2f}x however wide we go. Second,
kappa(p) grows with p, from {(F(b1,'bcast_s')+F(b1,'gather_s'))/T1:.5f} at p = 1 to {(F(p28,'bcast_s')+F(p28,'gather_s'))/T1:.5f} at p = 28,
because every extra rank is another participant in the collective. Third and
largest here, `p_eff` does not grow monotonically with p. Going from p = 2 to
p = 3 adds a process but leaves the number of ranks doing real work at 2, so the
run gets *slower*, not faster, the extra rank contributes nothing while still
joining every collective. The same happens at every step onto a multiple of 3.

**How would the workload distribution affect the speedup?**
It is the dominant factor in this implementation, which is the whole of section 1.
Cyclic partitioning was the right instinct, the cost of `is_prime(k)` grows like
sqrt(k), so a block split would give the last rank the most expensive numbers and
every other rank would wait for it. But a stride of exactly 2p locks each rank into
a residue class, and that interacts with the trial-division fast rejection to idle
one rank in *d*. The fix is to break the congruence, not to abandon cyclic.

**Will the speedup results be the same across different machines?**
No. r_s and kappa are both properties of the machine, not the algorithm. A slower
disk raises the write phase and therefore r_s, lowering the ceiling. Running across
two computers over a network raises kappa by orders of magnitude, because
`MPI_Gatherv` stops being a shared memory copy and becomes real network traffic. A
machine with homogeneous cores would push the plateau closer to 14x. The one thing
that *would* transfer is the saw tooth, because it comes from arithmetic in the
partitioning rather than from any hardware.


---

## 8. CAAS: the same code across two compute nodes

Everything above was measured on one laptop. On 9 September we ran the same
programs on Monash's CAAS cluster (`student-caas-headnode`), with 8 MPI ranks
split deliberately across **two physical compute nodes**, `student-caas-n01` and
`student-caas-n02`, so that `MPI_Gatherv` had to cross a network rather than copy
within one machine. Job 39361, n = 130,000,000, output verified byte identical to
the serial reference.

| p | Total (s) | Speedup vs serial | Speedup vs p=1 | Amdahl | Gap | kappa(p) |
|---|---|---|---|---|---|---|
| 1 | 52.50 | 1.49x | 1.00x | 1.00 | 0.0% | 0.00015 |
| 2 | 26.86 | 2.91x | 1.95x | 1.96 | 0.4% | 0.00072 |
| 4 | 13.99 | 5.60x | 3.75x | 3.78 | 0.7% | 0.00116 |
| 8 | 7.59 | **10.31x** | 6.91x | 7.05 | 1.9% | 0.00124 |

Serial baseline on the cluster: 78.29 s. Measured fractions: r_p = 0.9819,
r_s = 0.0179, giving a ceiling of 55.9x.

### Three things this changes

**1. The code scales near linearly on hardware that suits it.** 86.4% parallel
efficiency at 8 processes, and the curve had not flattened when we stopped. On
the laptop we plateaued near 7x. The difference is the machine, not the code: the
M3 Max has 10 performance cores and 4 much slower efficiency cores, and past 14
workers we were oversubscribing. Cluster cores are homogeneous and dedicated.

**2. Amdahl's Law predicts our measurement to within 2%.** This is the result we
would lead with. On the laptop, theory overshot measurement by roughly 23% at
p = 8, and section 7 attributes that to core heterogeneity and oversubscription
rather than to a flaw in the model. The cluster run tests that claim directly: on
homogeneous dedicated cores with a balanced process count, the same model lands
at 7.05 against a measured 6.91. The gap was the hardware, and we can now show it
rather than argue it.

**3. We predicted communication would dominate here. It does not.** The earlier
version of this document, and our closing slide, both said a CAAS run across two
nodes was the missing measurement and that kappa would finally become the
dominant term. That prediction was wrong, and we would rather report it than
quietly drop it.

The gather did become genuinely more expensive: 0.0633 s at p = 8 across the
network against 0.0138 s at the same width on one machine, 4.6x larger, which
confirms it really is network traffic now and not a memory copy. But as a
fraction of runtime kappa is still only 0.0012. The reason is a ratio we had not
thought about carefully enough: the payload is about 59 MB of primes, moved once,
against 52 seconds of arithmetic. At roughly 0.9 GB/s of effective throughput the
transfer is over before it matters. Communication would only dominate this
problem at a much smaller n, or with far more ranks, or on a slower interconnect.

### What this run does not show

We chose process counts of 1, 2, 4 and 8, all powers of two, so that the
partition would be balanced and the scaling result would be clean. The
consequence is that every measured imbalance ratio came back at 1.00, and the
residue-class saw tooth from section 1 does not appear in this data at all. That
finding still rests on the laptop sweep, which covered 18 widths including the
ones with odd prime factors. Re-running on CAAS at p = 3, 6 or 12 would confirm
it on the cluster, and we would expect it to, because it comes from arithmetic in
the partitioning rather than from any property of the hardware.

Raw output: `caas/results/caas_results.txt`.

---

## 9. Limitations we would raise ourselves

1. **The cluster run covers only balanced process counts.** Section 8 used powers
   of two, so it confirms the scaling result but not the residue-class finding.
   That still rests on the laptop sweep.
2. **The Week 4 baseline is a different primality test.** Handled by reporting both
   baselines, but it is the first thing we would flag rather than be caught on.
3. **`int` in the gather path.** `MPI_Gatherv` takes `int` counts, so the code caps
   out above about 2 billion primes. Not reachable at our n, but a real limit.
4. **kappa is measured, not modelled.** We report kappa(p) at the widths we ran
   rather than fitting a function, so the theoretical curve is only defined there.
5. **The `p_eff` model is first order.** It accounts for the rank that is fully
   idle, not for the fact that the surviving ranks also carry slightly uneven
   shares, which is why measured imbalance runs a little above `1/(1 - 1/d)` at
   the larger widths.
"""

open("Task3_Performance_Evaluation.md", "w").write(DOC)
print("wrote Task3_Performance_Evaluation.md")
