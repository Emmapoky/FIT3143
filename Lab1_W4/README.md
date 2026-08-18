# FIT3143 Lab #1, Threads & OpenMP

Erwyna Soo Wen Xin (36555789) and Taabish Farooq Bhat (35473932)

Finding every prime number strictly below n, three ways, and comparing how fast they run.

## Who did what

| Part | Owner |
|---|---|
| Task 1, serial code (`task1.c`) | Erwyna |
| Task 2, POSIX Threads (`task2.c`) | Taabish |
| Task 3, OpenMP (`task3.c`) | Taabish |
| Task 4, benchmarking, graphs and slides | Erwyna |

## Before submitting

1. **The benchmarks were re-run on the submission machine on 18 Aug 2026** (Apple M3 Max,
   14 cores: 10 performance and 4 efficiency, macOS 26.6.1). Every number in the CSVs,
   the graphs and the Canva deck now comes from that run. To repeat it:
   ```bash
   chmod +x run_benchmarks.sh
   ./run_benchmarks.sh          # 30 values of n up to 30M, threads 1 to 28, best of 3
   CORES=14 N_FIXED=30000000 python3 make_graphs.py
   ```
   Note: `Slides_Reference.html` still shows the numbers from the old 2 core draft run.
   The Canva deck is the live copy, so treat the HTML as superseded.

2. **Fill in `AI_Declaration.md`**, including the tool name, then export it to PDF and attach
   your prompt records as `AI_Prompt_Records.pdf`.

3. **Build the slides in Canva** using `Slides_Reference.html` as the source of the text, and
   upload the PNGs from the `graphs` folder.

## Files

| File | What it is |
|---|---|
| `task1.c` | Task 1, serial prime search |
| `task2.c` | Task 2, POSIX Threads with chunked workload distribution |
| `task3.c` | Task 3, OpenMP |
| `run_benchmarks.sh` | Builds everything, checks correctness, runs the three sweeps |
| `make_graphs.py` | Draws the eight required graphs plus our comparison graph |
| `Slides_Reference.html` | All the slide text with copy buttons, split by presenter |
| `AI_Declaration.md` | Declaration form, needs filling in |
| `results_*.csv` | The raw timings |
| `graphs/` | The nine graphs |

## Building and running

```bash
gcc task1.c -o task1 -lm                # -lm links sqrt from math.h
gcc task2.c -o task2 -lm -lpthread      # -lpthread links POSIX threads
gcc task3.c -o task3 -lm -fopenmp       # -fopenmp turns the pragmas on

./task1 100                             # small n prints to the terminal
./task1 10000000                        # large n writes primes_serial.txt
./task2 10000000 8                      # n then thread count
./task3 10000000 8                      # n then thread count
```

If you leave `-fopenmp` off, `task3` still compiles and runs but ignores the pragma and uses
one thread, so the speedup comes out as exactly 1.00 with no error message.

## Checking it works

All three have to produce the same list.

```bash
diff primes_serial.txt primes_pthread.txt
diff primes_serial.txt primes_omp.txt
head -1 primes_serial.txt        # should be 664579
```

There are 664,579 primes below ten million. `run_benchmarks.sh` checks this before it times
anything.

## How it works, briefly

**The prime test.** We only divide by numbers up to the square root of k. If k is not prime it
factorises as k = m x p, and m and p cannot both be above the square root, because multiplying
them would overshoot k. So if a factor exists, one of them is at or below the square root. We
handle 2 separately so the loop can step by 2 and skip all the even divisors.

**Storing the answers.** One byte per number in a flag array. We mark a position when we find a
prime, and reading the array back from the front gives ascending order without sorting. Because
each thread only writes to the positions it was handed, no two threads ever touch the same
element, so there is no race condition and no mutex anywhere.

**Splitting the work in Task 2.** We first gave each thread one big block, like the vector cell
product example from the Week 3 lab prep. That reached 8.70x on 14 threads, because checking a
big number takes more divisions than checking a small one, so the thread holding the high numbers
finishes long after the others. Handing out chunks of 1000 numbers in rotation instead gives every
thread a mix of cheap and expensive numbers, and that took us to 9.75x.

**Splitting the work in Task 3.** `schedule(dynamic, 1000)` does the same job automatically, and
adapts at run time instead of following a fixed rotation. On 14 threads dynamic beat static by
about 9 percent (10.44x against 9.55x), with guided level with dynamic, so the choice of dynamic
is now backed by our own measurement rather than reasoning alone.

## Reference numbers, Apple M3 Max (14 cores), n = 30,000,000, 14 threads

| Version | Time | Speedup |
|---|---|---|
| Serial | 2.62s | 1.00x |
| POSIX Threads, chunks | 0.27s | 9.75x |
| OpenMP, schedule(dynamic, 1000) | 0.25s | 10.44x |
| POSIX Threads, one block per thread | 0.30s | 8.70x |
| OpenMP, schedule(static, 1000) | 0.27s | 9.55x |
| OpenMP, schedule(guided, 1000) | 0.25s | 10.42x |

Averaged over 30 values of n at 14 threads: POSIX Threads 8.09x, OpenMP 9.37x.
Thread sweep at n = 30M: near linear to 8 threads, then a plateau around 9.7x to 10.4x.
The plateau sits below 14 because 4 of the 14 cores are efficiency cores, and past 14
threads there is no more hardware so extra threads only add scheduling overhead.
