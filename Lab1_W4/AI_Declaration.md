# Declaration of Generative AI Use

**Unit:** FIT3143 Parallel Computing, Semester 2 2026
**Assessment:** Lab #1, Threads & OpenMP
**Team:** Erwyna Soo Wen Xin (36555789) and Taabish Farooq Bhat (35473932)
**Date:** 13 Aug 2026

---

## 1. Declaration

Generative AI [Gemini Flash] was used during the **preparation period** for this assessment, as permitted by
item 9 of the Lab #1 Assessment Specification:

> "You are allowed to use Generative-AI to search for information and resources during the
> preparation period. However, you must declare in your report and upload all the prompt
> records (in PDF files)."

No generative AI was used during the presentation, the Q&A, or any oral or coding interview
session, in line with item 10 of the specification.

**Tool used:** ______________________________________________

**Dates of use:** ______________________________________________

> Fill in the tool name and version you actually used, and attach the matching prompt records.
> These two need to agree with each other, since the prompt records are submitted alongside
> this form.

---

## 2. What it was used for

| Part | How AI was involved |
|---|---|
| `task1.c` (Erwyna) | Helped draft the serial version and the prime test. The square root bound and the odd divisor step are from the hint section of the specification. |
| `task2.c` (Taabish) | Helped draft the thread creation and joining, following the vector cell product example from the Week 3 lab prep. The first draft used one block per thread. Changing to chunks came from our own timing, after the block version only reached 1.58x. |
| `task3.c` (Taabish) | Helped draft the pragma and the schedule clause. Which schedule to keep was decided from our own timings, which are in `results_extra.csv`. |
| `run_benchmarks.sh` (Erwyna) | Helped draft the benchmarking script, the sweeps and the correctness check. |
| `make_graphs.py` (Erwyna) | Helped draft the plotting script for the eight required graphs plus our comparison graph. |
| Slides (Erwyna) | Helped draft the structure and wording. All figures shown are our own measurements. |

---

## 3. What it was **not** used for

- **No result was generated or estimated by AI.** Every time, speedup and graph in this
  submission comes from running our own code on our own machine.
- The correctness check, 664,579 primes below ten million with identical output from all three
  programs, was confirmed by running the programs, not by asking.
- No AI was used during the presentation or the Q&A.

---

## 4. What we did to make sure we understand it

1. Read through all three programs line by line and can explain any part without notes.
2. Compiled all three ourselves and confirmed there are no warnings under `-Wall -Wextra`.
3. Checked correctness with `diff` between the three output files and against the known count
   of 664,579.
4. Ran the full benchmark ourselves and regenerated every graph from our own numbers.
5. Practised the presentation and the Q&A answers unaided.

The change from block partitioning to chunks in `task2.c` is a good example of where the
measurement led rather than the tool. The first version was correct and looked fine, it was
just slower than we expected, and finding out why meant timing both and comparing.

---

## 5. Prompt records

The full prompt and response records are attached separately as required by item 9.

**Attachment:** `AI_Prompt_Records.pdf`

---

## 6. Signatures

| Name | Student ID | Signature | Date |
|---|---|---|---|
| Erwyna Soo Wen Xin | 36555789 | | |
| Taabish Farooq Bhat | 35473932 | | |

We declare that the above is a complete and accurate account of generative AI use in this
assessment, and that we understand and can explain all of the submitted work.
