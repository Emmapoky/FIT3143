# Week 6 - Applied #1 (Distributed Wireless Sensor Network)

Assessed applied session, Week 6, 10% of the unit. Teams of 2, in-person 7-minute
presentation + 2-minute Q&A. Submit slides, design docs, graphs, answers, any code,
and AI declaration + prompt records to Moodle BEFORE the start of class (5%/day late).

## Folders

- `untouched/` - the original course files, unmodified:
  - `Applied #1 - Assessment Specification.pdf`
  - `Applied #1 Rubric.pdf`
  - `FIT3143-Workshop-W6.pptx`
- `solution/` - prep workspace (AI-assisted, declare if reused in the submission):
  - `ERWYNA_part.md` - Erwyna's half: Task 1 + Task 2 structure, slides 1-6, script 0:00-3:30, Q&A prep
  - `TAABISH_part.md` - Taabish's half: Task 2 messages + Task 3 + conclusion, slides 7-12, script 3:30-7:00, Q&A prep
  - `workshop_W6_solutions.md` - worked answers to Workshop W6 Q1-Q4
  - `transmission_delay_model.py` - generates the Task 3 delay graphs (`python3 transmission_delay_model.py`)
  - `wsn_skeleton.c` - minimal MPI proof-of-concept of the grid + base-station architecture
    (`mpicc wsn_skeleton.c -o wsn_skeleton && mpirun -np 10 ./wsn_skeleton`)

## What to prep (short version)

1. Task 1 (10%): compare ALL Week 5 topologies in one table; pick 2-D mesh + star
   overlay to the base station; justify with WSN realism.
2. Task 2 (15%): MPI architecture - MPI_Cart_create grid of node ranks, dedicated
   base-station rank, ports as threads inside each node process (shared memory +
   message passing = the HD line). Two UML diagrams: class + communication.
   Name every message type.
3. Task 3 (15%): t = L/B + t_other per link. Neighbour traffic O(1) in node count,
   base-station alerts O(n), b base stations -> O(n/b) with a synchronisation caveat.
   One graph per message type, for growing nodes AND growing base stations.
4. Task 4: slides in the mandated order, 6-7 minutes rehearsed, conclusion with
   limitations + future work, parallel-computing terminology throughout.

Full walkthrough, oral script, and predicted Q&A: vault note
"FIT3143 Week 06 - Applied Guide" (Obsidian Vault/FIT3143_Parallel_Computing/02_Notes/Week_06/).
