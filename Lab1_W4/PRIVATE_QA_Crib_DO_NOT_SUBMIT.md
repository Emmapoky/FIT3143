# Lab 1 prep sheet. PRIVATE. Do not submit. Delete after the lab.

Numbers are from our run on 19 Aug 2026. Apple M3 Max, 14 cores (10 performance, 4 efficiency).

## Who did what

**Erwyna**
* task1.c, the serial version
* run_benchmarks.sh, runs everything and collects the timings
* make_graphs.py, draws the graphs
* Ran all the benchmarks, made the slides

**Taabish**
* task2.c, POSIX Threads version
* task3.c, OpenMP version

Either of us can be asked about any part, so both read all three files.

## Numbers to memorise

* 664,579 primes below 10 million
* Serial at n = 30M takes 2.6 seconds
* Pthreads: 8.09x average over 30 values of n
* OpenMP: 9.37x average over 30 values of n
* 2 threads = 2.00x, 4 threads = 3.93x, 8 threads = 7.79x (almost perfect)
* After 14 threads it goes flat around 9.7x to 10.4x
* Block vs chunk: 8.70x vs 9.75x
* static 9.55x, dynamic 10.44x, guided 10.42x

## How the code works, in plain words

**Prime test (all three files use the same one)**
Only check divisors up to the square root of k. Reason: if k = a x b, a and b cannot both be above the square root because then a x b would be bigger than k. Skip even numbers, handle 2 on its own.

**Flag array**
One byte per number. Mark it 1 if prime. Read front to back and it is already in order, no sorting. Each thread only writes to its own slots so they never clash. That is why there is no mutex.

**Task 2 chunks**
First we gave each thread one big block. Slow, because big numbers take longer to check, so the thread with the big numbers finishes last and the rest wait. Fix: hand out chunks of 1000 in a rotation (thread 0 gets chunk 0, thread 1 gets chunk 1, and so on, then wrap around). Now every thread has a mix of easy and hard numbers.

**Task 3 schedule(dynamic, 1000)**
OpenMP does the chunk handing out for us. Dynamic means a thread grabs the next free chunk when it finishes. Static decides it all up front. Guided starts big and shrinks. We tested all three, dynamic won.

**Why stop the timer before the file write**
Writing 664,579 lines to a file is slow and cannot be made parallel. If we included it the speedup would look worse than it really is.

## The two questions from the spec (they WILL ask these)

**Q. Is the speedup exactly equal to the number of threads? Why not? Give two reasons.**
No. Reason 1: Amdahl's Law. Some parts cannot be made parallel (allocating memory, creating threads, joining them). That part stays the same no matter how many threads, so it caps the speedup. Reason 2: overhead and load imbalance. Creating and managing threads costs time, and threads never finish at exactly the same moment. Extra: 4 of our 14 cores are efficiency cores, so 14x was never really possible on this laptop.

**Q. Would you recommend OpenMP over POSIX Threads?**
For this kind of problem, yes. One pragma replaced about 40 lines of thread code and it was actually a bit faster (9.37x vs 8.09x) because dynamic scheduling balances the work at run time. I would use pthreads when you need fine control, like producer consumer pipelines or when each thread needs its own state that is not just a loop.

## Other likely questions

**Q. How did you split the work? Is it a good way?**
Chunks of 1000 in rotation, so every thread gets a mix of small and big numbers. Good here because the work gets heavier in a predictable way as numbers get bigger. If the work was random it would be better to use dynamic scheduling, which is what OpenMP does.

**Q. Where is the critical section? Why no mutex?**
There is none on purpose. Each thread writes to different spots in the array, so no race. A mutex would only slow it down.

**Q. What happens with more threads than cores?**
Goes flat. Past 14 threads there are no more cores, the extra threads just take turns. You can see it in graph 4.

**Q. Why the square root?**
If k has a factor, at least one factor is at or below the square root. So checking up to there is enough.

**Q. How would you make it faster?**
A segmented Sieve of Eratosthenes. Much better complexity than trial division and you can parallelise by segment. Harder to write and uses more memory.

**Q. How did you check it is correct?**
All three programs write their primes to a file, we diff the files and they match, and the count is 664,579 which is the known number of primes below 10 million.

**Q. Why 30 values of n?**
The spec asks for at least 30. We went 1M to 30M in steps of 1M.

**Q. Why is the OpenMP one faster than your pthreads one?**
Dynamic scheduling adapts while the program runs, our rotation is fixed from the start. Also OpenMP reuses its threads instead of creating new ones each time.

**Q. What does the fopenmp flag do?**
Turns the pragmas on. Without it the compiler ignores them and the program runs on one thread. Speedup shows exactly 1.00 and no error, so it is easy to miss.

## Words to use (markers want parallel computing terms)

speedup, workload partitioning, load imbalance, race condition, critical section, Amdahl's Law, fork and join, cyclic distribution, dynamic scheduling, granularity

## On the day

* Keep answers short. Answer the question and stop.
* No phones, no laptops, no AI during Q&A. Auto fail.
* If you do not know, say what you do know and reason it out loud.
