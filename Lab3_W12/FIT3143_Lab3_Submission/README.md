# FIT3143 Lab #3 (Week 12): Distributed Wireless Sensor Network

**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu)
and Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)

A simulator of a grid of EV charging nodes and one base station. Open MPI
connects the nodes (one MPI process each, in an MPI virtual topology) and
the base station (one more MPI process). OpenMP simulates the charging
ports inside each node (one thread per port, sharing one array).

| Task | Owner | Files |
|---|---|---|
| Task 1, EV charging nodes | Taabish | `main.c`, `node.c` |
| Task 2, base station | Erwyna | `base_station.c`, `common.c` |
| Shared message formats | both | `wsn.h` |
| Task 3, communication analysis | Erwyna (3a), Taabish (3b) | `scripts/`, `results/`, `graphs/`, `logs/` |
| Task 4, slides | both | Canva deck, exported to `Presentation_Script.pdf`; recording in `Presentation_Video.mp4` |

---

## Build and run

```bash
make
mpirun --oversubscribe -np 10 ./wsn 3 3
```

`-np` must be rows x cols + 1: the last rank is the base station, the same
layout as the Week 12 virtual topology example. `rows = 1` gives the line
topology. Linux / CAAS: `make` uses plain `-fopenmp` automatically.

| Option | Meaning | Default |
|---|---|---|
| `-k` | charging ports per node (OpenMP threads per node, plus 1 comms thread) | 6 |
| `-t` | congested when free ports <= t | 1 |
| `-c`, `-p` | cycles to run, real ms per cycle (1 cycle = 10 simulated s, like Table 1) | 40, 100 |
| `-w` | base station predefined period, in cycles | 3 |
| `-s` | load: `uniform`, `hotspot` (low availability test case), `saturated`, `idle` | hotspot |
| `-a`, `-d` | arrival / departure probability per port per cycle (uniform only) | 0.45, 0.30 |
| `-V` | node version: 1 blocking, 2 nonblocking, 3 neighbour collective | 2 |
| `-B` | base station version: 1 probe, 2 irecv, 3 persistent | 3 |
| `-C` | cooldown cycles after a report | 2 |
| `-P` | poll sleep in microseconds | 200 |
| `-S` | random seed | 3143 |
| `-o` | base station log file | `base_station.log` |
| `-L dir` | also write one log per node (with the Table 1 availability table) | off |
| `-r file` | append one CSV summary row per run | off |
| `-q` | quiet stdout | off |

The run ends on its own after `-c` cycles: the base station sends TERMINATE,
waits for every node's ACK, then sends SHUTDOWN. No CTRL+C needed.

---

## What is where

| Path | What |
|---|---|
| `wsn.h`, `main.c`, `node.c`, `base_station.c`, `common.c`, `Makefile` | the program |
| `logs/sample/` | a 3x3 hotspot run: base station log + all 9 node logs |
| `logs/e1_grid/`, `logs/e2_line/`, ... | base station log of every seed 1 run behind the graphs |
| `results/*.csv` | one row per run, written by the base station; `summary_*.csv` = seed averages |
| `results/run_experiments.out` | console output of the experiment runner |
| `graphs/slides/` | everything on the slides: `v*` diagrams, `c*` code cards, `l*` log cards, `g*` graphs, `a*` appendix graphs (all text at least 30 px on the slide) |
| `graphs/graph*.png`, `graphs/per_type/` | earlier full size graphs, one per message type |
| `scripts/` | `run_experiments.py` (E1 to E5), `make_slide_visuals.py` (every slide image), older `make_graphs.py`, `make_diagrams.py`, `make_code_cards.py` |
| `Presentation_Script.pdf`, `Presentation_Video.mp4` | the 26 slide deck, and the recorded talk (about 5:15) followed by the two Q&A answers |
| `AI_Declaration.pdf` | AI use declaration and prompt records |
| `caas/` | CAAS job files (see the CAAS section) |
| `tests/test_evidence.txt` | edge cases, sanitizer and leak checks, bugs found |

## Reproducing Task 3

```bash
make
python3 scripts/run_experiments.py      # E1 to E5, about 41 minutes on a laptop, resumable
python3 scripts/make_slide_visuals.py graphs
```

---

## Versions (rubric: blocking and nonblocking, at least three for the base station)

| Version | Node side (`-V`) | Base station side (`-B`) |
|---|---|---|
| 1 | `MPI_Send` + blocking `MPI_Probe`/`MPI_Recv` wait loop (still answers neighbours while waiting, so no deadlock) | `MPI_Iprobe` poll, then blocking `MPI_Recv` + `MPI_Send`, one disk write per log line |
| 2 | `MPI_Irecv` posted first, then `MPI_Isend`, then `MPI_Testall` while cycles keep running | one `MPI_Irecv(MPI_ANY_SOURCE)` kept posted, answers with `MPI_Isend` |
| 3 | `MPI_Neighbor_allgather` on the Cartesian communicator every cycle, `MPI_Allreduce` to agree on the stop | one persistent `MPI_Recv_init` per node + `MPI_Testsome`, persistent `MPI_Send_init` answers, 1 MB buffered log |

Chosen: node v2, base station v3 (see `graphs/slides/g01_node_versions.png`,
`g02_bs_versions.png`). Every version uses the same decision code, so the
comparison isolates the MPI pattern.

| Measured (3 seeds) | v1 | v2 | v3 |
|---|---|---|---|
| Node: ms blocked in MPI per node per run (grid, all sizes) | 5.0 | 0 | 52.3 |
| Node: messages per node per cycle | 1.90 | 1.90 | 3.16 |
| Base station: report delay, 9 to 64 nodes, saturated (ms) | 0.95 to 3.5 | 0.15 to 0.21 | 0.27 to 0.31 |
| Base station: work per report (us) | about 180 | about 25 | 8 to 18 |

Base station v2 delivers reports about 0.1 ms faster than v3; we kept v3
because it does half the work per report, so it has more headroom as the
grid grows, and the 0.1 ms is below the 200 us poll interval.

## CAAS

Run on Monash CAAS on 23 October 2026 (Open MPI 4.1.5 module `openmpi`, `srun`
launcher, same as Lab 2). All outputs are in `caas/` exactly as the jobs wrote them.

| Job | What | Result |
|---|---|---|
| 200672 | `wsn_demo.job`: one 3x3 run on 2 nodes, base station log and 9 node logs (`caas/demo200672/`) | COMPLETED |
| 200673, 200674, 200675 | `wsn_sweep.job` with `VER=1`, `2`, `3`: 32 grids and 32 lines each on 4 nodes, base station v3, seed 1 (`caas/job<id>_v<n>/`, CSVs `e1_grid_caas.csv`, `e2_line_caas.csv`, 64 logs each) | all 192 runs COMPLETED, no FAILED lines |
| 200554 | first demo attempt | FAILED after 2 s: Open MPI `mpirun` could not start its daemons on the compute nodes. Kept in `caas/failed_attempt_200554/`. The job files were then changed from `mpirun` to `srun` (as in Lab 2). |

`caas/sacct_lab3.txt` is the `sacct` record of every job and step, including the failed attempt.

Two limits shaped the job files: the CAAS partition allows 20 minutes per job (so
the sweep is one job per node version), and a CAAS node has 16 CPUs (so the demo
uses 5 tasks x 3 CPUs per node with `-k 2`).

What CAAS showed (node v2, grid, `slides` A9): neighbour round trip about 0.8 to
0.9 ms against 0.65 to 0.77 ms on the laptop, terminate about 0.4 to 1.7 ms against
0.17 to 0.73 ms, and the line still sends about 2.8x the grid's reports (laptop
2.4x). Same trends, with the network adding delay.

To rerun:

```bash
cd Lab3_W12/caas
sbatch wsn_demo.job
for v in 1 2 3; do sbatch --export=ALL,VER=$v wsn_sweep.job; done
```
