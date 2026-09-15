# CAAS run, job 39361: analysis

**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu) and Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)
**Written by:** Erwyna Soo Wen Xin

**Run:** 9 September 2026 on `student-caas-headnode`. Eight MPI processes were split across two compute nodes, `student-caas-n01` and `student-caas-n02`, four on each, with n = 130,000,000. The prime list matched the serial reference exactly.

Serial baseline on the cluster (our Week 4 search): **78.29 s**, of which 77.60 s is the search and 0.69 s is the file write.

| p | Total (s) | Speedup vs serial | Speedup vs p = 1 | Amdahl | Gap | kappa(p) | Slowest / average rank |
|---|---|---|---|---|---|---|---|
| 1 | 52.50 | 1.49x | 1.00x | 1.00 | 0.0% | 0.00015 | 1.000 |
| 2 | 26.86 | 2.91x | 1.95x | 1.96 | 0.4% | 0.00072 | 1.001 |
| 4 | 13.99 | 5.60x | 3.75x | 3.78 | 0.7% | 0.00116 | 1.001 |
| 8 | 7.59 | **10.31x** | 6.91x | 7.05 | 1.9% | 0.00124 | 1.001 |

"Speedup vs serial" is already 1.49x at one process because Task 1 uses a faster primality test (divisors of the form 6k - 1 and 6k + 1) than our Week 4 serial program, which tries every odd divisor. "Speedup vs p = 1" takes that difference out, and it is the column Amdahl's Law is compared against.

From the p = 1 run: r_p = 0.9819 and r_s = 0.0179, so the Amdahl ceiling is 1 / 0.0179 = 55.9x. Parallel efficiency at p = 8 is 6.91 / 8 = **86.4%**.

Task 2 with 2 processes x 2 threads, one process on each node, took 13.96 s. Task 1 with 4 processes took 13.99 s. With the same number of workers and an even split, the two versions run at the same speed.

## What we found

**1. Close to linear scaling.** 86.4% efficiency at 8 processes across two machines, and the speedup was still rising. On our laptop the speedup levels off near 7x, because its 14 cores are 10 performance cores and 4 slower efficiency cores, and past 14 processes the laptop is oversubscribed. The cluster cores are all the same and were given to our job alone, so that ceiling does not apply.

**2. Amdahl's Law is within 2% of what we measured.** At p = 8 the model gives 7.05 and we measured 6.91. On the laptop the model overshot by about 23% at p = 8, which we put down to the mixed cores. This run backs that up: on identical cores with an even split, the same model matches.

**3. Communication is still small, even across two nodes.** We expected the network to make kappa the biggest term. It did not. The gather at p = 8 took 0.0633 s across the two nodes, against 0.0138 s at the same width on the laptop, so it was about 4.6 times slower. That shows the data really crossed the network, but it is still only about 0.12% of the run. The job sends about 59 MB of primes once, against 52 s of searching. Communication would only matter at a much smaller n, with many more processes, or on a slower network.

## What this run does not show

We used 1, 2, 4 and 8 processes, all powers of two, so the split was even and every rank did real work. That means the idle rank problem described in our Task 3 document does not appear in this data. It would appear at p = 3, 6 or 12, because it comes from the arithmetic of the stride and not from the hardware.

Raw output: `caas_results.txt`.
