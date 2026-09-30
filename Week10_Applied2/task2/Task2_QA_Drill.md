# Task 2 Q&A Drill

Format for every answer: **verdict**, then **mechanism** in parallel computing terms, then **evidence** with a number. Name the challenge before giving the fix. Reference numbers match `references.md`.

---

**1. What is PUE, and why is it not enough on its own?**
PUE is total facility energy divided by IT equipment energy, so 1.0 means zero overhead for cooling and power delivery. Frontier runs at about 1.03 against an industry average of 1.54 [7], [70]. PUE ignores where the electricity comes from, so a site on a coal grid can have a perfect PUE and a high carbon footprint; that is why we also ask for CUE (carbon) and WUE (water).

**2. Frontier and LUMI have almost the same GFLOPS/W. So why is LUMI "greener"?**
The challenge is that GFLOPS/W only measures conversion of electricity into FLOPs. Both use HPE Cray EX235a nodes with MI250X GPUs on Slingshot-11 and score about 55 and 53 GFLOPS/W [6]. LUMI's grid is 100% hydropower and its waste heat supplies up to 20% of Kajaani's district heating [8], so its carbon per FLOP is far lower.

**3. How would carbon-aware scheduling work in SLURM?**
The challenge is that grid carbon intensity changes by hour, but the scheduler normally only sees nodes and priorities. A carbon-aware policy reads a carbon-intensity forecast and holds jobs that have deadline slack (for example with a begin time or a low-priority partition) until a cleaner window, as Google does with virtual capacity curves [64]. Wiesner et al. found up to about 19% less CO2 for ML jobs that can wait days and be paused [65]; Google's fleet saw 1 to 2% at peak-carbon hours [64].

**4. Why does Amdahl's law matter for energy, not just speed?**
Amdahl's law says the serial fraction caps speedup, so past some processor count each extra GPU adds little speed [68]. But every GPU still draws power while it waits on the serial part or on all-reduce communication. Energy is power times time, so poor parallel efficiency burns energy for no work; Llama 3 405B ran at only 38 to 43% MFU on up to 16K H100s [22].

**5. What is data sovereignty, and how does it affect distributed training?**
Data sovereignty means data is governed by the laws of the place where it is stored or processed. In data-parallel training every node exchanges gradients through all-reduce each iteration, and gradients can leak training samples [27], so a cluster spanning countries moves data-derived information across borders. The fix is to make residency a placement constraint for the scheduler, or use federated learning, which keeps raw data on site at the cost of more communication rounds [28].

**6. Why is Malaysia's data centre boom an ethical issue?**
It concentrates large power and water loads on a mostly fossil grid. Johor grew from about 10 MW in 2021 to about 1.3 GW in 2024 [17], data centres could reach 31% of Peninsular demand by 2035 [18], and 79% of Malaysian electricity was fossil in 2025 [21]. Johor has stopped approving water-heavy Tier 1 and 2 designs [20], and unlike Kajaani it has no heating demand to reuse waste heat.

**7. Do AI data centres really emit more CO2 than aviation?**
No, not today. That claim comes from an Accenture projection for 2030 reported by Sherwood News [15]. The IEA estimates all data centres emitted about 180 Mt CO2 in 2024, around 0.5% of combustion emissions, rising to 300 to 500 Mt by 2035 [16], [1]; the accurate statement is that data centre emissions are among the few still growing.

**8. How many GPUs does a 1 GW AI data centre hold?**
Roughly 650,000 H100-class GPUs, not a few thousand. An H100 is rated up to 700 W [23], and with host CPUs, NICs and power supplies each GPU needs about 1.3 kW; SemiAnalysis sizes a 100,000 GPU cluster at over 150 MW [24]. At that scale the interconnect and failure rate limit scaling: Llama 3 had 466 job interruptions in 54 days [22].

**9. Why is the EU AI Act threshold written in FLOP?**
Training compute is the one input that is measurable and scales with capability, so the Act presumes systemic risk above 10^25 FLOP [53]. That is about the same as running Frontier at its full HPL speed of 1.353 EFLOP/s for 100 days [5]. The limitation is that efficiency gains let capable models be trained below the threshold.

**10. How does unequal access to HPC create unfairness, in parallel computing terms?**
Frontier-scale training needs strong scaling across tens of thousands of GPUs, which only industry can afford. Over 90% of notable 2025 models came from industry [3], the best academic model is about 3,000 times below the frontier [38], and 85% of surveyed academics had no cloud budget [40]. With 1 to 8 GPUs, wall time grows so much that frontier work and independent audits become impossible.

**11. What does national HPC like NCI Gadi fix, and what can it not fix?**
It fixes access, not scale. Gadi offers merit-based, fair-share allocation on 776 GPUs [42], but demand was nearly 3 times the national allocation [43], and Colossus alone had 200,000 chips [25]. So shared systems keep academic research alive and auditable, but they cannot compete on frontier model size.

**12. How does SLURM measure energy per job, and what is the catch?**
The AcctGatherEnergyType plugin reads RAPL, IPMI or GPU sensors, and `sacct` reports the result as ConsumedEnergy in joules [60], [61]. The catch is that Slurm only guarantees the value for exclusive node allocations, because shared nodes cannot split the reading cleanly between jobs [61]. For GPUs, NVIDIA DCGM job statistics give per-job energy through prologue and epilogue scripts [62].

---

### Backup questions (short)

- **Why not just buy carbon offsets?** Offsets do not cut grid load at peak hours; scheduling and power caps reduce actual kWh at almost no cost [64], [66].
- **Does power capping hurt performance?** Slightly. BERT capped at 150 W used 87.7% of the energy for 108.5% of the time [66]; watch for users submitting extra jobs to compensate [72].
- **Why does tokenisation matter for fairness?** A Tamil prompt needs about 10 tokens per word [33], so it costs more inference FLOPs for the same meaning.
