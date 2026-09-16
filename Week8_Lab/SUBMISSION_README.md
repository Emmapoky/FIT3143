# FIT3143 Lab 2 (Week 8): Message Passing Interface

**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu) and Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)

| File | Task | Written by |
|---|---|---|
| `task1.c` | Task 1, Open MPI | Taabish |
| `task2.c` | Task 2, hybrid Open MPI + OpenMP | Taabish |
| `Task3_Performance_Evaluation.pdf` | Task 3, performance evaluation | Erwyna |
| `supporting/` | The measurements, scripts and CAAS run behind Task 3 | Erwyna |

The slides, the AI declaration and the AI prompt records are uploaded as separate files.

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
| `caas/` | The CAAS job files and the output of job 39361, 8 processes across two nodes. |

Measured on a MacBook Pro 14 inch (November 2023) with an Apple M3 Max (14 cores: 10 performance and 4 efficiency), and on Monash CAAS.
