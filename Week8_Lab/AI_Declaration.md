# Declaration of Generative AI Use

**Unit:** FIT3143 Parallel Computing, Semester 2 2026
**Assessment:** Lab 2, Message Passing Interface (Week 8)
**Team:** Erwyna Soo Wen Xin (36555789) and Taabish Farooq Bhat (35473932)
**Date:** 8 September 2026 [last touched]

## Declaration

We used generative AI during the preparation period for this lab, as allowed under
item 9 of the assessment specification. We did not use any AI tool during the
presentation or the Q&A, as required by item 10.

**Tool used:** Claude (Anthropic), during the week of 1 to 8 September 2026.

What it was used for, by task:

- **Task 1 and Task 2 (Open MPI and hybrid code).** Taabish drafted both programs.
  AI was used to review the drafts, and it identified one real defect: `task_2.c`
  called `memcpy` without including `<string.h>`, which made the file fail to
  compile under Apple clang. The one line include was added; nothing else in the
  search, the partitioning or the collectives was changed by AI.

- **Task 3 (performance evaluation).** AI was used to help design the measurement
  experiment, in particular the decision to instrument separate copies of the two
  programs (`task_1_instr.c`, `task_2_instr.c`, `serial_instr.c`) rather than time
  the submitted code, and the decision to take the maximum phase time across ranks
  rather than rank 0's own. It was also used to draft `run_benchmarks.sh` and
  `make_graphs.py`, and to check the Amdahl algebra. The measurement design,
  the choice of baseline, and every number in the results are our own; the numbers
  were produced by running the code on our own machine and can be reproduced by
  running `./run_benchmarks.sh`.

- **Task 4 (slides).** AI was used to draft the slide text and to check the deck
  against the Lab 2 marking rubric for coverage of all seven required graphs. All
  graphs were generated from our own measured CSV data.

Content in the slides and in `Task3_Performance_Evaluation.md` that is AI drafted
synthesis rather than a direct report of our own measurements is written as such
where it appears.

## Prompt records

The full prompt and response record is attached separately as
`AI_Prompt_Records.pdf`, as required by item 9.

## Signatures

| Name                | Student ID |
|---------------------|------------|
| Erwyna Soo Wen Xin  | 36555789   |
| Taabish Farooq Bhat | 35473932   |

We declare that the above is a complete and accurate account of generative AI use in
this assessment, and that we understand and can explain all of the submitted work.
