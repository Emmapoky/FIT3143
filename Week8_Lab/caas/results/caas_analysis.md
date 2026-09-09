# CAAS run, job 39361 - analysis

**Run:** 9 September 2026, `student-caas-headnode`, 8 MPI ranks across two
compute nodes (`student-caas-n01`, `student-caas-n02`). n = 130,000,000.
Output verified byte identical to the serial reference.

Serial baseline on the cluster: **78.29 s** (77.60 compute + 0.69 write).

| p | Total (s) | Speedup vs serial | Speedup vs p=1 | Amdahl | Gap | kappa(p) | imbalance |
|---|---|---|---|---|---|---|---|
| 1 | 52.50 | 1.49x | 1.00x | 1.00 | 0.0% | 0.00015 | 1.000 |
| 2 | 26.86 | 2.91x | 1.95x | 1.96 | 0.4% | 0.00072 | 1.001 |
| 4 | 13.99 | 5.60x | 3.75x | 3.78 | 0.7% | 0.00116 | 1.001 |
| 8 | 7.59 | **10.31x** | 6.91x | 7.05 | 1.9% | 0.00124 | 1.001 |

Measured fractions: **r_p = 0.9819, r_s = 0.0179**, ceiling 55.9x.
Parallel efficiency at p = 8: **86.4%**.

Hybrid, 2 processes x 2 threads, one process per node: 13.96 s, against
13.99 s for pure MPI at 4 processes. Indistinguishable at matched width, which
is consistent with the laptop finding that arrangement only matters when the
partition is unbalanced.

## Three findings

**1. Near linear scaling.** 86.4% efficiency at 8 processes across two physical
machines, and the curve had not flattened. The laptop plateaued near 7x because
of the M3 Max's 4 efficiency cores and oversubscription past 14 workers. Cluster
cores are homogeneous and dedicated, so that ceiling is gone.

**2. Amdahl predicts to within 2%.** On the laptop, theory overshot measurement
by roughly 23% at p = 8, and we attributed that to core heterogeneity rather
than to the model. This run tests that claim: on homogeneous dedicated cores at
a balanced process count, the same model gives 7.05 against a measured 6.91.
The gap was hardware, and we can now show it rather than argue it.

**3. Our prediction about communication was wrong.** We said a two node run was
the missing measurement and that kappa would finally dominate. The gather did
get genuinely dearer, 0.0633 s at p = 8 against 0.0138 s at the same width on
one machine, 4.6x larger, which confirms it is real network traffic now. But as
a fraction of runtime kappa is still only 0.0012.

The reason is a ratio we had not considered carefully: about 59 MB of primes
moved once, against 52 seconds of arithmetic, at roughly 0.9 GB/s effective
throughput. Communication would only dominate at a much smaller n, with far more
ranks, or on a slower interconnect.

## What this run does not show

Process counts were 1, 2, 4 and 8, all powers of two, chosen so the partition
would be balanced and the scaling result clean. Every imbalance ratio therefore
came back at 1.00, and the residue-class saw tooth does not appear in this data.
That finding still rests on the laptop sweep across 18 widths. Re-running at
p = 3, 6 or 12 would confirm it here, and should, since it comes from arithmetic
in the partitioning rather than from hardware.

Raw output: `caas_results.txt`.
