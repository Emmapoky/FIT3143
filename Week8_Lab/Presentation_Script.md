# FIT3143 Lab 2 - Presentation script

**Target: 6:41 at a steady 130 words a minute.** The rubric wants 6 to 7 minutes,
so that sits comfortably inside it with 19 seconds spare. At a brisker 140 it
lands at 6:14, which is still fine. At a slow 120 it runs to 7:14, which is over,
so if rehearsal comes out at 7 minutes or more, cut rather than talk faster. The
cuts to make first are listed at the bottom.

**Speakers.** Taabish takes Task 1 and Task 2 (slides 3 to 10), because he wrote
both programs and the Q&A will come back to him on them. Erwyna takes the open,
Task 3, and the close.

**Pace.** Written at 130 words per minute, which is a calm technical pace rather
than a rush. `[beat]` means stop talking for one second. Do not fill them. The
beats are what make this sound composed instead of recited, and they are already
counted in the timings.

**The deck is 22 pages, but you only present 17.** Pages 18 to 22 are the
appendix, and page 18 says so on its face. Do not click into them during the
7 minutes. They exist so the marker reading the deck afterwards can check the
phase breakdown, the full parameter table, how to reproduce the numbers, and the
AI declaration.

**Do not read the slides aloud.** The body text on each slide is for the marker
reading the deck afterwards. If you catch yourself reading it, you are
duplicating yourself and burning time you do not have.

---

## Slide 1 - Title | Erwyna | 0:00 to 0:14
Good afternoon. I'm Erwyna, this is Taabish. Our Lab 2 work on prime search with
Open MPI, measured on a 14 core M3 Max up to 130 million. `[beat]`

---

## Slide 2 - What we set out to answer | Erwyna | 0:14 to 0:30
Three questions. Can Open MPI beat our Week 4 threaded versions. Does adding
OpenMP threads inside each process help. And does Amdahl's Law predict what we
measured. `[beat]` Taabish takes the first two.

**Hand over.**

---

## Slide 3 - Partitioning scheme | Taabish | 0:30 to 1:01
Our partitioning is cyclic. Rank r starts at 3 plus 2r and steps by 2p, walking
the odd numbers in a stride.

That was deliberate over a block split. Testing a candidate costs about its
square root, so a block gives the last rank the expensive end and everyone waits.
`[beat]`

The stride also costs nothing. Every rank computes its own range. No
communication, no scheduler.

---

## Slide 4 - Collecting the results | Taabish | 1:01 to 1:26
Results come back in two stages. `MPI_Gather` of one count per rank, so the root
knows the sizes. Those become displacements, then `MPI_Gatherv` lands every block
at its own offset in one call. `[beat]`

The root sorts, because a cyclic split arrives interleaved, then writes. Output
is byte identical to the Week 4 serial.

---

## Slide 5 - Graph 1, run time | Taabish | 1:26 to 1:49
Run time against problem size. 31 values of n, 14 workers.

Serial reaches 21.2 seconds. Open MPI, 2.8. OpenMP, 2.6. `[beat]`

Open MPI sits just above OpenMP at every n, and the gap is a constant, not a
slope. It is 0.184 seconds of `mpirun` launch, paid once.

---

## Slide 6 - Graph 2, speedup vs n | Taabish | 1:49 to 2:14
The same runs as speedup. 2.5x at 10 million, rising to 7.8x at 126 million,
because the launch cost is fixed while the work grows. `[beat]`

One caveat we raise ourselves. Our Week 8 search uses a faster primality test
than the Week 4 serial, worth about 1.4x before any parallelism.

---

## Slide 7 - Graph 3, speedup vs width | Taabish | 2:14 to 2:41
Now n is fixed and we sweep width to 28, twice our core count.

All three plateau near 7x, not 14x. Ten performance cores plus four slower
efficiency cores, then oversubscription past 14. `[beat]`

But look at Open MPI. It has a saw tooth, and p equals 3 is slower than p equals
2. Hold that thought.

---

## Slide 8 - Hybrid design | Taabish | 2:41 to 3:08
Task 2 puts OpenMP inside each process. We initialise with
`MPI_THREAD_FUNNELED`, because only the main thread calls MPI.

The same stride picks each process's share, then `schedule(dynamic, 1000)` splits
it across threads. `[beat]`

Dynamic matters. A thread that draws a cheap chunk comes back for another, so
threads self balance in a way the fixed stride cannot.

---

## Slide 9 - Graph 4, hybrid vs pure MPI | Taabish | 3:08 to 3:30
Process count held at 4 for both lines, adding threads.

Pure Open MPI is flat at 4.8 seconds. Thread count means nothing to it. The
hybrid drops to 2.4. `[beat]` Returns flatten past 4 threads, as expected. 4 by 4
is already 16 workers on 14 cores.

---

## Slide 10 - Graph 5, matched width | Taabish | 3:30 to 3:56
The comparison the spec asks for specifically. Matched total width, so 3
processes of 2 threads is compared against 6 OpenMP threads, not 3.

Our best is 2 by 7, at 2.29 seconds, beating OpenMP at 14 threads and pure MPI at
14 processes. `[beat]` Few processes, many threads keeps winning. Erwyna will
explain why.

**Hand over.**

---

## Slide 11 - How we measured | Erwyna | 3:56 to 4:31
For Task 3 I had to split the run into the part that scales and the part that
doesn't. One stopwatch can't do that, so I instrumented three copies. Searches
untouched, timers added.

Phases are the maximum across ranks, because a collective finishes when the
slowest rank arrives. `[beat]`

And there are two barriers. My first run reported gather times of 7.6 seconds,
absurd for a memory copy. That was idle ranks waiting, billed as communication.

---

## Slide 12 - The model | Erwyna | 4:31 to 4:54
Separated properly, real communication is 5 milliseconds at one process, 36 at
28. `[beat]` Kappa is four thousandths of runtime. On one node, communication is
not what stops the speedup.

The serial fraction caps us at 34.7x. But plain Amdahl still overshoots, and the
error has structure.

---

## Slide 13 - One rank in d does no work | Erwyna | 4:54 to 5:35
Here is why. Rank r only ever tests 3 plus 2r plus 2pk. For any odd prime d
dividing p, that term vanishes modulo d, so every number a rank touches sits in
one residue class. `[beat]`

So one rank gets nothing but multiples of d, thrown out on the first iteration.

At p equals 3, rank 0 found two primes, in twelve milliseconds. Ranks 1 and 2
found 3.7 million each, in 7.6 seconds. `[beat]` At p equals 4, all four ranks
finished within 5 milliseconds.

---

## Slide 14 - Graph 6 | Erwyna | 5:35 to 5:53
Which is what this shows. Amdahl at p is smooth and overshoots. Amdahl at the
effective process count reproduces the saw tooth, dip for dip. `[beat]` That
match is the evidence imbalance is the dominant error term, not noise.

---

## Slide 15 - Graph 7 | Erwyna | 5:53 to 6:14
The hybrid partly escapes it, because only the MPI stride is congruence bound.
Inside a rank, dynamic scheduling hands out chunks on demand.

With the same 6 workers, 2 by 3 took 3.4 seconds and 3 by 2 took 4.7. With 3
processes, one of them has nothing to search.

---

## Slide 16 - What we found and would change | Erwyna | 6:14 to 6:38
Open MPI matched OpenMP but never beat it, and paid launch cost to do it. On one
shared memory node, threads are the right tool here.

On CAAS, across two nodes, Task 1 reached 10.31x at 8 processes and Amdahl was
within 2%. Even there, communication was about 0.1% of the run. `[beat]` What we
would change: hand out chunks instead of single strided values, so no rank sits idle.

---

## Slide 17 - Questions | Erwyna | 6:38 to 6:41
That is our work. Happy to take questions.

---

# Rehearsal notes

- **Time the two blocks separately.** Taabish runs 0:30 to 3:56, so 3 minutes 26.
  Erwyna runs 3:56 to 6:41, so 2 minutes 46. If either drifts more than 15
  seconds, cut a sentence rather than speeding up. Rushing costs presentation
  marks. Finishing 20 seconds early does not.
- **Practise the two handovers**, at slides 2 to 3 and 10 to 11. A fumbled
  handover reads as a team that prepared separately.
- **Slide 13 is the slide that earns the marks.** Do not rush it. The two numbers
  to land clearly are "two primes" and "3.7 million".
- **Know your appendix.** If a Q&A question goes to the parameter table or the
  phase split, jump to A1 or A2 rather than describing it from memory. That reads
  as prepared, not as padding. A5 is the new one: theoretical against measured
  speedup as n grows. Go there if anyone asks what happens to the speedup when the
  problem gets bigger. The line to say is that r_s falls from 0.096 at 10 million
  to 0.027 at 130 million, so the ceiling rises with n, and our measurement keeps
  the same 60 to 67 percent of theory the whole way, which makes the gap a hardware
  gap and not a size effect.
- **If you are running long**, cut in this order. First the caveat paragraph on
  slide 6, which is already covered on slide 12. Then the last sentence of slide
  8. Then the second paragraph of slide 16. That is about 45 seconds and none of
  it is load bearing.

# Likely Q&A, and who takes it

| Question | Who | One line answer |
|---|---|---|
| Why cyclic and not block? | Taabish | Cost grows like sqrt(k), so a block gives the last rank the expensive end and everyone waits. |
| Why `MPI_Gatherv` rather than `MPI_Gather`? | Taabish | Ranks find different counts, so the blocks are unequal. Gatherv takes a displacement per rank. |
| Why `MPI_THREAD_FUNNELED`? | Taabish | Only the main thread calls MPI. A stronger level costs locking we do not need. |
| Would you recommend MPI here over OpenMP? | Either | Not on one node. Same speed, extra launch cost, harder code. MPI earns its keep across machines. |
| Why is empirical below theoretical? | Erwyna | Three measured reasons: an idle rank when p has an odd factor (p_eff), qsort costs more once the lists arrive interleaved, and 4 slower efficiency cores. On CAAS, Amdahl was within 2%. |
| Why baseline at p = 1 and not the Week 4 serial? | Erwyna | Different primality test, worth 1.4x. Using Week 4 would count an algorithmic win as a parallel win. |
| What did CAAS show? | Erwyna | 10.31x at 8 processes across two nodes, 86% efficiency, Amdahl within 2%. The gather got 4.6x slower but was still about 0.1% of the run. |
| Why does speedup stop at 7x? | Either | 10 performance plus 4 efficiency cores, then oversubscription past 14. |
| How do you know the output is correct? | Taabish | Byte identical to the Week 4 serial reference under diff, at 30 million. |
