# Declaration of Generative AI Use

**Unit:** FIT3143 Parallel Computing, Semester 2 2026
**Assessment:** Lab 2, Message Passing Interface (Week 8)
**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu) and Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)
**Date:** 16 September 2026

We used generative AI while preparing this lab, which item 9 of the assessment specification allows. We did not use any AI tool during the presentation or the Q&A, as item 10 requires.

This is our one AI declaration file. It has three parts:

| Part | What it is |
|---|---|
| Part 1 | This declaration |
| Part 2 | The full Gemini Pro prompt record, exported from Gemini |
| Part 3 | The full Claude prompt record, exported from the Claude Code session logs |

All measurements in this submission were taken on a MacBook Pro 14 inch (November 2023), Apple M3 Max, 14 cores: 10 performance and 4 efficiency, and on the Monash CAAS cluster.

## Tools used

| Tool | Used by | Prompt record |
|---|---|---|
| Gemini Pro (Google) | Taabish Farooq Bhat and Erwyna Soo Wen Xin, together | Part 2 of this file |
| Claude (Anthropic) | Erwyna Soo Wen Xin | Part 3 of this file |

## Gemini Pro

One session, "Hybrid MPI and OpenMP Programming", which Taabish and Erwyna worked through together. The transcript was exported on 16 September 2026. Six prompts, in order:

1. Structuring the hybrid program: `MPI_Init_thread` with `MPI_THREAD_FUNNELED`, an MPI stride across processes, and `#pragma omp parallel for schedule(dynamic, 1000)` inside each process to avoid thread level load imbalance and false sharing.
2. Reviewing our cyclic partitioning, where rank r takes 3 + 2r and strides by 2p, for residue class lock in and the load imbalance when an odd prime d divides p, with p_eff = p (1 - 1/d). Gemini recommended block cyclic chunking with a chunk size of 32,768 odd candidates.
3. Designing the timing framework: `MPI_Wtime` with explicit `MPI_Barrier` calls, so that time a rank spends waiting is not counted as communication, separating the search, the gather (kappa) and the root's serial sort and file write (r_s).
4. Benchmark configurations comparing p x t hybrid runs against pure MPI and pure OpenMP at matched total worker counts, for example 2 x 7 against 14 processes and against 14 threads.
5. Drafting a 6 to 7 minute presentation script covering methodology, the phase breakdown, the speedup plateau, limitations and multi node CAAS scaling.
6. A practice viva: four questions on load imbalance, residue congruence, shared memory against message passing overheads, and deriving the Amdahl's Law parameters, marked against the HD rubric.

The hybrid structure in `task2.c` follows the first prompt, and the timing method in the instrumented programs follows the third. **The block cyclic suggestion in the second prompt was not adopted.** The submitted `task1.c` and `task2.c` keep the single value stride, and section 11 of `Task3_Performance_Evaluation.pdf` lists that change as future work, so that every measurement we report matches the code we submit.

## Claude (Anthropic)

Used by Erwyna on 8, 9, 15 and 16 September 2026.

**Task 1 and Task 2 (`task1.c` and `task2.c`, written by Taabish)**

- Reviewing the programs. This found one real bug: `task2.c` called `memcpy` without including `<string.h>`, so it did not compile with Apple clang. The include was added.
- Renaming the files to `task1.c` and `task2.c` to match the submission checklist, and rewriting some of the code comments to make them clearer.
- Adding the per rank search times to `task1.c` and the per thread search times to `task2.c`, and adding checks on the value of n, on the MPI thread support level, and on every memory allocation. The search, the partitioning and the MPI and OpenMP calls that do the work were not changed.
- On 16 September, writing a separate test program, `supporting/experiments/partition_variants.c`, that times the cyclic stride in `task1.c` against a block split and against chunks of 1000 odd numbers, with the script and graph behind appendix slide A6. The submitted `task1.c` was not changed.
- On 16 September, after the teaching team asked for CAAS job files and the sorted prime output, recovering the exact job file and printed output of CAAS job 39361 from our git history and terminal records, and producing the compressed prime files and checksums in `supporting/primes_output/` by running the submitted programs.

**Task 3 (performance evaluation, written by Erwyna)**

- Building the measurement scripts in `supporting/scripts/` and the CAAS job files, and working out why our first CAAS jobs failed to build, until job 39361 ran.
- The second sweep that measures the theoretical speedup as n grows (`run_phases_by_n.py`, Graph 10).
- Checking the Amdahl's Law working, and drafting and editing `Task3_Performance_Evaluation.pdf` and `CAAS_Analysis.pdf`.

**Task 4 (slides)**

- Drafting slide text, drawing the three explanatory diagrams with `make_diagrams.py`, and checking the deck against the specification and the marking rubric.
- On 16 September, a last check of the finished deck and the submission files against the specification, the rubric and our CSV data. This corrected one percentage on appendix slide A5 and in section 7 of the Task 3 document, and put this declaration and both prompt records into one file.

**Q&A preparation**

- Practice questions to rehearse with before the lab.

Every number in our slides and documents comes from running our own code, on our own laptop and on CAAS, and the scripts in `supporting/scripts/` reproduce them.

## Signatures

| Name | Student ID | Email |
|---|---|---|
| Erwyna Soo Wen Xin | 36555789 | esoo0013@student.monash.edu |
| Taabish Farooq Bhat | 35473932 | ttaa0006@student.monash.edu |

We declare that this is a complete and accurate account of our use of generative AI in this assessment, and that we understand and can explain all of the submitted work.
