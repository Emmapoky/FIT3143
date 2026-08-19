# Declaration of Generative AI Use

**Unit:** FIT3143 Parallel Computing, Semester 2 2026
**Assessment:** Lab 1, Threads and OpenMP
**Team:** Erwyna Soo Wen Xin (36555789) and Taabish Farooq Bhat (35473932)
**Date:** 19 August 2026 [last touched]

## Declaration

We used generative AI during the preparation period for this lab, as allowed under item 9 of the assessment specification. We used two tools:

* **Google Gemini Flash**, on 11 August, to help draft the first versions of the three programs, on 15 and 17 August, to help fix our benchmarking script and tweak our graphs to show correct result.

<<<<<<< HEAD
No AI was used during the presentation, the Q and A, or any oral or coding interview session, in line with item 10.

## What we used each tool for

**Gemini [Flash]**
 
- First drafts of the thread creation and joining in Task 2, and of the parallel for pragma in Task 3. The square root bound in Task 1 came from the hint section of the specification.

- Helped to guide us through our first full benchmark run produced graphs that looked finished but were wrong. The script was not collecting the OpenMP timings at all, and the plotting code was quietly turning the blank cells into zeros, so we got eight graphs with a flat line along the bottom and no error to warn us. 

- We used Gemini to find and fix both problems, and to change the plotting script so that missing data now stops with an error instead of drawing something misleading. 

## What we did ourselves

* **Every timing, speedup and graph in this submission comes from running our own code on our own laptop.** No result was generated or estimated by AI.
* The change in Task 2 from one block per thread to chunks in rotation came from our own timings, after the block version only reached 8.70x. The measurement led, not the tool.
* Which OpenMP schedule to keep was decided from our own results in `results_extra.csv`.
* The correctness check, 664,579 primes below ten million with identical output from all three programs, was confirmed by running the programs and diffing the output files.
* We have both read through all three programs and can explain any part of them without notes.
=======
We used Gemini to assist with technical research, code drafting, data verification, and slide quality auditing. Specifically, the tool was used to:

- **Code & Script Drafting:** Help draft initial code structures, including POSIX thread creation and join loops (Task 2), OpenMP compiler pragmas (Task 3), benchmarking shell scripts, and Python plotting scripts (make_graphs.py).
- **Benchmark & Mathematical Verification:** Audit timing logs, speedup equations, parallel efficiency calculations, and core-scaling curves across 1 to 28 threads.
- **Rubric & Presentation Compliance:** Cross-check our slide deck (Lab1_W4_Taabish_Erwyna.pdf) against the FIT3143 Lab 1 Marking Rubric to verify complete coverage of Graphs 1–8, load-distribution schemes, and HD criteria.
- **Q&A Technical Refinement:** Rehearse parallel computing concepts—such as physical core saturation (14 M3 Max cores), thread oversubscription (28 threads), and lock-free memory flagging—for the presentation Q&A.
>>>>>>> 7e784df199ea6a323eb6c230b5067df9b63b4848

## Prompt records

The full prompt and response records for both tools are attached separately as `AI_Prompt_Records.pdf`, as required by item 9.

## Signatures

<<<<<<< HEAD
| Name               |Student ID| 
|--------------------|----------|
| Erwyna Soo Wen Xin | 36555789 | 
| Taabish Farooq Bhat| 35473932 | 

We declare that the above is a complete and accurate account of generative AI use in this assessment, and that we understand and can explain all of the submitted work.
=======
| Name                | Student ID |
| ------------------- | ---------- |
| Erwyna Soo Wen Xin  | 36555789   |
| Taabish Farooq Bhat | 35473932   |
>>>>>>> 7e784df199ea6a323eb6c230b5067df9b63b4848
