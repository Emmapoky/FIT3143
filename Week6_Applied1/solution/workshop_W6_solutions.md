# Workshop W6 - Worked Solutions (Q1 to Q4)

AI-written prep material (Claude, 2026-08-25). For study only, verify before any assessed use.

Formulas used:

- Aggregate performance: `P = N * C * F * R` (nodes x cores x FLOP/cycle x clock rate)
- Transmission delay per link: `t = L / B + t_other`, with the course convention 1 MB = 1,000,000 bytes and 1 Gbps = 10^9 bps (remember bytes -> bits: x8)

## Q1 - Find the clock rate

10 nodes, 4 cores/node, 8 FLOP per cycle, P = 640 GFLOPS. (The 3200MHz DDR4 RAM is a distractor.)

```
R = P / (N * C * F) = 640e9 / (10 * 4 * 8) = 2e9 Hz = 2 GHz
```

## Q2 - Heterogeneous cluster aggregate performance

Compute each half separately, then sum:

```
New half: 25 * 96 * 16 * 2.4 GHz = 92,160 GFLOPS
Old half: 25 * 12 *  8 * 2.0 GHz =  4,800 GFLOPS
Total                            = 96,960 GFLOPS
```

## Q3 - Ring of 8, 2MB alive messages, 1 Gbps, t_other = 0.004 s

Delay for one message to reach a neighbour:

```
t = (2 * 8,000,000 bits) / 1e9 + 0.004 = 0.016 + 0.004 = 0.020 s
```

| Statement | Verdict | Why |
|---|---|---|
| Period 0.025 s | TRUE | 0.025 > 0.020, message arrives before the next send |
| Period 0.01 s | FALSE | 0.01 < 0.020 |
| Period 0.01 s with 1 MB | FALSE | 0.008 + 0.004 = 0.012 > 0.01 |
| Period 0.01 s with 0.5 MB | TRUE | 0.004 + 0.004 = 0.008 < 0.01 |
| Period 0.017 s with t_other = 0.00001 s | TRUE | 0.016 + 0.00001 = 0.01601 < 0.017 |

## Q4 - 6 nodes, 1 MB message, fault tolerant if all alive nodes reached < 0.03 s with any 1 link cut

Per-hop delay: 1 Gbps -> 0.008 s (budget 3 hops); 10 Gbps -> 0.0008 s (budget 37 hops).

| Statement | Verdict | Why |
|---|---|---|
| Line: not fault tolerant | TRUE | any single cut disconnects a line |
| Line: fault tolerant at 10 Gbps | FALSE | still disconnected; speed cannot restore connectivity |
| Binary tree: not fault tolerant | TRUE | a tree has no redundant links, any cut disconnects it |
| Binary tree: fault tolerant at 10 Gbps | FALSE | same reason |
| Ring: not fault tolerant (1 Gbps) | TRUE | 1 cut leaves a 6-node line, worst case 5 hops = 0.040 s > 0.03 s |
| Ring: fault tolerant at 10 Gbps | TRUE | 5 hops * 0.0008 = 0.004 s < 0.03 s |

Rule of thumb: link-speed upgrades can fix delay failures, never connectivity failures.
