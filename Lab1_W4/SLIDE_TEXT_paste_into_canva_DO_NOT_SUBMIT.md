# Slide text to paste into Canva. PRIVATE. Delete after.

Each slide: the bullets that go ON the slide (so you can read them while presenting), then the notes (short, what to actually say). Speaker and rough time at the top.

How to use: open the slide in Canva, add a text box on the empty side (or shrink the graph to the left half), paste the bullets. Then open Notes at the bottom and paste the notes.

If you want to, you can split any graph slide into two (one graph + bullets each). Totally fine for time.

---

## Slide 1, Title. ERWYNA, 15 sec

Notes:
Hi, we are Erwyna and Taabish. We found every prime below n three ways, serial, POSIX Threads and OpenMP, and measured how much faster the parallel ones are. I did the serial code and all the benchmarking, Taabish did both parallel versions.

---

## Slide 2, Task 1 serial. ERWYNA, 60 sec

Already has bullets. Keep as is.

Notes:
Serial version is the baseline. Prime test is trial division but only up to the square root, because if k has a factor at least one of them is at or below the square root. Handle 2 separately, then only test odd divisors.

Results go in a flag array, one byte per number. Read it front to back and it is already sorted, no sort step.

We stop the timer before writing the file because writing 664,579 lines is serial disk work and would make the speedup look worse. All three programs give 664,579 primes below 10 million and the output files match by diff. That is our correctness check.

---

## Slide 3, Task 2 how we split the work. TAABISH, 90 sec

Already has bullets (8.70x block, 9.75x chunks, the diagram, NO MUTEX). Keep.

Notes:
For pthreads the big question was how to split the numbers between threads. Checking a big number takes more divisions than a small one, so the work is not even.

First try: one big block per thread, like the Week 3 lab example. Got 8.70x on 14 threads. Problem is the thread with the big numbers finishes last and everyone waits at the join. That is load imbalance.

Fix: chunks of 1000 handed out in rotation. Thread 0 gets chunk 0, thread 1 gets chunk 1, wrap around. Every thread gets a mix of easy and hard numbers. Same machine, 9.75x.

No mutex anywhere. Each thread only writes its own spots in the array so there is no race condition.

---

## Slide 4, Graphs 1 and 2. ERWYNA, 45 sec

Bullets to add on slide:
* 30 values of n, 1M to 30M, 14 threads
* Serial hits 2.6 s at 30M, pthreads stays under 0.4 s
* Speedup between 7x and 10x the whole way
* Average 8.09x across all 30 n values

Notes:
Graphs 1 and 2 sweep n from 1 million to 30 million with 14 threads. Serial climbs to 2.6 seconds, threads stay under 0.4. Speedup sits between 7 and 10x, average 8.09x. The gap gets wider as n grows because the parallel version spreads the extra work over all the cores.

---

## Slide 5, Graphs 3 and 4. ERWYNA, 45 sec

Bullets to add on slide:
* n fixed at 30M, threads 1 to 28
* 2 threads 2.00x, 4 threads 3.93x, 8 threads 7.79x
* Almost one to one until 8 threads
* Flattens at 14 threads, the core count
* Not 14x because of Amdahl's Law and thread overhead

Notes:
Graphs 3 and 4 hold n at 30 million and change the thread count. Up to 8 threads it is nearly perfect: 2 threads gives 2x, 4 gives 3.93x, 8 gives 7.79x. After 14 it goes flat because that is every core we have. Extra threads just take turns.

Why not 14x? Two reasons. Amdahl's Law: the serial bits like allocating memory and creating threads cap the speedup. And overhead: creating threads costs time, and they never finish at exactly the same moment. Also 4 of our 14 cores are efficiency cores so 14x was never really on the table.

---

## Slide 6, Task 3 OpenMP pragma. TAABISH, 60 sec

Already has bullets (pragma, 40 lines, static/dynamic/guided, fopenmp warning). Keep.

Notes:
Task 3 does the same thing with OpenMP. All the thread creation, chunking and joining from task 2 becomes one line, parallel for with schedule dynamic 1000. About 40 lines replaced by one.

The schedule clause is where the task 2 thinking carries over. Static splits up front, dynamic hands out the next free chunk when a thread finishes, guided starts big and shrinks. Our work gets heavier as numbers get bigger, so dynamic fits best.

One gotcha: if you forget the fopenmp flag, the pragma is ignored, it runs on one thread, and speedup shows exactly 1.00 with no error. We got caught by that early.

---

## Slide 7, Graphs 5 and 6. TAABISH, 45 sec

Bullets to add on slide:
* Same n sweep, OpenMP with schedule(dynamic, 1000)
* Steady 9x to 10x at every n
* Average 9.37x, a bit ahead of pthreads
* Schedules at n = 30M: static 9.55x, dynamic 10.44x, guided 10.42x

Notes:
Graphs 5 and 6 are the same sweep for OpenMP. Very steady, 9 to 10x everywhere, average 9.37x, a bit ahead of our pthreads version.

We also timed all three schedules at 30 million. Static 9.55x, dynamic 10.44x, guided 10.42x. Dynamic beat static by about 9 percent, so the load imbalance argument is measured, not just a guess. That chart is in the appendix.

---

## Slide 8, Graphs 7 and 8. ERWYNA, 30 sec

Bullets to add on slide:
* Both parallel versions on the same axes
* OpenMP a bit faster at nearly every point
* 9.37x vs 8.09x average
* Why: dynamic adapts at run time, our rotation is fixed

Notes:
Graphs 7 and 8 put the two side by side. OpenMP is slightly faster almost everywhere, 9.37x against 8.09x. Two reasons: dynamic scheduling adjusts while it runs, our rotation is decided at the start. And OpenMP reuses its thread team instead of making new threads.

---

## Slide 9, Head to head summary. ERWYNA, 15 sec

Already has the big numbers. Keep.

Notes:
So in one line: 9.37x vs 8.09x, and one pragma vs about 40 lines. For this problem OpenMP wins on speed and on simplicity.

---

## Slide 10, Conclusion. ERWYNA, 45 sec

Already has 4 bullets and the recommendation. Keep.

Notes:
Four things we learned. Speedup is near linear while there are real cores behind it, then flat at the core count. How you split the work matters a lot when the cost per item is uneven, chunking took pthreads from 8.70 to 9.75x and dynamic gave OpenMP another 9 percent. The flag array gave us sorted output and no mutex at the same time. More threads than cores gives nothing.

Limitation and future work: trial division is not the fastest way to find primes. A segmented Sieve of Eratosthenes would be much faster and splits naturally by segment, but it is harder to write and uses more memory.

Recommendation: OpenMP for loop shaped work like this, pthreads when you need fine control over each thread.

Thanks, happy to take questions.

---

## Slide 11, Questions. BOTH

Keep the four numbers up during Q&A.

Notes:
Leave this up. The four numbers are your anchors. Answer short, use the proper terms (speedup, load imbalance, race condition, Amdahl's Law), stop when the question is answered.

---

## Slide 12, Appendix. Only if asked

Notes:
Not presented. Only if someone asks how we measured. Best of 3 runs, computation only, file writing excluded, all three outputs checked to match before timing.

---

## Slide 13, Thank you.

Notes:
Just say thanks.

---

Total talk time about 7 min 30. Erwyna about 4:15, Taabish about 3:15. Target is 6 to 8 minutes.
