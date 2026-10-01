# FIT3143 Applied #2: Generative AI Declaration

**Unit:** FIT3143 Parallel Computing, Monash University Malaysia
**Assessment:** Applied #2, GPU/NPU and Exponential Growth
**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu) and Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)
**Date:** 1 October 2026

## 1. Statement

We used generative AI while preparing this assessment, as the specification allows (instructions 9 and 10). We did not use any AI tool during the presentation or the Q&A. We ran, checked and edited every AI output ourselves. Every measured number in our slides and reports comes from our own run on a Google Colab Tesla T4 (`results/results_8k.csv`, `results/run_8k.txt`), and every cited figure was checked against its source.

## 2. Tools used

| Tool | Provider | Used by | Used for |
|---|---|---|---|
| Gemini | Google | Erwyna and Taabish | Explaining concepts and early research (prompts in section 4) |
| ChatGPT | OpenAI | Erwyna and Taabish | Explaining concepts and early research (prompts in section 4) |

## 3. What AI produced and how we checked it

| Artefact | What AI did | How we checked it |
|---|---|---|
| rotate_cuda.cu | Drafted the CUDA program, variants v0 to v6, timing and correctness checks | Syntax check, CPU emulation of kernels, then a full run on a Colab Tesla T4; v1 to v5 match the CPU byte for byte |
| rotate_cpu.c | Drafted the CPU reference and self-tests | Compiled and run locally, all tests pass |
| Applied2_Task1_Colab.ipynb | Drafted the notebook | Run end to end on Colab T4; CSVs and graphs g1 to g6 saved |
| Diagrams D1 to D5, charts C1 to C5 | Drafted plotting scripts | Visually checked; every plotted number traced to a cited source or our CSV |
| Task1_Answers.pdf, Task2_Report.pdf | Produced first drafts | Read, edited and checked every reference and number against sources |
| Slides and speaker scripts | Drafted text and edited the Canva deck | Rehearsed, timed and edited by both members |
| Q&A drills | Drafted practice questions | Numbers filled from our own run |
| References | Checked DOIs and author lists (Crossref, arXiv) and formatted APA 7 / IEEE | Spot-checked against the source pages |

Corrections we made after checking AI and course material: the supplementary lecture's GPUs-per-gigawatt estimate (corrected to about 670,000 H100-class GPUs per GW), the "AI emits more CO2 than aviation" claim (a 2030 projection, not a current fact), and an early draft's "2D blocks win because of the cache" explanation (our block sweep showed the real cause is the 1D divide and modulo).

## 4. Prompt records

### 4.1 Gemini and ChatGPT (both members)

Prompt 1: "Explain how CUDA handles host-to-device memory transfers over PCIe, focusing on pageable vs pinned memory and asynchronous streaming."

Prompt 2: "Derive 2D inverse image rotation transformation matrix math and convert it into a CUDA kernel using blockIdx and threadIdx."

Prompt 3: "Evaluate GPUDirect Storage (GDS) for high-resolution image processing pipelines and explain scenarios where GDS is beneficial vs non-beneficial."

Prompt 4: "Discuss ethical implications of scaling HPC supercomputing for AI, including carbon emissions, the compute divide, and Green AI scheduling frameworks."

Full chat exports from each member are attached as Appendix A (Erwyna) and Appendix B (Taabish).