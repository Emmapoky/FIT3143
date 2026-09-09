# FIT3143 Lab #2 (Week 8) — Message Passing Interface

Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu

| File | Task | Author |
|---|---|---|
| `task1.c` | Task 1, Open MPI | Taabish |
| `task2.c` | Task 2, hybrid MPI + OpenMP | Taabish |
| `Task3_Performance_Evaluation.pdf` | Task 3, performance evaluation | Erwyna |

Slides and the AI declaration are uploaded separately.

## Building

```
mpicc -O2 task1.c -o task1 -lm
mpirun -np 8 ./task1 30000000

mpicc -O2 task2.c -o task2 -lm -fopenmp
OMP_NUM_THREADS=4 mpirun -np 2 ./task2 30000000
```

On macOS the OpenMP flags are `-Xpreprocessor -fopenmp -I$(brew --prefix libomp)/include -L$(brew --prefix libomp)/lib -lomp`.

Both write to `primes_task1.txt` / `primes_task2.txt`. Output is byte identical
to our Week 4 serial program under `diff`.

Pick a power of two for the process count if you want a balanced partition.
Section 1 of the Task 3 document explains why.

## supporting/

| Folder | What |
|---|---|
| `instruments/` | the three timer-instrumented copies Task 3 measures with |
| `scripts/` | benchmark and plotting scripts, everything regenerates from these |
| `graphs/` | the 7 required figures, plus 2 extra and 3 diagrams |
| `results/` | every measurement as CSV |
| `caas/` | cluster job files and the output of job 39361 |

Measured on an Apple M3 Max (14 cores) at n = 130,000,000, and on Monash CAAS
across two compute nodes, where it reached 10.31x over the serial baseline at
86.4% parallel efficiency.
