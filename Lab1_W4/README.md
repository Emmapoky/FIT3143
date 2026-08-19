# FIT3143 Lab 1: Threads and OpenMP

Erwyna Soo Wen Xin (36555789) and Taabish Farooq Bhat (35473932)

We find every prime number below n three ways (serial, POSIX Threads, OpenMP) and compare how fast each one runs.

## Who did what

| Part | Who |
|---|---|
| Task 1, serial code (`task1.c`) | Erwyna |
| Task 2, POSIX Threads (`task2.c`) | Taabish |
| Task 3, OpenMP (`task3.c`) | Taabish |
| Task 4, benchmarking and graphs (`run_benchmarks.sh`, `make_graphs.py`) | Erwyna |

## Files

| File | What it is |
|---|---|
| `task1.c` | Serial prime search |
| `task2.c` | POSIX Threads version, work handed out in chunks |
| `task3.c` | OpenMP version |
| `run_benchmarks.sh` | Builds everything, checks the outputs match, runs the timing sweeps |
| `make_graphs.py` | Draws the 8 required graphs plus one extra comparison |
| `results_by_n.csv` | Timings for 30 values of n (1M to 30M), 14 threads |
| `results_by_threads.csv` | Timings for 1 to 28 threads, n = 30M |
| `results_extra.csv` | Block vs chunk, and the three OpenMP schedules |
| `graphs/` | The 9 graphs as PNG |

## Build and run

```bash
gcc task1.c -o task1 -lm
gcc task2.c -o task2 -lm -lpthread
gcc task3.c -o task3 -lm -fopenmp

./task1 100              # small n prints to terminal
./task1 10000000         # big n writes primes_serial.txt
./task2 10000000 8       # n, then number of threads
./task3 10000000 8
```

On a Mac with Apple clang, `-fopenmp` on its own does not work. You need libomp from Homebrew:

```bash
clang task3.c -o task3 -lm -Xpreprocessor -fopenmp -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp
```

`run_benchmarks.sh` picks the right one automatically. If you forget `-fopenmp` the program still compiles and runs but ignores the pragma, so it runs on one thread and the speedup comes out as exactly 1.00.

## Checking it works

All three have to give the same list. There are 664,579 primes below ten million.

```bash
diff primes_serial.txt primes_pthread.txt
diff primes_serial.txt primes_omp.txt
head -1 primes_serial.txt      # 664579
```

The benchmark script does this check before it times anything.

## How it works

**Prime test.** Only check divisors up to the square root of k. If k = m x p, m and p cannot both be bigger than the square root or the product would be bigger than k. Handle 2 on its own, then step by 2 so we skip even divisors.

**Storing the answer.** One byte per number in a flag array. Mark the spot when we find a prime, read the array front to back and it is already sorted. Each thread only writes to the spots it was given, so no two threads ever touch the same element. No race condition, no mutex needed.

**Splitting the work in Task 2.** First try was one big block per thread, same as the vector cell product example from the Week 3 lab prep. That only got 8.70x on 14 threads. The problem is that big numbers take more divisions to check than small ones, so the thread with the high numbers finishes last and everyone waits for it. Handing out chunks of 1000 in rotation instead gives every thread a mix of small and big numbers, and that got 9.75x.

**Splitting the work in Task 3.** `schedule(dynamic, 1000)` does the same thing but OpenMP handles it. We timed static, dynamic and guided at n = 30M. Dynamic was about 9 percent faster than static (10.44x vs 9.55x), guided was in between.

## Our numbers

Apple M3 Max, 14 cores (10 performance, 4 efficiency). Each timing is the best of 3 runs, computation only, file writing not included.

| | Speedup |
|---|---|
| POSIX Threads, average over 30 values of n | 8.09x |
| OpenMP, average over 30 values of n | 9.37x |
| POSIX Threads, best with 28 threads | 9.71x |
| OpenMP, best with 28 threads | 10.45x |

Speedup goes up almost one to one until about 8 threads, then flattens out around 14, which is the core count.
