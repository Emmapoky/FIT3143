# AI use log, Task 1

Team: Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu) and
Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)

For the AI declaration. An AI coding assistant (Claude Code) generated
first drafts of the files below from our prompts. We reviewed, ran and
edited them. Prompt records go in the separate declaration PDF.

| File | What the assistant generated | How it was checked |
|---|---|---|
| rotate_cuda.cu | CUDA program, variants v0 to v6, timing, checks, CSV | clang CUDA syntax check (host + sm_75), kernels emulated on CPU; still to run on Colab T4 |
| rotate_cpu.c | CPU reference and self-tests | compiled and run locally, all tests pass |
| Applied2_Task1_Colab.ipynb, tools/build_notebook.py | notebook and its builder | analysis cells dry-run on dummy data; Numba cell run in the Numba CUDA simulator; full run on Colab still to do |
| diagrams/make_diagrams.py and D1 to D5 PNGs | diagram script | visually checked |
| Task1_Answers.md, .html, .pdf, tools/render_pdf.py | draft answers and renderer | references checked against the sources (web) |
| code_snippets/*.txt | slide snippets | match rotate_cuda.cu (snippet 1 is simplified) |
| Task1_QA_Drill.md | 12 practice questions and model answers | to rehearse, fill numbers from our Colab run |

The assistant also looked up and checked the reference URLs, DOIs and
hardware figures (PCIe, DDR5, T4, H100, GDS claims).
