# FIT3143 Lab #2 (Week 8) — Message Passing Interface

**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu)
and Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)

| Task | Owner |
|---|---|
| Task 1 — Open MPI prime search | Taabish |
| Task 2 — hybrid Open MPI + OpenMP | Taabish |
| Task 3 — performance evaluation with Amdahl's Law | Erwyna |
| Task 4 — presentation slides and documentation | Erwyna |

## Submitted files

| File | What it is |
|---|---|
| `task_1.c` | Task 1, Open MPI |
| `task_2.c` | Task 2, hybrid Open MPI + OpenMP |
| `Task3_Performance_Evaluation.md` | Task 3 supporting document |
| `AI_Declaration.md` | Generative AI declaration, item 9 |
| `graphs/` | The seven required graphs plus two supporting figures |

## Measurement instruments (Task 3)

`serial_instr.c`, `task_1_instr.c` and `task_2_instr.c` are copies of the Week 4
serial program and of Taabish's two Week 8 programs with per-phase timers added
and nothing else changed. Diff them against the originals to confirm.

## Reproducing everything

```bash
./run_benchmarks.sh          # results_*.csv, plus a correctness check against the serial reference
python3 run_phases.py        # phases_*.csv and rank_balance.csv
python3 measure_launch.py    # launch_overhead.txt
python3 make_graphs.py       # graphs/ and amdahl_summary.csv
python3 make_task3_doc.py    # Task3_Performance_Evaluation.md
```

`run_benchmarks.sh` reads `N_MIN`, `N_STEP`, `N_MAX`, `N_FIXED`, `WIDTHS`,
`COMBOS` and `REPS` from the environment, so a reduced sweep can be run on CAAS
without editing the script:

```bash
N_MAX=40000000 WIDTHS="1 2 4 8 16" REPS=1 ./run_benchmarks.sh
```

## Building by hand

```bash
mpicc -O2 task_1.c -o task_1 -lm
mpicc -O2 task_2.c -o task_2 -lm -Xpreprocessor -fopenmp \
      -I$(brew --prefix libomp)/include -L$(brew --prefix libomp)/lib -lomp
mpirun -np 8 ./task_1 30000000
OMP_NUM_THREADS=4 mpirun -np 2 ./task_2 30000000
```

On Linux, `-fopenmp` alone replaces the three libomp flags.

## Note on `task_2.c`

As originally drafted, `task_2.c` called `memcpy` without including
`<string.h>`, which is a hard error under Apple clang. A one line include was
added; the original is preserved as `task_2.c.orig-backup`.
