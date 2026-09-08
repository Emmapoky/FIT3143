# FIT3143 Lab #2 (Week 8), Message Passing Interface

**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu)
and Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)

| Task | Owner |
|---|---|
| Task 1, Open MPI prime search | Taabish |
| Task 2, hybrid Open MPI + OpenMP | Taabish |
| Task 3, performance evaluation with Amdahl's Law | Erwyna |
| Task 4, presentation slides and documentation | Erwyna |

---

## Submission checklist

Against the checklist in the assessment specification:

| Required | File | Status |
|---|---|---|
| Task 1 code | `task_1.c` | done, compiles, output verified against the serial reference |
| Task 2 code | `task_2.c` | done, compiles, output verified against the serial reference |
| Task 4 slides | `Presentation_Slides.pdf` | export from Canva once the last image is placed |
| Task 3 supporting notes | `Task3_Performance_Evaluation.md` | done |
| AI declaration | `AI_Declaration.md` | done, also Appendix A4 of the deck |
| AI prompt records | `AI_Prompt_Records.pdf` | **outstanding, Taabish** |
| CAAS or cluster analysis | `caas/` | **outstanding, Taabish.** Job files are written and ready to submit |

Two things are still open, and both are listed above rather than buried:

1. **`AI_Prompt_Records.pdf`** has not been produced. Item 9 of the spec requires it.
2. **The CAAS run has not been done.** Both the Task 1 and the Task 2 rubric rows
   ask for it by name in their D and HD bands. Everything needed is in `caas/`.

---

## Which figure goes on which slide

All figures live in `graphs/`. Twelve in total: nine plots of measured data, and
three drawings of how the code works.

| Slide | Figure | What it is |
|---|---|---|
| 3 | `diagram1_stride_partition.png` | how candidates are handed out, and why p = 3 breaks |
| 4 | `diagram2_gatherv_offsets.png` | Gather, displacements, Gatherv into the root array |
| 5 | `graph1_runtime_vs_n.png` | run time against problem size |
| 6 | `graph2_speedup_vs_n.png` | empirical speedup against problem size |
| 7 | `graph3_speedup_vs_width.png` | empirical speedup against width |
| 8 | `diagram3_hybrid_layout.png` | processes across, threads within |
| 9 | `graph4_hybrid_vs_mpi_threads.png` | hybrid against pure MPI as threads are added |
| 10 | `graph5_matched_width.png` | matched total width, four arrangements |
| 13 | `graph9_rank_balance.png` | per rank search time and primes found |
| 14 | `graph6_amdahl_task1.png` | Task 1, empirical against theoretical |
| 15 | `graph7_amdahl_task2.png` | Task 2, empirical against theoretical |
| 19 (A1) | `graph8_phase_breakdown.png` | measured phase split across the width sweep |

Graphs 1 to 7 are the seven the specification requires by number. Graphs 8 and 9
and the three diagrams are ours, added because they carry the Task 3 argument.

---

## Measurement instruments (Task 3)

`serial_instr.c`, `task_1_instr.c` and `task_2_instr.c` are copies of the Week 4
serial program and of Taabish's two Week 8 programs, with per-phase timers added
and nothing else changed. Diff them against the originals to confirm.

The instruments are deliberately separate files. The `MPI_Reduce` calls that
collect phase times cost time themselves, so leaving them inside `task_1.c` would
make the submitted Task 1 slower than the code we are actually claiming.

---

## Reproducing everything

```bash
./run_benchmarks.sh          # results_*.csv, plus a correctness diff against the serial reference
python3 run_phases.py        # phases_*.csv and rank_balance.csv
python3 measure_launch.py    # launch_overhead.txt
python3 make_graphs.py       # graphs 1 to 9, and amdahl_summary.csv
python3 make_diagrams.py     # the three explanatory diagrams
python3 make_task3_doc.py    # Task3_Performance_Evaluation.md
```

`run_benchmarks.sh` reads `N_MIN`, `N_STEP`, `N_MAX`, `N_FIXED`, `WIDTHS`,
`COMBOS` and `REPS` from the environment, so a reduced sweep can be run on CAAS
without editing the script:

```bash
N_MAX=40000000 WIDTHS="1 2 4 8 16" REPS=1 ./run_benchmarks.sh
```

The full sweep takes roughly 45 minutes on an M3 Max.

---

## Building by hand

```bash
mpicc -O2 task_1.c -o task_1 -lm
mpicc -O2 task_2.c -o task_2 -lm -Xpreprocessor -fopenmp \
      -I$(brew --prefix libomp)/include -L$(brew --prefix libomp)/lib -lomp
mpirun -np 8 ./task_1 30000000
OMP_NUM_THREADS=4 mpirun -np 2 ./task_2 30000000
```

On Linux, `-fopenmp` alone replaces the three libomp flags.

**Pick a power of two for the process count** if you want a balanced partition.
See section 1 of `Task3_Performance_Evaluation.md`: at any p with an odd prime
factor d, one rank in d does no work.

---

## Note on `task_2.c`

As originally drafted, `task_2.c` called `memcpy` without including `<string.h>`,
which is a hard error under Apple clang, so the file did not compile. A one line
include was added. The original is preserved as `task_2.c.orig-backup`.

---

## Files not for submission

`build/` and `primes_*.txt` are generated and gitignored. The prime lists total
about 470 MB. Regenerate any of them by running the corresponding program.
