# FIT3143 Lab 1 Presentation Script (final 13 page deck)

Target: about 7 and a half minutes of speaking, then 1 to 2 minutes of Q&A.
The rubric rewards 6 to 8 minutes, so this lands comfortably inside the band.
All numbers from the 18 Aug 2026 run on the Apple M3 Max, 14 cores.

## Slide 1, Title. ERWYNA. 0:00 to 0:15

Hi everyone, we are Erwyna and Taabish. Our task was to find every prime
number strictly below a limit n three ways: a serial baseline, POSIX Threads,
and OpenMP, and then measure exactly what parallelism buys us. I wrote the
serial version and ran all the benchmarks, Taabish wrote both parallel
versions.

## Slide 2, Task 1 serial baseline. ERWYNA. 0:15 to 1:15

The serial program is the baseline every speedup is measured against, so it
has to be correct and honest. The prime test uses trial division, but only up
to the square root of k. If k factorises as m times p, both factors cannot
sit above the square root, so if no divisor exists at or below it, k is
prime. We handle 2 separately, then step through odd divisors only, which
halves the divisions again.

Results go into a flag array, one byte per candidate. Reading it front to
back gives the sorted ascending list for free, no sorting step. Small n
prints to the terminal, large n writes to a text file.

One design decision to flag: we stop the timer before the file write, because
writing 664,579 lines is serial disk work and including it would understate
every speedup. All three programs report 664,579 primes below ten million and
their output files are identical by diff, which is our correctness proof.

## Slide 3, Task 2 partitioning. TAABISH. 1:15 to 2:45

For POSIX Threads the real design question is how to split the range, because
the cost of testing a candidate is not uniform. The divisor loop runs to the
square root of k, so large candidates cost more divisions than small ones.

Our first attempt gave each thread one contiguous block, like the vector cell
product example from the lab prep. It works, but the thread holding the top
of the range is still grinding through expensive candidates long after the
others finish, and everyone waits for it at the join. That load imbalance
cost us: one block per thread reached 8.70x on 14 threads.

So we moved to cyclic chunk distribution. Chunks of one thousand numbers are
dealt out in rotation, thread 0, thread 1 and so on, wrapping until the range
is exhausted. Every thread holds a mix of cheap and expensive candidates, so
they finish together. Same machine, same n, 9.75x.

And there is deliberately no mutex. Each flag array element is written by
exactly one thread, the writes are disjoint, so no race condition exists and
locking would only serialise the hot loop.

## Slide 4, graphs 1 and 2. ERWYNA. 2:45 to 3:30

Graphs one and two sweep n from one million to thirty million at 14 threads.
Serial time grows to 2.6 seconds at n equals thirty million, the threaded
version stays under 0.4 seconds, and speedup holds between 7x and 10x across
the whole sweep, averaging 8.09x over all 30 values of n. The gap widens as
n grows because the parallel version spreads the growing work across every
core while the serial version carries it alone.

## Slide 5, graphs 3 and 4. ERWYNA. 3:30 to 4:15

Graphs three and four hold n at thirty million and sweep the thread count
from 1 to 28. Speedup tracks the ideal line almost perfectly to 8 threads: 2
threads give 2.00x, 4 give 3.93x, 8 give 7.79x. Past 8 it bends, and past 14
threads it plateaus just under 10x, because 14 is every core this machine
has.

Why is speedup not equal to the thread count? Two reasons. First, Amdahl's
Law: the serial fraction, the memory allocation, thread creation and the
join, caps speedup no matter how many threads we add. Second, parallel
overhead and load imbalance: creating and scheduling threads costs time that
does no searching, and threads never finish perfectly together. On this
machine there is also a hardware detail: ten of the fourteen cores are
performance cores and four are efficiency cores, so the ideal of 14x was
never truly available.

## Slide 6, Task 3 OpenMP approach. TAABISH. 4:15 to 5:15

Task 3 asks the same question with OpenMP. The entire parallel machinery of
task two, creating threads, computing chunk boundaries, joining, becomes one
pragma: parallel for with schedule dynamic and a chunk size of one thousand.
Roughly forty lines of bookkeeping replaced by one line, and the loop body is
untouched.

The schedule clause is where the partitioning thinking carries over. Static
hands out fixed blocks up front, dynamic lets each thread pull the next chunk
when it finishes, guided starts with big chunks and shrinks them. Because our
workload is skewed toward large candidates, dynamic is the natural fit, and
unlike our hand rolled rotation it adapts at run time.

One practical warning: compile without the fopenmp flag and the pragma is
silently ignored. The program runs on one thread and reports a speedup of
exactly one. We hit that early and it is a useful diagnostic to know.

## Slide 7, graphs 5 and 6. TAABISH. 5:15 to 6:00

Graphs five and six repeat the n sweep for OpenMP. Speedup is steady between
9x and 10x across all 30 values of n, averaging 9.37x, slightly ahead of our
pthread version. We also measured the three schedules directly at n equals
thirty million: static 9.55x, dynamic 10.44x, guided 10.42x. Dynamic beat
static by about nine percent, which turns the load imbalance argument from a
guess into a measurement. That chart is in the appendix.

## Slide 8, graphs 7 and 8. ERWYNA. 6:00 to 6:30

Graphs seven and eight put the two parallel versions on the same axes. OpenMP
is consistently a little faster, 9.37x against 8.09x averaged over the n
sweep. Two reasons: dynamic scheduling adapts at run time while our cyclic
rotation is fixed at launch, and the OpenMP runtime reuses its thread team
instead of creating fresh threads.

## Slide 9, head to head summary. ERWYNA. 6:30 to 6:45

So the head to head in one line: 9.37x against 8.09x on average, and one
pragma against roughly forty lines of thread management. On this workload
OpenMP wins on both speed and simplicity.

## Slide 10, conclusion. ERWYNA. 6:45 to 7:30

Four things we learned. Speedup scales near linearly while there is real
hardware behind it, then plateaus at the core count, exactly as Amdahl and
the hardware predict. Workload distribution is the whole game when per item
cost varies: chunking lifted pthreads from 8.70x to 9.75x, and dynamic gave
OpenMP another nine percent over static. The flag array bought us sorted
output and freedom from mutexes at the same time. And more threads than
cores buys nothing.

Limitations and future work: trial division is not the fastest prime
algorithm. A segmented Sieve of Eratosthenes would improve the complexity
class and parallelises naturally by segment, at the cost of a more complex
implementation and more memory per segment.

Our recommendation: OpenMP for loop shaped parallelism like this, POSIX
Threads when you need fine control over thread lifetime and per thread state.

Thank you. We are happy to take questions.

## Slide 11, Q&A. BOTH. 1 to 2 minutes

Leave the key numbers slide up. Answer in parallel computing terms: speedup,
workload partitioning, load imbalance, race condition, Amdahl's Law. Short
answers, stop when the question is answered. Slide 12 is a clearly labelled
appendix with the benchmark method and the workload comparison chart, only
shown if a question calls for it. Slide 13 closes.
