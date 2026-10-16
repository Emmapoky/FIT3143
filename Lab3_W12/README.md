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
| Task 4, slides | both | Canva deck, exported to `Presentation_Slides.pdf` |

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
| `graphs/graph*.png` | Task 3 graphs; `graphs/per_type/` one graph per message type |
| `graphs/diagram*.png`, `graphs/code/` | slide diagrams and code cards (drawn from the source) |
| `scripts/` | `run_experiments.py`, `make_graphs.py`, `make_diagrams.py`, `make_code_cards.py` |
| `caas/` | CAAS job files (see the CAAS section) |
| `tests/test_evidence.txt` | edge cases, sanitizer and leak checks, bugs found |

## Reproducing Task 3

```bash
make
python3 scripts/run_experiments.py      # E1 to E5, about 70 minutes on a laptop, resumable
python3 scripts/make_graphs.py
```
