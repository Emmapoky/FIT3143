# PRIVATE prep sheet. Do not submit. Delete after the lab.

All numbers from the 18 Aug 2026 run. Apple M3 Max, 14 cores, 10 performance
and 4 efficiency, macOS 26.6.1, gcc and clang at O2.

## What I did (Erwyna)

* task1.c, the serial baseline. Trial division to the square root, odd
  divisors only, 2 handled separately. Flag array, one byte per candidate,
  read front to back for sorted output. Timer stops before the file write.
* run_benchmarks.sh. Builds all four binaries, checks the three programs
  agree by diff and against the known count 664,579, then runs three sweeps:
  30 values of n from 1M to 30M, threads 1 to 28 at n = 30M, and the two
  workload comparisons. Each timing is the best of three runs.
* make_graphs.py, draws the eight required graphs plus the extra comparison.
* The benchmark run itself, the slides and the speaker notes.

## What Taabish did

* task2.c, POSIX Threads. Global n, thread count and flag array. Fork and
  join with pthread_create and pthread_join. Cyclic chunk distribution:
  chunk index starts at my rank and advances by the thread count, chunk size
  1000. The block version is kept behind a compile flag called USE_BLOCK for
  the comparison.
* task3.c, OpenMP. One parallel for pragma with schedule dynamic 1000.
  Thread count set from the command line when given. Same IsPrime and same
  file writer as the others so the comparison is fair.

## Numbers to have cold

* 664,579 primes below ten million. All three outputs identical by diff.
* Serial at n = 30M: 2.62 seconds.
* Pthread at 14 threads, n = 30M: 9.17x. Average across the 30 n values: 8.09x.
* OpenMP at 14 threads, n = 30M: 10.03x. Average across the n sweep: 9.37x.
* Near linear early: 2 threads 2.00x, 4 threads 3.93x, 8 threads 7.79x.
* Plateau past 14 threads at roughly 9.7x to 10.4x. No collapse, just flat.
* Block 8.70x against chunk 9.75x, both at 14 threads.
* Schedules at n = 30M: static 9.55x, dynamic 10.44x, guided 10.42x.

## The two questions the spec itself names

Q. Is the speedup exactly equal to the number of threads? Why not, two reasons.
A. No. One, Amdahl's Law: the serial fraction, memory allocation, thread
   creation and join, caps speedup no matter the thread count. Two, load
   imbalance and hardware: per candidate cost grows with the square root, and
   4 of our 14 cores are efficiency cores, so equal shares do not finish
   together and the ideal of 14x was never available on this chip.

Q. Would you recommend OpenMP over POSIX Threads?
A. For this workload yes. Same parallelism from one pragma instead of forty
   lines, and it measured faster, 9.37x against 8.09x on average, because
   dynamic scheduling adapts at run time while our cyclic rotation is fixed.
   I would still pick pthreads when the parallelism is not loop shaped, say a
   producer consumer pipeline, or when I need control of thread lifetime,
   affinity or per thread state.

## Questions likely aimed at me (Erwyna)

Q. Why stop the timer before writing the file?
A. The write is serial disk work. Including it would understate the speedup.
   It is the serial fraction of Amdahl's Law made visible, so we report
   computation time and keep the write outside it.

Q. Why is one thread 1.02x and not exactly 1.00x?
A. Measurement noise plus scheduling. One worker on a performance core runs
   the same loop as the serial program, so the times match to within a couple
   of percent. Anything near 1 is the expected answer.

Q. Why best of three runs?
A. The slowest runs carry interference from whatever else the machine was
   doing. The fastest run is the closest estimate of the true cost of the
   computation itself, and it makes the sweep repeatable.

Q. How do you know the parallel output is correct?
A. Three ways. diff says all three files are byte identical, the count is
   664,579 which matches the known prime count below ten million, and the
   flag array construction cannot produce an unsorted list.

Q. Why does speedup keep creeping up past 14 threads, 9.17x at 14 but 9.7x
   at 28?
A. With more threads each one owns a smaller slice, so a slow efficiency
   core holds a smaller share of the tail and the finish line evens out. It
   is finer grained balancing, not extra hardware.

## Questions likely aimed at Taabish

Q. Where is the race condition in task2, and why is there no mutex?
A. There is none by construction. Each element of the flag array is written
   by exactly one thread, writes are disjoint, shared reads are read only
   after setup. A mutex would serialise the hot loop for nothing.

Q. Why chunk size 1000?
A. Small enough that each thread gets many chunks from all over the range,
   which is what balances the load. Large enough that the loop overhead per
   chunk is negligible. We did not tune it further because the schedule
   comparison showed the remaining gap between strategies is about 9 percent.

Q. What exactly does schedule dynamic do differently from your task2 scheme?
A. Our task2 rotation is decided at launch: chunk assignments are fixed by
   rank. Dynamic keeps a shared queue of chunks and each thread pulls the
   next when it finishes, so it adapts to whatever imbalance shows up while
   running. That adaptivity is the measured 9 percent over static.

Q. What happens with more threads than cores?
A. No new parallelism, the OS time slices them onto the same 14 cores. Our
   graph 4 shows the plateau. Cost is context switching and scheduler
   pressure, benefit is only the finer grained balancing already mentioned.

## If asked about hardware

Apple M3 Max, 14 cores, no simultaneous multithreading, so 14 hardware
threads. 10 performance cores and 4 efficiency cores, which is why the
plateau sits near 10x rather than 14x.

## If asked what we would do next

Segmented Sieve of Eratosthenes. Better complexity class, cache friendly
segments, and segments parallelise naturally. Trade is implementation
complexity and memory per segment.

## Honesty line if AI comes up

We used generative AI during the preparation period as the spec allows,
declared it, and attached the prompt records. Nothing AI touches the room:
no tools during the presentation or Q&A.
