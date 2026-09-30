# HD Panel Round 2: The Improver's plan (FIT3143 Applied #2)

Plan only. No team file was edited. Date 2026-09-30. Talk likely Thu 8 Oct 2026.

## 0. The one decision that matters

**Throw away Draft v1 as a source. Build the deck from the team's own artefacts.**
Draft v1 (Gemini/ChatGPT) is weaker than, and in places contradicts, what is already in
`task1/` and `task2/`. The reviewers found most of its errors (CW turn, grayscale kernel,
"completely bypassing the CPU", "20x to 100x", "four pillars" vs SCALE, uncited 700 to 1200 W,
64 GB/s, millions of litres). None of that survives if we simply stop using it.

Artefacts the deck is built from (all exist, checked today):
- `task1/Task1_Answers.md` (3,086 words, answers 1a/1b/1c, 24 IEEE refs incl. GDS guides,
  Thompson and Newburn 2019, Ravi et al. 2020, limitations + future work). **No reviewer
  mentioned this file. It already solves most Task 1 findings.**
- `task1/diagrams/D1 to D5`, `task1/code_snippets/1 to 4` (not empty: 4 snippets, 9 to 11 lines
  each), `task1/rotate_cuda.cu` (v0 to v6), `task1/Applied2_Task1_Colab.ipynb` (writes
  g1_speedup, g2_stage_breakdown, g3_pinned_vs_pageable, g4_block_sweep, g5_size_sweep,
  g6_streams and prints the slide numbers in section 10).
- `task2/Task2_Slide_Content.md` (6 slides, 547 words, cited), `task2/Task2_Report.md`,
  `task2/references.md` (72 IEEE refs), `task2/charts/C1 to C4` (regenerated 14:16, after
  references.md at 14:15, and captions already use final numbers).

---

## 1. REVISION PLAN (ranked by marks per minute)

Current projection (Strict Marker): 58.6. Weights: 1a 6, 1b 7, 1c 7, Task 2 20,
Presentation 20, Q&A 40.

| # | Criterion | Fix | +marks est. | Effort | From |
|---|---|---|---|---|---|
| 1 | Presentation (cap) | Rebuild deck to the slide list in §3. Script ~880 words, 6:30 to 6:50, includes a Limitations and future work slide and a separate Q&A slide | +5 (12 to 17) | 2 h build + 2 timed run-throughs | SM, SL, PH |
| 2 | Task 2 | Use Task2_Slide_Content (trimmed to §4 scripts), C1 to C4 on slides, a cite on every bullet, say "dual-use" and "security" out loud | +7 (10 to 17) | 1 h | SM, SL, PH, EX |
| 3 | 1b (HD gate) + Q&A | **YOU MUST DO:** Taabish runs the Colab notebook on a T4, saves `results/`, screenshots section 8 tables and section 10 printout | unlocks +1.8 on 1b and ~+2 on Q&A | 30 min (Taabish) | all four |
| 4 | 1b | Two 1b slides: model (D2 + snippets 1, 2) and features vs speed-up (variant table + g1 + g2 with measured numbers) | +1.8 (4.2 to 6.0) | 40 min after #3 | SM, SL, PH, EX |
| 5 | Q&A | Write and drill a 12-question sheet (§6), verdict then mechanism then our evidence, both people, all parts | +8 to +10 (24 to 32/36) | 3 h across both, spread over the week | EX, PH, SM |
| 6 | 1c | GDS slide from D3 + verdict for OUR pipeline + cites [11] [13] [15] | +1.8 (4.2 to 6.0) | 20 min | SM, SL, EX |
| 7 | 1a | D1 slide covering the full round trip (cudaMalloc, H2D, pageable vs pinned, kernel in GDDR, D2H) + one line each on UM and zero-copy (on slide, not spoken) | +0.9 (4.2 to 5.1) | 20 min | SM, SL |
| 8 | Integrity gate | AI declaration PDF: both members, ALL tools (Claude, Gemini, ChatGPT), full prompt records exported as PDF, dates, one "what we checked ourselves" line | protects the whole 10 marks | 45 min | SL, SM |
| 9 | Hygiene | Names, IDs, Monash emails on every file; correct file names (rotate_cuda.cu, not rotate_kernel.cu); fill the "fill from Colab" table in Task1_Answers.md; zip without `__pycache__`, `.DS_Store`, `panel/`, Draft_v1; both members upload the same set | protects 1 to 2 | 20 min | SM, SL, PH |
| 10 | 1b / Q&A | One line from section 10: kernel GB/s as % of T4 peak (memory bound, shown not claimed) | +0.3 plus a strong Q&A answer | 2 min after #3 | EX |
| 11 | 1c / Task 2 | Appendix reference slides (cited items only), Task 1 list and Task 2 list with clear headers | protects 1c and Task 2 HD "properly cited" | 30 min | SM, SL |
| 12 | Task 2 figures | Optional simple Canva diagram for slide 9 (two countries, all-reduce arrows over a border) so every Task 2 topic has a visual | +0.3 to +0.5 | 15 min | SM |

---

## 2. PUSHBACK (rejected or reduced reviewer demands)

1. **Spec Lawyer: "code_snippets empty".** Wrong. `task1/code_snippets/` holds 4 files (index
   maths, launch config, pinned + streams, event timing). Only the QA drill files are missing.
2. **Examiner C7: regenerate charts for stale caption numbers.** Already done. `make_charts.py`
   captions use [5] [6] [8], [1] [4], [38] [39] [53] [5], [47] [60] [61], and the PNGs were
   rebuilt after references.md. Just eyeball each PNG once (2 min). No rebuild.
3. **Strict Marker: "measured H2D/D2H on the 1a slide".** The 1a rubric asks for correct,
   complete explanation and a clear diagram, not measurements. Put the measured copy rate in
   ONE spoken number on slide 3 (it is free once Colab runs) and keep the rest for 1b.
4. **Examiner beyond-rubric move 3: "8K frame read ~14 ms at ~7 GB/s NVMe".** Reject the 7 GB/s.
   It is not in either reference list, so it would be an uncited number in a criterion whose
   HD line says "properly referenced". Use our own measured copy share instead: if PCIe copies
   already dwarf the kernel, the I/O argument for GDS stands without a guessed NVMe speed.
5. **Spec Lawyer: "NPU and exponential growth, one line + C3".** C3 already shows exponential
   growth on slide 10. NPU is a ULO, not a Task 1 or Task 2 requirement, and no rubric line
   rewards it. Keep the SIMD vs SIMT vs NPU paragraph in Task1_Answers.md and an appendix
   slide for Q&A. Spend no talk seconds.
6. **Strict Marker: ">= 2 dated sources AND a figure per Task 2 topic".** Sources yes (the
   report has them). A figure per topic is nice, not a gate; 2b gets an optional Canva sketch
   (#12). 2d already has C4. Do not build new charts.
7. **Strict Marker: "names/IDs on all slides".** Title slide plus every submitted file is
   enough (spec item 11 says files). A footer on every slide costs nothing in Canva, so fine,
   but it is not worth a debate.
8. **Separate limitations slides per task.** One combined slide, spoken by Erwyna, is enough
   for "sections summarise... limitations and future work" and saves a handover. It also shows
   either of us can speak to Task 1.
9. **Pattern Hunter's draft-kernel edge cases (y flip, half-pixel, grayscale).** Not fixes to
   make; they vanish when the draft kernel is dropped. They stay in the Q&A sheet because the
   team code handles them (y flip at rotate_cuda.cu :62 to 73, floorf(+0.5)).
10. **Reference numbering clash.** Task 1 uses [1] to [24], Task 2 uses [1] to [72]. Do not
    renumber two documents a week out. Put "Refs: Task 1 list" or "Refs: Task 2 list" in each
    slide footer and give the appendix two clearly headed reference slides.

---

## 3. FINAL SLIDE LIST (Canva). Main talk 6:40 target, window 6:30 to 6:50

Speed assumption: 135 to 140 words per minute plus pointing. Core script = ~880 words.
Lines in {braces} in §4 are "drop if over time" (about 58 words, ~25 s of buffer).
`[IMAGE: ...]` = placeholder; Erwyna places the image herself. `[Y]` values = YOU MUST DO
from the Colab run (Taabish), quoted exactly from the CSV or section 10 printout.

| # | Title on slide | What is on it | Owner | Time | Spoken words | Slide words (max) |
|---|---|---|---|---|---|---|
| 1 | GPU Image Rotation and the Ethics of Scaling HPC for AI | Unit, Applied #2, both names, IDs, Monash emails, date; 3-item agenda strip: Task 1 GPU design, Task 2 ethics, Limitations + Q&A | Erwyna | 0:15 | 38 | 40 |
| 2 | Task 1: 33 million independent pixels | [IMAGE: task1/diagrams/D4_inverse_mapping.png]; one line: "Inverse mapping: one thread per output pixel, one writer, no holes" | Taabish | 0:20 | 49 | 20 |
| 3 | 1a. Host to device and back | [IMAGE: D1_data_path.png] large; 3 bullets: pageable = extra staging copy; pinned (cudaMallocHost) = direct DMA + async; measured pinned H2D **[a] GB/s** vs GDDR6 320 GB/s [9]. Small footnote: "Unified Memory migrates pages on demand; zero-copy reads host RAM over PCIe per access" [1] [2] | Taabish | 0:40 | 86 | 45 |
| 4 | 1b. CUDA model: host, device, <<<grid, block>>> | [IMAGE: D2_cuda_hierarchy.png] left; [IMAGE: code_snippets/1_kernel_index_maths.txt as a code box] and [IMAGE: code_snippets/2_launch_config.txt as a code box] right. Label: "16 x 16 = 256 threads = 8 warps; 480 x 270 blocks on 40 SMs" | Taabish | 0:40 | 89 | 30 + code |
| 5 | 1b. Each CUDA feature, and what it does to speed-up | Left: variant table (v1 1D grid, v2 2D tiles, v3 bilinear, v4 pageable, v5 streams, v6 texture) with one "effect" column taken from Task1_Answers.md, trimmed to 5 words each. Right: [IMAGE: results/g1_speedup.png] over [IMAGE: results/g2_stage_breakdown.png]. Callout: "Kernel **[K]x**, end to end **[E]x**: copies = **[C]%** of GPU time (Amdahl)". Footer: "T4, one CPU core baseline, mean of 10 runs after warm-up" | Taabish | 0:45 | 99 | 60 |
| 6 | 1c. GPUDirect Storage: helps the bulk pipeline, not one photo | [IMAGE: D3_gpudirect_storage.png]; two short columns Helps / Does not help (from Task1_Answers.md 1c verdict); cites [11] [13] [15] [16] | Taabish | 0:35 | 83 | 45 |
| 7 | 2a. Energy: the grid matters more than the chip | [IMAGE: task2/charts/C2_iea_datacentre_electricity.png] left, [IMAGE: C1_top500_green500_efficiency.png] right; 3 cited bullets from Task2_Slide_Content slide 1 | Erwyna | 0:40 | 90 | 35 |
| 8 | 2a. Malaysia lens and a myth check | Kajaani vs Johor table (already written in Task2_Slide_Content); one line "More CO2 than aviation = 2030 projection, not today [15] [16]" | Erwyna | 0:25 | 54 | 50 |
| 9 | 2b. Data governance, security and fairness | 4 cited bullets (US share [25]; gradient leakage [27]; dual-use export controls + Malaysia permit [29] [31]; Malay 0.086% of web text [2]). [IMAGE: optional Canva sketch: data shards in two countries, all-reduce arrows crossing a border] | Erwyna | 0:40 | 96 | 40 |
| 10 | 2c. The compute divide | [IMAGE: C3_epoch_training_compute.png] large; 3 cited bullets (industry share [3], 1 to 8 GPUs [40], Gadi 776 GPUs ~3x oversubscribed [42] [43]) | Erwyna | 0:35 | 76 | 30 |
| 11 | 2d. Frameworks, and our SCALE checklist | [IMAGE: C4_SCALE_framework.png] large; one line "Principles give values, not metrics [47] [48] [50]; EU gives numbers [53] [54]" | Erwyna | 0:40 | 96 | 25 |
| 12 | Limitations and future work | Two columns. Task 1: one-core CPU baseline; shared Colab VM; GDS not testable on Colab; cropped corners, RGB PPM only. Task 2: energy figures mostly estimates [38]; Green500 is FP64, AI trains BF16/FP8; carbon-aware 1 to 2% fleet-wide [64]. Future: nvJPEG + GDS + streams on a GDS server; Slurm energy accounting of our kernel [60] [61] | Erwyna | 0:25 | 63 | 60 |
| 13 | Q&A | "Questions" + both names. Nothing else. Separate section as the brief requires (Task 3c) | Erwyna | 0:05 | 9 | 5 |
| | **Main talk total** | | T 3:00 / E 3:40 | **6:45 at 140 wpm incl. buffer; 6:25 if all {braces} dropped** | 928 (870 core) | |

**APPENDIX (after Q&A). Slide header on every one: "APPENDIX: extra material for Q&A, not part
of the 7-minute talk".**

| # | Title | Content | Owner |
|---|---|---|---|
| A1 | Measured results, 8K at 30 degrees | Screenshot or table of section 8 "8K pipelines" (CPU, H2D, kernel, D2H, total, kern-SU, e2e-SU, mismatch) **YOU MUST DO** | Taabish |
| A2 | Pinned vs pageable, and streams | [IMAGE: results/g3_pinned_vs_pageable.png] + [IMAGE: results/g6_streams.png] + [IMAGE: D5_streams_timeline.png] + snippet 3 code box **YOU MUST DO (g3, g6)** | Taabish |
| A3 | Block sweep and image size sweep | [IMAGE: results/g4_block_sweep.png] (occupancy) + [IMAGE: results/g5_size_sweep.png] **YOU MUST DO** | Taabish |
| A4 | How we timed it | snippet 4 (CUDA events), "warm-up discarded, mean of 10", `--fmad=false` for byte-exact checks against the CPU | Taabish |
| A5 | Why PCIe is the narrow pipe | Bandwidth ladder table from Task1_Answers.md 1a + roofline line (about 25 flops/byte balance on T4 [8] [9]) | Taabish |
| A6 | GDS in practice | cuFile call sequence, requirements (nvidia-fs, O_DIRECT, supported FS, compatibility mode) [11] [13] [14] | Taabish |
| A7 | SIMD vs SIMT vs NPU | The paragraph from Task1_Answers.md, 3 rows [20] [21] | Taabish |
| A8 | References: Task 1 (IEEE) | Only the refs cited on slides | Erwyna |
| A9 | References: Task 2 (IEEE) | Only the refs cited on slides; "full list in Task2_Report.pdf" | Erwyna |
| A10 | Generative AI declaration | One line: tools used, what for, "all prompt records in AI_Declaration.pdf" | Erwyna |

---

## 4. REWRITES: speaker lines in Erwyna's voice (numbered to slides)

No em or en dashes. None of the banned words. `[x]` = measured value, YOU MUST DO.
Before → after is shown for the lines that replace a Draft v1 line.

**Slide 1 (Erwyna).**
Before: "Good day everyone. Today we are presenting our analysis on GPU Acceleration..."
After: "Hi, I'm Erwyna and this is Taabish. First, Taabish shows how we rotate large images on a
GPU with CUDA. Then I look at the ethical cost of scaling HPC for AI, and we finish with our
limitations."

**Slide 2 (Taabish).** "An 8K frame has 33 million pixels, and each output pixel depends only
on the input, so the task is data parallel. We use inverse mapping. Each thread owns one
output pixel and applies R transpose to find its source, so there are no holes and no write
races."

**Slide 3 (Taabish).**
Before: "By using pinned memory via cudaMallocHost, we prevent OS page swapping, allowing direct
DMA access over PCIe."
After: "{This is the full round trip.} The CPU decodes the image into DDR5, and cudaMalloc
reserves both buffers in GDDR6. For host to device, the GPU's DMA copy engine pulls the bytes
over PCIe. From pageable memory, the driver must first copy into a pinned staging buffer.
cudaMallocHost gives page-locked memory, so the DMA reads it directly and async copies can
overlap. The kernel then works only in GDDR6, and device to host brings the result back. PCIe
is the narrow pipe: we measured [a] gigabytes per second, against 320 inside the T4."

**Slide 4 (Taabish).** "The host is the controller. It allocates, copies, picks the launch
configuration, launches the kernel asynchronously, then synchronises and checks errors. The
device runs thousands of threads in SIMT style. Our block is 16 by 16, so 256 threads, or 8
warps of 32. For 8K the grid is 480 by 270 blocks, one thread per pixel. Each thread finds its
pixel from blockIdx times blockDim plus threadIdx, and a guard drops threads past the edge.
{Blocks are independent, so they run on any of the T4's 40 SMs.}"

**Slide 5 (Taabish).**
Before: "By processing millions of pixels concurrently, GPUs achieve 20x to 100x speedups
compared to sequential CPU loops."
After: "We built one variant per CUDA feature. 2D blocks beat the 1D grid because a square tile
reads a compact patch of the source, which suits the cache. Against one CPU core, our kernel
alone is [K] times faster, but end to end it is only [E] times, because copies take [C]
percent of GPU time. That is Amdahl's law: more cores cannot shrink the PCIe transfer. The
kernel runs at [B] gigabytes per second, [P] percent of peak, so it is memory bound. Pinned
memory made copies [X] times faster, and streams gave [S] times on a batch."
Check before saying it: if v2 is NOT faster than v1 in the CSV, change the sentence to what
the CSV shows. The deck must match the CSV.

**Slide 6 (Taabish).**
Before: "GPUDirect Storage creates a direct DMA link ... bypassing host CPU RAM and caches."
After: "GPUDirect Storage lets NVMe DMA straight into GPU memory. The CPU keeps only the control
path through cuFile, so the bounce buffer in host RAM goes away. Our verdict: it helps the
company's bulk pipeline, which is I/O bound, if frames are raw or decoded on the GPU with
nvJPEG. It does not help one photo, JPEGs decoded on the CPU, or images already in RAM. {It
also needs nvidia-fs and a supported file system, so we could not test it on Colab.}"

**Slide 7 (Erwyna).** "{AI training is a parallel workload, so its ethics start with energy.}
The IEA puts data centres at 415 terawatt hours in 2024, and about 1,200 by 2035, with GPU
servers driving the growth. Now compare Frontier and LUMI. They use the same Cray nodes and
the same MI250X GPUs, and their GFLOPS per watt are almost equal. But LUMI runs on hydropower
and heats part of a Finnish town. So the carbon cost of a FLOP depends on the grid and on heat
reuse, not only on the chip."

**Slide 8 (Erwyna).** "This matters here. Johor went from 10 megawatts to over a gigawatt in
about three years, and data centres could use almost a third of Peninsular electricity by
2035, on a grid that is 79 percent fossil. One myth check: AI does not emit more CO2 than
aviation today. That is a 2030 projection."
(Fix vs Task2_Slide_Content: "under four years" became "about three years", 2021 to 2024 [17].)

**Slide 9 (Erwyna).** "Where the compute sits decides whose law governs the data. {Three
quarters of AI supercomputer performance is in the US.} In data-parallel training, nodes swap
gradients every iteration, and gradients can leak training samples. So data residency becomes
a scheduler placement rule. Security is the dual-use problem. The same accelerators can train a
hospital model or a military one, so the US limits their export by performance, and since July
2025 Malaysia needs a permit for every US AI chip in transit. Fairness has a compute cost too:
Malay is under 0.1 percent of web text."
(New vs Task2_Slide_Content: the words "security" and "dual-use" are now spoken, closing the
Spec Lawyer's literal miss. Cites [29] [31].)

**Slide 10 (Erwyna).** "This is Epoch AI's data on notable models. Frontier training compute
grows about five times a year, and the best academic model sits about three thousand times
lower. Most academics have one to eight GPUs. That is strong scaling in reverse: fewer
processors, much longer wall time. Public systems help, but NCI Gadi has 776 GPUs and demand
near three times its allocation. And if only companies can train frontier models, only
companies can audit them."

**Slide 11 (Erwyna).**
Before: "we recommend four key strategies: carbon-aware scheduling ..., LoRA and FP8
quantization ..., dynamic hardware power management, and ... NAIRR"
After: "UNESCO, the OECD and Malaysia's AIGE agree on values, but none gives an operator a number
to report. The EU is closer. The AI Act flags models above ten to the twenty-five FLOP, and
sites over 500 kilowatts must report PUE. So we propose SCALE, where each step is a Slurm
setting and a reported number. Size right: stop adding GPUs when parallel efficiency drops.
Carbon-aware: delaying flexible jobs cut emissions by up to 19 percent. Account every joule
with Slurm energy accounting. Keep data Lawful and local. And give Equitable, fair-share access
to small users."

**Slide 12 (Erwyna).** "Our limits. The CPU baseline is one core and Colab is a shared VM, so
our speed-ups belong to that setup. We could not run GDS. For Task 2, most model energy
figures are estimates, and carbon-aware gains fall to 1 to 2 percent across Google's fleet.
Next, we would run the rotation on a GDS server and measure its energy with Slurm."

**Slide 13 (Erwyna).** "Thank you. We are happy to take your questions."

**Task1_Answers.md, line 114 (small edit for the PDF):** "massive numbers of high-resolution
images" → "large numbers of high-resolution images".

---

## 5. EVIDENCE SHE MUST PRODUCE HERSELF

1. **YOU MUST DO (Taabish, by Sat 3 Oct):** Colab, Runtime > T4 GPU, Run all. Download
   `results.zip`. Needed values, all printed in notebook section 10 or tables in section 8:
   [a] pinned H2D GB/s and pageable H2D GB/s (v2, v4); [K] kern-SU and [E] e2e-SU for v2 and
   v3; [C] copy share of v2 GPU time; [B] v2 kernel GB/s and [P] as % of the printed peak;
   [X] pinned vs pageable H2D ratio; [S] v5b streams ratio; best block and its occupancy
   (section 8 block sweep); Amdahl bound line; GPU name as printed. Also check `mismatch` = 0
   for v1 to v4 (v6 small max diff is expected).
2. Fill the "fill from Colab" table in `task1/Task1_Answers.md` with those exact values; then
   the local M3 Max CPU numbers (113 ms, 290 ms) stay only as the "prediction", never on slides.
   If you did not actually run `rotate_cpu.c` locally, delete that sentence.
3. Save g1 to g6 PNGs for slides 5, A2, A3.
4. AI declaration PDF (Erwyna collects): export the full prompt records for Claude (the Task 1
   code, diagrams, charts, report drafts and this panel review), Gemini and ChatGPT (Draft v1),
   and Taabish's own. Add a short cover page: tool, date, what it was used for, what we checked
   ourselves (for example: ran the code, checked every number against the CSV and the source).
5. Two timed run-throughs together, with a phone stopwatch, recorded. Log the times. Cut
   {braces} lines until both runs land 6:30 to 6:50.
6. Each person explains rotate_cuda.cu v2 kernel and the launch line to the other without
   notes (Q&A risk: AI-written code and "little understanding of the code").

---

## 6. Q&A sheet to drill (40% of the mark, the real route to 90)

Format for every answer: verdict, then the mechanism, then our evidence. Under 25 seconds.
Parallel terms, no analogies. Either of us can get any question.

1. *Why is pinned faster than pageable?* Verdict: it removes a copy. Mechanism: DMA needs
   page-locked pages, so pageable data is first copied into the driver's pinned staging
   buffer; pinned is also required for cudaMemcpyAsync to overlap. Evidence: [a] vs [b] GB/s.
2. *Why is end-to-end speed-up so much lower than kernel speed-up?* Amdahl: PCIe copies are a
   part more SMs cannot shrink. Copies are [C]% of GPU time, so the bound is about [bound]x.
3. *Is your kernel compute or memory bound?* Memory bound: about 2 flops per byte against a T4
   balance of about 25, so bandwidth is the roof; we hit [B] GB/s, [P]% of peak.
4. *Walk me through the index maths and why 16 x 16.* x = blockIdx.x * blockDim.x +
   threadIdx.x; guard for the rounded-up grid; 256 threads is 8 full warps; the sweep showed
   [best block] at [occ]% occupancy.
5. *Why inverse mapping?* One writer per output pixel: no holes, no atomics, no sync. We flip y
   before and after R transpose so the turn stays counterclockwise on screen.
6. *Does GDS bypass the CPU completely?* No. It removes the bounce buffer from the data path;
   the CPU still runs the control path (open with O_DIRECT, cuFileHandleRegister, cuFileRead).
   Without nvidia-fs it falls back to compatibility mode, which stages through host RAM.
7. *Would GDS help your benchmark?* No: our images are already in host RAM, and GDS only changes
   the storage to GPU leg. It helps the company's I/O-bound bulk pipeline with raw frames or
   nvJPEG.
8. *What do streams overlap, and why only about 2x?* H2D of one image, kernel of another, D2H of
   a third, on separate copy engines. Time per image goes from the sum toward the max of the
   stages, and H2D and D2H are similar, so the ceiling is about 2x. We measured [S]x.
9. *Does carbon-aware scheduling really work?* Partly: up to 19% in single-region studies [65],
   1 to 2% across Google's fleet [64], because it needs grid variation and deadline slack. So
   SCALE puts Size right first.
10. *Why is efficiency not enough?* Rebound: cheaper compute invites more jobs [72], and demand
    still rises from 415 TWh toward about 945 TWh by 2030 [1]. So we need Account, not only
    better GFLOPS per watt.
11. *What is dual-use here?* The same accelerators serve civilian and military training, so
    chips are controlled by performance threshold [29], and Malaysia now permits every transit
    [31].
12. *What is the weakest part of your work?* One-core CPU baseline on a shared VM, and GDS
    argued from sources, not measured. Next: OpenMP baseline and a GDS server run.

---

## 7. PROJECTED MARK IF ALL ACCEPTED

| Criterion | Now (SM) | After plan | Note |
|---|---|---|---|
| 1a (6) | 4.2 | 5.1 | HD floor; full round trip + D1 |
| 1b (7) | 4.2 | 6.0 | HD only if Colab numbers are on slide 5. Without them: D at best, 4.9 |
| 1c (7) | 4.2 | 6.0 | cited, diagram, verdict for our pipeline |
| Task 2 (20) | 10 | 17 | extensive cited research, comparisons, 4 charts |
| Presentation (20) | 12 | 17 | only if both run-throughs land 6:30 to 6:50 |
| Q&A (40) | 24 | 32 to 36 | the swing factor |
| **Total** | **58.6** | **85 to 89** | |

Honest read: 90+ needs Q&A at 36+ (every answer HD-precise, both people) and a presentation
that sounds rehearsed, not read. The content criteria top out near the HD floor because band
marking rarely gives 95%+ per criterion. If the Colab run does not happen, 1b stays at D and
the total drops about 3 (numbers on slides 3 and 5 also feed Q&A answers 1 to 4 and 8).
