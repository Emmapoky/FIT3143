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

1. **Run the benchmarks on your own laptop.** The numbers currently in the CSVs and in
   `Slides_Reference.html` came from a 2 core test machine. The Q&A will ask about your
   hardware, so the figures should be yours.
   ```bash
   chmod +x run_benchmarks.sh
   ./run_benchmarks.sh          # takes a while, raise N_MAX if your machine is fast
   python3 make_graphs.py       # redraws all nine graphs from your CSVs
   ```
   Then update every highlighted number in `Slides_Reference.html` before building the deck.

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
product example from the Week 3 lab prep. That only reached 1.58x on 2 cores, because checking a
big number takes more divisions than checking a small one, so the thread holding the high numbers
finishes long after the others. Handing out chunks of 1000 numbers in rotation instead gives every
thread a mix of cheap and expensive numbers, and that took us to 1.95x.

**Splitting the work in Task 3.** `schedule(dynamic, 1000)` does the same job automatically. We
timed static, dynamic and guided and they came out within about 5 percent of each other on our
machine, so we cannot claim one won. We kept dynamic because the reasoning still holds and the
difference should grow on a machine with more cores.

## Reference numbers, 2 core machine, n = 10,000,000

| Version | Time | Speedup |
|---|---|---|
| Serial | 7.43s | 1.00x |
| POSIX Threads, 2 threads | 3.84s | 1.93x |
| OpenMP, 2 threads | 3.79s | 1.96x |
| POSIX Threads, one block per thread | 4.71s | 1.58x |

Averaged over 30 values of n: POSIX Threads 1.92x, OpenMP 1.95x.
