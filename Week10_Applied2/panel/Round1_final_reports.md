# HD Panel, final check, Round 1 (1 Oct 2026), condensed by the Chair

## Strict Marker: projected 73/100 (D)
1a HD 4.8 | 1b D 4.9 (A4 says all outputs mismatch 0 but v6 = 257,964; 1.55 vs 1.45 ms unexplained; no theoretical bound on main slides) | 1c HD 5.6 | Task 2 HD floor 16 (news sources for 31%, water; slides 10/11 dense) | Presentation D 14 (scripts 894 words = 6:53 before handovers, risk >7:00 -> C) | Q&A D 28 (drill placeholders unfilled).
Gate: no AI_Declaration.pdf + prompt PDFs. Leaks: Q&A +4..+8; timing/density +2 (cut ~60 words, slide 6 + 14); 1b +0.7 (fix A4, label runs, add Amdahl bound 509.3/(8.06+7.58)=32.6x, measured 29.6x = 91% of bound; vs bandwidth-saturating CPU ~4x); Task 2 sources +0..1; IEEE vs APA mix. Realistic ceiling 82-86.

## Spec Lawyer
GenAI allowed WITH declaration + all prompt records as PDF (instr 9), none in talk/Q&A (instr 10). Compliance met for 1a/1b/1c/T2/structure/limitations. Partly: notebook has 0 executed outputs; speech vs slide mismatch (19%, 128 GB/s/40% not on slides); A4 mismatch claim false for v6; Task2_Report has no emails; Task2_QA_Drill no names. Missing: AI_Declaration.pdf, prompt-record PDFs, deck PDF export (link not marked).
Tool list contradiction: slide 26 says Claude, Gemini, ChatGPT; ai_logs list only Claude. Declare exactly what was used. task1/ai_log.md stale ("still to run on Colab"). Add one AI line inside each report PDF.
Upload: Slides PDF; Task1_Answers.pdf; Task2_Report.pdf; AI_Declaration.pdf (+ prompt PDFs per member); Task1_Code.zip (rotate_cuda.cu, rotate_cpu.c, EXECUTED notebook, results csv/txt/png, diagrams, code_snippets); optional Task2_Charts.zip. Exclude panel/, .DS_Store, scripts, drills, .md sources, ai_logs (fold into declaration), tools/make_*.py, ~285 MB .ppm files, Team_Roles.txt, run_m3.sbatch.

## Pattern Hunter
P2: "2D beats 1D because square tile suits cache" (script:17, Answers:64-65, rotate_cuda.cu:142-144, drill Q9) contradicted by block sweep (128x1 1.444 ms = 16x16 1.453 ms); real cause is v1 divide/modulo. "Tamil 10x tokens" should be "about 10 tokens per word". "19%" needs the Wiesner condition + citation (Wiesner missing from APA list). "1-2% fleet-wide" should be "at peak-carbon hours". Drill Q8 GPU maths (770k at 1.3 kW, not 650k), Q9 86 days not 100.
P7: Task1_QA_Drill placeholders [g3] [g2 %] [% of peak] [g4 best] [result] [max_diff]; Answers:116 stale "(graph g2 confirms or corrects this)" + banned word "massive"; stale speaker_notes.txt, Task2_Slide_Content.md.
Voice: no dashes in deliverables. Both members sound identical (same closers, same scaffolding "Why/So what/Alternative that loses"). Suggested per-member rewrites (5 each) given.
Numbers otherwise match CSV.

## Examiner
Depth: (1) cache claim contradicted (as above); bilinear is where shape matters (16x8 2.83 vs 64x4 4.00 ms). (2) run-to-run variance never stated (v2 kernel 1.55/1.45/2.11 ms; copies stable 8.06). (3) 6.6x estimate vs 29.6x: baseline Colab core 509 ms vs M3 113 ms; vs bandwidth-saturating CPU ~4x. (4) size sweep: CPU ns/px also rises. (5) streams bound ~2.3x ideal, achieved 80%; 5 vs 30 degree result unused. (6) SCALE L (FedAvg) undercut by own Zhu citation: add secure aggregation/DP. (7) SCALE S: name a threshold (e.g. efficiency < 70%).
Contradictions: v6 mismatch counted in BYTES (rotate_cuda.cu:316), 0.26% of output; "1 or 2 levels" vs measured 1. 19% vs 1-2% mixing. "Strong scaling in reverse" loose.
Beyond-rubric: 5 vs 30 degree insight; streams ideal bound; joules per image via nvidia-smi (links T1 to SCALE A).
Q&A drill: T1-T5, E1-E5, X1-X3 with skeletons.

## Polisher
APA: "(Stanford HAI, 2026)" -> "(Stanford Institute for Human-Centered AI [HAI], 2026)"; "(NCI, ...)" -> "(National Computational Infrastructure [NCI], ...)"; "European Parliament & Council" -> full author name; orphans NVIDIA 2018 and Ravi 2020 not cited on deck; The Sun / Lowyat as group authors questionable; header says "A9 to A10"; arXiv DOIs (10.48550/arXiv.2504.16026). Italics lost on slides.
Numbers: 12.3 vs CSV 12.35; A4 mismatch claim; "speed-up grows with size" not monotonic (4K 28.95x vs 8K 28.83x) -> "generally grows".
Code: notebook lines >80 cols (cells 9,13,15); missing one-line why-comments above some functions in rotate_cuda.cu / rotate_cpu.c.
Names: Task2_Report no emails. Placeholder: speaker_notes.txt. Junk list as Spec Lawyer.
