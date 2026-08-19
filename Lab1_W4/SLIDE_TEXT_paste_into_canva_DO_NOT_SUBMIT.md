# Canva paste sheet. PRIVATE. Delete after the lab.

## The 10 minute version

Only FOUR slides need work: 4, 5, 7 and 8. They are the graph slides with no words on them.

On each one: click the graph, drag its right edge left so it takes up about the left two thirds. Then add a text box in the gap on the right and paste the block below. Size about 26, same dark navy as the titles.

Everything else in the deck already has text. If you run out of time, do these four and stop.

---

# SLIDE 4  (Graphs 1 and 2, cream background)

Paste this into a text box on the right:

30 values of n, from 1M to 30M
14 threads throughout

Serial reaches 2.6 s at n = 30M
Threads stay under 0.4 s

Speedup sits between 7x and 10x
Average 8.09x across all 30 runs

---

# SLIDE 5  (Graphs 3 and 4, cream background)

Paste this into a text box on the right:

n fixed at 30M, threads 1 to 28

2 threads 2.00x
4 threads 3.93x
8 threads 7.79x

Almost perfect scaling to 8 threads
Goes flat at 14, our core count

Not 14x because of Amdahl's Law
and thread overhead

---

# SLIDE 7  (Graphs 5 and 6, dark navy background)

Paste this into a text box on the right. Make the text WHITE on this slide:

Same sweep, now with OpenMP
schedule(dynamic, 1000)

Steady 9x to 10x at every n
Average 9.37x

Schedules tested at n = 30M
static 9.55x
dynamic 10.44x
guided 10.42x

---

# SLIDE 8  (Graphs 7 and 8, dark navy background)

Paste this into a text box on the right. WHITE text:

Both parallel versions, same axes

OpenMP ahead almost everywhere
9.37x against 8.09x

Why OpenMP wins
dynamic scheduling adjusts as it runs
our rotation is fixed at the start
OpenMP reuses its thread team

---

# OPTIONAL: shorter speaker notes

The notes in Canva right now are long paragraphs. If you have time, replace them with these. Open Notes at the bottom of the Canva editor.

**Slide 1, ERWYNA, 15 sec**
We are Erwyna and Taabish. We found every prime below n three ways, serial, POSIX Threads and OpenMP, and measured the speedup. I did the serial code and the benchmarking, Taabish did both parallel versions.

**Slide 2, ERWYNA, 60 sec**
Serial is our baseline. Trial division but only up to the square root, because if k has a factor at least one is at or below the square root. Handle 2 separately, then only odd divisors.
Flag array, one byte per number. Read it front to back and it is already sorted.
We stop the timer before writing the file, because writing 664,579 lines is serial disk work and would hide the real speedup. All three programs agree by diff.

**Slide 3, TAABISH, 90 sec**
The question was how to split the numbers. Big numbers take more divisions than small ones, so the work is uneven.
First try, one block each. 8.70x. The thread with the big numbers finishes last and everyone waits. That is load imbalance.
Fix, chunks of 1000 in rotation, so every thread gets a mix. 9.75x.
No mutex, because each thread writes only its own slots. No race condition.

**Slide 4, ERWYNA, 45 sec**
Graphs 1 and 2, n from 1 to 30 million at 14 threads. Serial climbs to 2.6 seconds, threads stay under 0.4. Average 8.09x. The gap widens as n grows because the parallel version spreads the extra work across the cores.

**Slide 5, ERWYNA, 45 sec**
Graphs 3 and 4, n fixed, thread count changing. Nearly perfect to 8 threads. Flat after 14 because that is every core we have.
Why not 14x. Amdahl's Law, the serial parts cap it. And overhead, threads cost time to create and never finish together. Also 4 of our 14 cores are efficiency cores.

**Slide 6, TAABISH, 60 sec**
OpenMP does the same thing in one line. About 40 lines of thread code replaced by one pragma.
Static splits up front, dynamic hands out the next free chunk, guided starts big and shrinks. Our work gets heavier as numbers grow, so dynamic fits.
Gotcha, forget the fopenmp flag and the pragma is ignored. Runs on one thread, speedup shows exactly 1.00, no error.

**Slide 7, TAABISH, 45 sec**
Graphs 5 and 6, same sweep for OpenMP. Steady 9 to 10x, average 9.37x, slightly ahead of pthreads.
We timed all three schedules at 30 million. Dynamic beat static by about 9 percent, so the load balancing argument is measured, not guessed.

**Slide 8, ERWYNA, 30 sec**
Graphs 7 and 8, the two side by side. OpenMP slightly faster almost everywhere. Dynamic scheduling adjusts while running, ours is fixed at the start, and OpenMP reuses its threads.

**Slide 9, ERWYNA, 15 sec**
In one line, 9.37x against 8.09x, and one pragma against 40 lines. OpenMP wins on both here.

**Slide 10, ERWYNA, 45 sec**
Four things. Speedup is near linear while real cores back it, then flat. How you split the work matters when cost per item is uneven, chunking took us 8.70 to 9.75x and dynamic gave another 9 percent. The flag array gave sorted output and no mutex. More threads than cores gives nothing.
Limitation, trial division is not the fastest way. A segmented Sieve of Eratosthenes would be much faster and splits by segment, but is harder and uses more memory.
Recommendation, OpenMP for loop work like this, pthreads when you need fine control.
Thanks, happy to take questions.

**Slide 11, BOTH**
Leave this up during questions. Short answers, proper terms, stop when answered.

**Slide 12**
Appendix. Only if asked how we measured.

**Slide 13**
Just say thanks.

---

Total about 7 min 30. Erwyna 4:15, Taabish 3:15. Target is 6 to 8.
