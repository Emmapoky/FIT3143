# Declaration of Generative AI Use

**Unit:** FIT3143 Parallel Computing, Semester 2 2026
**Assessment:** Lab 2, Message Passing Interface (Week 8)
**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu) and Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)
**Date:** 15 September 2026

We used generative AI while preparing this lab, which item 9 of the assessment specification allows. We will not use any AI tool during the presentation or the Q&A, as item 10 requires. Every prompt record is uploaded as a PDF, listed at the end of this declaration.

## Tools used

| Tool | Used by | Used for |
|---|---|---|
| Gemini (Google) | Taabish | Task 1 and Task 2, the Open MPI and hybrid programs |
| Claude (Anthropic) | Erwyna | Tasks 1 to 4, on 8, 9 and 15 September 2026, as listed below |

## What Claude was used for

**Task 1 and Task 2 (`task1.c` and `task2.c`, written by Taabish)**

- Reviewing Taabish's programs. This found one real bug: `task2.c` called `memcpy` without including `<string.h>`, so it did not compile with Apple clang. The include was added.
- Renaming the files to `task1.c` and `task2.c` to match the submission checklist, and rewriting some of the code comments to make them clearer.
- Adding the per rank search times to `task1.c` and the per thread search times to `task2.c`, and adding checks on the value of n and on every memory allocation. The search, the partitioning and the MPI and OpenMP calls that do the work were not changed.

**Task 3 (performance evaluation, written by Erwyna)**

- Helping design the timing experiment: separate timed copies of the programs, reporting the slowest rank's time for each phase, and the two `MPI_Barrier` calls.
- Drafting the scripts in `supporting/scripts/` and the CAAS job files, and working out why our first CAAS jobs failed to build, until job 39361 ran.
- Adding a second timing sweep that grows n (`run_phases_by_n.py`, Graph 10), so the theoretical speedup is also worked out for an increasing problem size.
- Checking the Amdahl's Law working, and drafting and editing `Task3_Performance_Evaluation.pdf` and `CAAS_Analysis.pdf`.

**Task 4 (slides)**

- Drafting slide text and a speaking script, drawing the three explanatory diagrams with `make_diagrams.py`, and checking the deck against the specification and the marking rubric.

**Q&A preparation**

- Writing practice questions to rehearse with before the lab.

Every number in our slides and documents comes from running our own code, on our own laptop and on CAAS, and the scripts in `supporting/scripts/` reproduce them.

## Prompt records

- `AI_Prompt_Records_Claude.pdf`: every prompt typed into Claude for this lab.
- `AI_Prompt_Records_Gemini.pdf`: Taabish's Gemini chats for this lab.

## Signatures

| Name | Student ID | Email |
|---|---|---|
| Erwyna Soo Wen Xin | 36555789 | esoo0013@student.monash.edu |
| Taabish Farooq Bhat | 35473932 | ttaa0006@student.monash.edu |

We declare that this is a complete and accurate account of our use of generative AI in this assessment, and that we understand and can explain all of the submitted work.
