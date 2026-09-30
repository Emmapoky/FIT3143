# HD Panel Round 1 reports (condensed by the Chair, 2026-09-30)

## Strict Marker: projected 58.6/100 (P)
| Criterion | Band | Mark |
|---|---|---|
| 1a (6) | D, C risk | 4.2 |
| 1b (7) | C | 4.2 |
| 1c (7) | C | 4.2 |
| Task 2 (20) | P, N risk | 10 |
| Presentation (20) | C cap | 12 |
| Q&A (40) | C | 24 |
Caps: presentation capped at C (script ~420 words = ~3 to 3.5 min vs "between 6 to 7 minutes"; no limitations/future work). Zero references: 1c capped C, Task 2 capped P. 1b cannot reach D (no hierarchy diagram, one code sample). Integrity: AI declaration incomplete; checklist names rotate_kernel.cu (real: rotate_cuda.cu), ticks results that don't exist; no names/IDs/emails; em dashes; "Furthermore" x2.
Top leaks: Q&A +4 to +8; Task 2 +4 to +6; Presentation +2 to +4; 1b +1.4; 1c +1.4; 1a +0.6.
Ceiling warning: band floors give ~80 at HD everywhere; 90+ has to come from Q&A precision.
HD asks per criterion: 1a full round-trip diagram (D1) incl D2H, zero-copy + UM one line each, measured H2D/D2H. 1b 3+ snippets from rotate_cuda.cu each tied to measured speed-up, hierarchy diagram, CPU vs GPU kernel-only AND end-to-end table with Amdahl/memory-bound explanation. 1c cited D3 separating CPU control path (cuFile) from DMA data path, prerequisites (O_DIRECT, FS/NVMe, alignment), verdict for our pipeline, nvJPEG acknowledged. Task 2 >=2 dated credible sources per topic, a figure per topic, an explicit comparison per topic, each framework's limitation, dual-use/security point. Presentation 6:30 to 6:50, limitations + future work slide, references slide, names/IDs/emails, parallel terms, no placeholders.

## Spec Lawyer
GenAI: ALLOWED WITH DECLARATION (items 9, 10, Task 2 p4). Draft declaration NON-COMPLIANT: omits Claude (used for rotate_cuda.cu, diagrams, charts, report, panel), paraphrased prompts not records, no Taabish records, no dates/versions/verification line, not a PDF.
Literal misses: Task 2 "security" (2b) absent; "dual-use risks" (p4 intro) absent; no named AI ethics guideline in 2d (UNESCO/OECD/EU AI Act); no citations ("cite all sources" p4); no diagrams used (D1 to D5, C1 to C4 unused); 1a missing D2H and host allocation; 1b expected speed-up unmeasured/uncited; separate Q&A section slide required (3c); appendix allowed after Q&A (put code, references, full results there); submit PDF not a link; names/IDs/emails on all files (item 11); ULO mentions NPU and exponential growth: one line + chart C3 covers it.
HD gates: 1b multiple sample codes + per-feature speed-up (not attempted); 1c references + GDS diagram; Task 2 extensive credible research per topic + comparisons + figures; presentation 6 to 7 min + limitations/future work; extensive parallel terminology everywhere; 1a/1b without omissions/errors; Q&A precise.
Timing: suggest 0:15 intro, 3:00 Task 1, 3:15 Task 2, 0:30 summary/limitations, finishing 6:30 to 6:50. Needs ~800 to 880 words of script.
Ambiguities (Ed questions): A1 both members upload same files? A3 prompt records = full transcripts? A4 is AI-written code OK if declared? Safest: both upload, full transcripts, declare everything, rewrite prose in own words, be able to explain every line.
Package: Colab results, QA drills, code_snippets empty; exclude task2/__pycache__.

## Pattern Hunter
C to D band as written. Hits: P1 severe (length, citations, security/dual-use, limitations, names, D2H); P2 severe (20 to 100x, 700 to 1200 W, millions of litres, 18 to 36 months, 64 GB/s all unmeasured/uncited; results not run); P3 (Task 2 noun bullets, no rebound effect, carbon-aware limits, NAIRR US-only, no GDS verdict for our pipeline); P4 (no Q&A prep, "unfiltered AI" risk); P5 (kernel-only speed-up, edge cases: clipped corners, 1 channel, nearest only, y-down flips CCW to CW; GDS control path); P7 (wrong filename, ticked undone items, draft header, __pycache__, >80 col lines, dashes, banned words "Furthermore", "massive" x4, "vast", "unlock", "ecosystem", "cutting-edge"); P8 (explain each kernel variant in one line); P9 severe (1b HD gate unattempted though code exists); P10 (draft kernel != submitted code; "four pillars" != SCALE framework).
Keep: draft skeleton (sections, slide timings, 3/4 split, inverse mapping rationale); Team_Roles lessons.

## Examiner
Draft is a step back from team files: rotate_cuda.cu v0 to v6 (1D :131, 2D :146, bilinear :158, pageable v4, streams :678, texture :185, block sweep + occupancy :603 to 653), D1 to D5, Task2_Report.md (limitations at line 104), C1 to C4.
Contradictions: C1 draft kernel rotates CW on screen (no y flip; team code flips y at :62 to 73). C2 draft kernel grayscale, int centre half-pixel off, __float2int_rn unchecked vs code floorf(+0.5) + byte compare. C3 "compute-heavy" vs "bandwidth-bound". C4 20 to 100x vs own D5 (streams best ~2x; PCIe Gen3 on T4 15.75 GB/s; H2D+D2H >= 2 x 6.3 ms vs kernel floor ~0.62 ms). C5 GDS "completely bypassing CPU" wrong; only the bounce buffer; "saturating PCIe" wrong. C6 four pillars vs SCALE. C7 chart captions cite stale reference numbers (C1 should be [5][6][8]; C2 IEA is [4] not [2]; C3 Epoch [38], Trends [39], EU AI Act [53], TOP500 [5]; C4 UNESCO [47], Slurm [60][61]): regenerate charts after numbering final. C8 AI declaration. C9 timing slots inconsistent.
Beyond-rubric moves: (1) bandwidth efficiency % of T4 320 GB/s from kernel_GBps (:485); (2) kernel-only vs end-to-end speed-up side by side with PCIe share (Amdahl; Topic 8 slide 46 bus bottleneck); (3) GDS back-of-envelope: 8K frame read ~14 ms at ~7 GB/s vs ~1 ms kernel, batch pipeline I/O-bound, plus honest "couldn't measure on Colab" limit.
Q&A drill Q1 to Q13 with HD skeletons (pinned vs pageable; index maths + 2D grid; inverse mapping; speed-up + limit; O(1) depth; GDS bypass; GDS worth it; streams ~2x; scaling vs parallel efficiency + Llama 3 MFU 38 to 43% [22]; Frontier vs LUMI GFLOPS/W 55.0 vs 53.4 [8]; rebound effect + IEA 415 TWh 2024 to ~945 TWh 2030 [1]; weakest part + future Slurm ConsumedEnergy; host vs device).
Priority: run Colab; rebuild deck from real artefacts; add results, limitations/future work, references slides; re-time 6:30 to 6:50; regenerate charts; complete AI declaration; drill Q4, Q6, Q12.
