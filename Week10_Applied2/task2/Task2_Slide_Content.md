# Task 2 Slide Content: Ethical Implications of Scaling HPC for AI

Presenter: Erwyna Soo Wen Xin. Section length: about 3 minutes 54 seconds (547 words) at about 140 words per minute.
Reference numbers match `Task2_Report.md` and `references.md`. Put the source line under each chart as it appears in the PNG.

---

## Slide 1. Energy: the grid matters more than the chip

**Bullets**
- Data centres: 415 TWh in 2024, about 1,200 TWh by 2035 [1]
- GPU server power grows 30% a year, conventional 9% [1]
- Frontier and LUMI: same MI250X design, about 55 vs 53 GFLOPS/W [6]
- LUMI adds hydropower and heat reuse; Frontier uses the US grid [8]

**Visual:** `charts/C2_iea_datacentre_electricity.png` (left) and `charts/C1_top500_green500_efficiency.png` (right)

**Speaker notes (110 words, about 47 s)**
> Modern AI is a parallel workload, so its ethics start with energy. The IEA puts data centres at 415 terawatt hours in 2024. By 2035 that is about 1,200 in the base case, and GPU servers drive the growth. Now compare two supercomputers. Frontier and LUMI use the same Cray nodes, the same MI250X GPUs and the same Slingshot interconnect. Their GFLOPS per watt are almost equal, and Frontier's PUE is about 1.03, so the building is efficient too. But LUMI runs on hydropower and heats part of a Finnish town. So the carbon cost of a FLOP depends on the grid and heat reuse, not only on the chip.

## Slide 2. Malaysia lens and a myth check

**Bullets**
- Johor: about 10 MW in 2021 to 1.3 GW by 2024 [17]
- Data centres could reach 31% of Peninsular demand by 2035 [18]
- 79% fossil grid; Johor blocks water-heavy Tier 1 and 2 [21], [20]
- "More CO2 than aviation" is a 2030 projection, not today [15], [16]

**Visual:** two-column table, Kajaani vs Johor (grid, cooling, heat reuse, water). No chart.

**Speaker notes (90 words, about 39 s)**
> This matters here. Johor went from ten megawatts to over one gigawatt in under four years. By 2035 data centres could use almost a third of Peninsular electricity, and our grid is still 79 percent fossil. Kajaani can reuse its waste heat; Johor has no heating demand to absorb it. Johor has already stopped approving water-heavy designs. One correction to a common claim: AI data centres do not emit more CO2 than aviation today. That figure is a 2030 projection. All data centres emit about 180 megatonnes now, still rising.

## Slide 3. Data governance, security and fairness

**Bullets**
- 75% of AI supercomputer performance is in the US [25]
- Data-parallel training moves gradients across borders; gradients can leak data [27]
- Malaysia now requires a permit for US AI chip transit [31]
- Malay is 0.086% of web text; Tamil needs about 10x tokens [2], [33]

**Visual:** simple diagram: data shards on nodes in two countries, all-reduce arrows crossing a border line. (Optional; build in slides.)

**Speaker notes (96 words, about 41 s)**
> Compute location also decides whose law governs the data. Three quarters of AI supercomputer performance is in the US. In data-parallel training, nodes swap gradients every iteration, and gradients can leak training samples. So data residency becomes a scheduler placement rule, and Malaysia's 2024 PDPA amendments add cross-border transfer rules. Security works the same way: since July 2025 Malaysia needs a permit for every US AI chip moving through. Fairness has a compute cost too. Malay is under a tenth of a percent of web data, and a Tamil prompt needs about ten times more tokens.

## Slide 4. Unequal access: the compute divide

**Bullets**
- Over 90% of notable 2025 models came from industry [3]
- Top academic model is about 3,000x below the frontier [38]
- 85% of surveyed academics had zero cloud budget [40]
- NCI Gadi: 776 GPUs, demand nearly 3x allocation [42], [43]

**Visual:** `charts/C3_epoch_training_compute.png`

**Speaker notes (91 words, about 39 s)**
> This chart is Epoch AI's data on notable models. Frontier training compute grows about five times a year. Blue is industry, orange is academia, and the best academic model sits about three thousand times lower. Most academics work with one to eight GPUs. That is strong scaling in reverse: fewer processors, much longer wall time. Public systems like NCI Gadi help, but Gadi has 776 GPUs and is three times oversubscribed. Its value is fair-share allocation, not raw scale. If only companies can train frontier models, only companies can audit them.

## Slide 5. Frameworks, and our SCALE checklist

**Bullets**
- UNESCO, OECD, Australia, Malaysia AIGE: shared values, no metrics [47], [50]
- EU: 10^25 FLOP model threshold; 500 kW sites report PUE [53], [54]
- Carbon-aware scheduling: up to 19% less CO2 [65]
- SCALE: Size right, Carbon-aware, Account, Lawful data, Equitable access

**Visual:** `charts/C4_SCALE_framework.png`

**Speaker notes (97 words, about 42 s)**
> The ethics frameworks agree on values, but none gives an operator a number to report. The EU is closer: its AI Act flags models above ten to the twenty-five FLOP, and data centres over 500 kilowatts must report PUE. So we propose SCALE, where each step maps to a Slurm setting and a reported number. Size right: stop adding GPUs once parallel efficiency drops, as Amdahl predicts. Carbon-aware scheduling: delaying flexible jobs cut emissions up to 19 percent. Account every joule with Slurm energy accounting. Keep data lawful and local. And give fair-share access to small users.

## Slide 6. Limitations and future work

**Bullets**
- Most model energy figures are estimates, not measurements [38]
- Green500 uses FP64 HPL; AI trains in BF16 or FP8
- Carbon-aware gains shrink at fleet scale: 1 to 2% [64]
- Next: measure our Task 1 kernel's energy with Slurm

**Visual:** none, or a small icon row. Keep it clean.

**Speaker notes (63 words, about 27 s)**
> Our limits. Most model energy numbers are estimates, because few operators publish them. Green500 measures FP64, while AI trains in lower precision, so our comparisons are order-of-magnitude. And carbon-aware gains are smaller at fleet scale, about one to two percent for Google. Next, we want to measure it: run a strong-scaling sweep of our Task 1 kernel with Slurm energy accounting. Thank you.

---

## Timing summary

| Slide | Words | Time at 140 wpm |
|---|---|---|
| 1 Energy | 110 | 0:47 |
| 2 Malaysia and myth check | 90 | 0:39 |
| 3 Governance, security, fairness | 96 | 0:41 |
| 4 Compute divide | 91 | 0:39 |
| 5 Frameworks and SCALE | 97 | 0:42 |
| 6 Limitations | 63 | 0:27 |
| **Total** | **547** | **about 3:54** |

## Kajaani vs Johor table (for Slide 2)

| | Kajaani, Finland (LUMI) | Johor, Malaysia |
|---|---|---|
| Grid | 100% hydropower [8] | Malaysia 79% fossil in 2025 [21] |
| Cooling | Cold climate | Tropical, water or chillers |
| Waste heat | Up to 20% of town heating [8] | No heating demand |
| Water policy | Not a constraint | Tier 1 and 2 no longer approved [20] |
