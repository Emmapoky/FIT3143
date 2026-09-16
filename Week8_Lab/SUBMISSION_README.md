# FIT3143 Lab 2 (Week 8): Message Passing Interface

**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu) and Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)

| File | Task | Written by |
|---|---|---|
| `task1.c` | Task 1, Open MPI | Taabish |
| `task2.c` | Task 2, hybrid Open MPI + OpenMP | Taabish |
| `Task3_Performance_Evaluation.pdf` | Task 3, performance evaluation | Erwyna |
| `supporting/` | The measurements, scripts and CAAS run behind Task 3 | Erwyna |

The slides and `AI_Declaration.pdf` are uploaded as separate files. `AI_Declaration.pdf` is also in this zip. It is our one AI declaration file: the declaration, then the full Gemini Pro prompt record, then the full Claude prompt record.

## Building and running

```
mpicc -O2 task1.c -o task1
mpirun -np 8 ./task1 130000000

mpicc -O2 task2.c -o task2 -fopenmp
OMP_NUM_THREADS=4 mpirun -np 2 ./task2 130000000
```

On macOS with Homebrew's libomp, use `-Xpreprocessor -fopenmp -I$(brew --prefix libomp)/include -L$(brew --prefix libomp)/lib -lomp` in place of `-fopenmp`.

Each program writes the sorted primes to `primes_task1.txt` or `primes_task2.txt`, then prints the total run time and the search time of every rank (task1) or every thread (task2). Both prime lists match the list from our Week 4 serial program exactly.

For an even split, use a power of two for the number of MPI processes. The Task 3 document explains why.

## What is in supporting/

| Folder | Contents |
|---|---|
| `instruments/` | Copies of our programs with phase timers added. Task 3 is measured with these. |
| `scripts/` | The benchmark and plotting scripts. Every graph and table comes from these. |
| `results/` | Every measurement, as CSV. |
| `graphs/` | The 7 required graphs, 3 supporting graphs and 3 diagrams. |
| `caas/` | Evidence of our CAAS run, job 39361 (8 processes across two nodes): the exact job file that ran, the output it printed, and our analysis. Its README explains what changed in our files after the run. |
| `primes_output/` | The sorted primes below n = 130,000,000 written by the submitted `task1.c` and `task2.c` (xz compressed), the console output of both runs with every rank's and thread's search time, and SHA-256 checksums showing both files are byte identical to our Week 4 serial output. |
| `experiments/` | A side experiment for Task 1, not the submitted code: `partition_variants.c` builds the search three ways (our cyclic stride, a block split, and chunks of 1000 odd numbers dealt in turn), `run_partition_comparison.py` times all three at n = 130,000,000 on 2 to 14 processes, and `partition_comparison.csv` and `partition_comparison.png` hold the result shown on appendix slide A6. |

Measured on a MacBook Pro 14 inch (November 2023) with an Apple M3 Max (14 cores: 10 performance and 4 efficiency), and on Monash CAAS.
