# AI Use Log (Task 2)

For the team's Generative AI declaration, as the Applied #2 specification requires. Attach the full prompt record as a PDF when submitting.

**Tool:** Claude Code (Anthropic), used on 30 September 2026 during the preparation period only. No AI is used during the presentation or Q&A.

## What was AI-assisted

1. **Reading the brief.** The assessment specification, the rubric (Task 2 row) and the Week 10 supplementary lecture transcript were summarised to set the scope and marking targets.
2. **Source search and verification.** Candidate sources were found and checked against the primary page or PDF: IEA, TOP500 and Green500 June 2026, Epoch AI, the Stanford AI Index, the papers, the government documents and the Malaysian news. Unverifiable claims were dropped or flagged. DOIs and page numbers were checked against Crossref.
3. **Charts.** `make_charts.py` (matplotlib) was drafted with AI help. Every plotted number is copied from a cited source, and the Epoch AI CSV is archived in `charts/`.
4. **Drafting.** First drafts of the report, slide bullets, speaker notes and Q&A answers were produced. The team must review, edit and rehearse all of them.
5. **Formatting.** The IEEE reference list was formatted and the PDF rendered.

## Main prompts and tasks (summary)

- "Build the Task 2 deliverables for FIT3143 Applied #2: Ethical Implications of Scaling HPC for AI ... cover (a) to (d), verify every number and reference, produce the report, charts, slide content, Q&A drill and references."
- "Verify IEA Energy and AI figures, TOP500 and Green500 June 2026, LUMI heat reuse, Strubell, Patterson, BLOOM, water use, the aviation comparison, and Malaysia's data-centre figures."
- "Verify Epoch AI compute data, AI Index industry share, academic GPU access, EU AI Act Article 51 and Annex XI, EU EED data-centre reporting, US export controls and the Malaysian MITI permit, NCI Gadi, EuroHPC and NAIRR."
- "Verify Green AI, the FAccT 2025 bigger-is-better paper, carbon-aware scheduling papers, Slurm energy accounting docs, PUE sources, UNESCO, OECD, Malaysia AIGE, Australia's principles, power capping and Llama 3 MFU."
- Style instructions: concise, no em or en dashes, plain student voice, what, why and so what for every finding, and a limitations slide.

## Corrections made to the unit's supplementary lecture after checking

- GPUs per gigawatt: the lecture's estimate (about 1,000 GPUs per GW) is wrong by orders of magnitude. The correct figure is roughly 650,000 H100-class GPUs per GW [23], [24].
- "AI data centres emit more CO2 than aviation": this is an Accenture 2030 projection, not a current fact [15], [16].
- Frontier's rank and power are updated to the June 2026 TOP500 (3rd, 1.353 EFLOP/s, 24.6 MW) [5].

## Team to do before submission

- Read every cited source you will speak about, so you can answer questions without notes.
- Add the declaration statement and this prompt record (as PDF) to the Moodle submission.
