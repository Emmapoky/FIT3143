# FIT3143 Lab 1 Presentation Script

Target: 7 minutes of speaking, then 1 to 2 minutes of Q&A. The rubric rewards a
presentation that lands between 6 and 8 minutes, so 7:00 is the aim point.
Numbers below are from the 18 Aug 2026 run on the Apple M3 Max, 14 cores.

---

## Slide 1, Title. ERWYNA. 0:00 to 0:15

Hi everyone, we are Erwyna and Taabish. Our lab task was to find every prime
number strictly below a limit n, three ways: a serial baseline, POSIX Threads,
and OpenMP, and then measure exactly what parallelism buys us. I wrote the
serial version and ran all the benchmarks, Taabish wrote both parallel versions.

## Slide 2, Task 1 serial baseline. ERWYNA. 0:15 to 1:15

The serial program is the baseline every speedup is measured against, so it has
to be correct and it has to be honest. The prime test uses trial division, but
only up to the square root of k. If k factorises as m times p, both factors
cannot sit above the square root, so if no divisor exists at or below it, k is
prime. We handle 2 separately, then step through odd divisors only, which
halves the divisions again.

Results are stored in a flag array, one byte per candidate. Reading that array
front to back gives the sorted ascending list for free, no sorting step at all.
Small n prints to the terminal, large n writes to a text file.

One design decision to flag: we stop the timer before the file write. Writing
664,579 lines is serial disk work. Including it would understate every speedup
we report. All three programs report 664,579 primes below ten million and their
output files are identical by diff, which is our correctness proof.

## Slide 3, Task 2 partitioning scheme. TAABISH. 1:15 to 2:45

For POSIX Threads the real design question is how to split the range between
threads, because the cost of testing a candidate is not uniform. The divisor
loop runs to the square root of k, so large candidates cost more divisions than
small ones.

Our first attempt gave each thread one contiguous block, like the vector cell
product example from the lab prep. That works, but the thread holding the top
of the range is still grinding through expensive candidates long after the
others have finished, and everyone waits for it at the join. That is load
imbalance, and it cost us: one block per thread reached 8.70x on 14 threads.

So we moved to cyclic chunk distribution. Chunks of one thousand numbers are
dealt out in rotation, thread 0, thread 1, and so on, wrapping around until the
range is exhausted. Every thread now holds a mix of cheap and expensive
candidates, so they finish together. Same machine, same n, 9.75x.

And there is deliberately no mutex anywhere. Each flag array element is written
by exactly one thread, the writes are disjoint, so no race condition exists and
locking would only serialise the hot loop.

## Slide 4, Task 2 results. ERWYNA. 2:45 to 4:15

Graphs one and two sweep n from one million to thirty million at 14 threads.
Serial time grows to 2.6 seconds at n equals thirty million, the threaded
version stays under 0.4 seconds, and speedup holds between 7x and 10x across
the whole sweep, averaging 8.09x over all 30 values of n.

Graphs three and four hold n at thirty million and sweep the thread count from
1 to 28. This is the interesting one. Speedup tracks the ideal line almost
perfectly to 8 threads: 2 threads give 2.00x, 4 give 3.93x, 8 give 7.79x. Past
8 it bends, and past 14 threads it plateaus just under 10x, because 14 is every
core this machine has. Beyond that there is no hardware left, extra threads
just take turns on the same cores and add scheduling overhead.

Why is speedup not equal to the thread count? Two reasons. First, Amdahl's
Law: the serial fraction, the memory allocation, thread creation and the join,
caps speedup no matter how many threads we add. Second, parallel overhead and
load imbalance: creating and scheduling threads costs time that does no
searching, and threads never finish perfectly together. On this machine there
is also a hardware detail: ten of the fourteen cores are performance cores and
four are efficiency cores, so the ideal of 14x was never truly available. That
is also why one thread gives 1.02x rather than exactly 1: one worker on a
performance core matches the serial baseline almost exactly.

## Slide 5, Task 3 OpenMP. TAABISH. 4:15 to 5:15

Task 3 asks the same question with OpenMP. The entire parallel machinery of
task two, creating threads, computing chunk boundaries, joining, becomes one
pragma: parallel for with schedule dynamic and a chunk size of one thousand.
Roughly forty lines of bookkeeping replaced by one line, and the loop body is
untouched.

The schedule clause is where the partitioning thinking from task two carries
over. Static hands out fixed blocks up front, dynamic lets each thread pull the
next chunk when it finishes, guided starts with big chunks and shrinks them.
Because our workload is skewed toward large candidates, dynamic is the natural
fit, and unlike our hand rolled rotation it adapts at run time.

One practical warning: compile without the fopenmp flag and the pragma is
silently ignored. The program still runs, on one thread, and reports a speedup
of exactly one. We hit that early and it is a useful diagnostic to know.

## Slide 6, Task 3 results. TAABISH. 5:15 to 5:45

Graphs five and six repeat the n sweep for OpenMP. Speedup is steady between
9x and 10x across all 30 values of n, averaging 9.37x, slightly ahead of our
pthread version. We also measured the three schedules directly at n equals
thirty million: static 9.55x, dynamic 10.44x, guided 10.42x. Dynamic beat
static by about nine percent, which confirms the load imbalance argument with
a measurement rather than a guess.

## Slide 7, head to head. ERWYNA. 5:45 to 6:15

Graphs seven and eight put the two parallel versions on the same axes. OpenMP
is consistently a little faster, 9.37x against 8.09x averaged over the n sweep,
because dynamic scheduling adapts while our cyclic rotation is fixed at launch,
and the OpenMP runtime reuses its thread team instead of creating threads per
run. So on this workload OpenMP wins on both speed and simplicity.

## Slide 8, conclusion. ERWYNA. 6:15 to 7:00

Four things we learned. Speedup scales near linearly while there is real
hardware to back it, then plateaus at the core count, exactly as Amdahl and
the hardware predict. Workload distribution is the whole game when per item
cost varies: chunking lifted pthreads from 8.70x to 9.75x, and dynamic
scheduling gave OpenMP another nine percent over static. The flag array bought
us sorted output and freedom from mutexes at the same time. And more threads
than cores buys nothing.

Limitations and future work: trial division is not the fastest prime algorithm.
A segmented Sieve of Eratosthenes would drop the complexity class entirely and
parallelises naturally by segment, at the cost of a more complex implementation.
Our recommendation: OpenMP for loop shaped parallelism like this, POSIX Threads
when you need fine control over thread lifetime and communication patterns.

Thank you. We are happy to take questions.

---

## Q&A period, 1 to 2 minutes

Each of us can be asked one to two questions. Short crib answers are in the
private prep sheet. Speak in parallel computing terms: speedup, load imbalance,
partitioning, race condition, critical section, Amdahl's Law.
