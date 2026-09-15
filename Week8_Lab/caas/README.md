# CAAS run

**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu) and Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)
**Written by:** Erwyna Soo Wen Xin

We ran Task 1 and Task 2 on Monash CAAS on 9 September 2026, as job 39361. The job used 8 MPI processes, 4 on each of two compute nodes, so the gather had to travel over the network instead of being a memory copy inside one machine.

| File | What it is |
|---|---|
| `run_all.job` | The job we submitted. It builds the programs, runs the serial baseline, runs Task 1 at 1, 2, 4 and 8 processes across both nodes, runs the timed copy of Task 1 for the phase split, runs Task 2 with one process on each node, and checks the output against the serial reference. |
| `serial.job`, `mpi.job`, `hybrid.job` | The same steps as separate jobs, for running one part at a time. |
| `caas_results.txt` | The raw output of job 39361. |
| `CAAS_Analysis.pdf` | What we worked out from that output. |

## Running it

1. Connect to the Monash VPN (GlobalProtect).
2. Log in with `ssh <authcate>@student-caas-headnode.rep.monash.edu`.
3. Copy our working folder up. The job files expect `task1.c`, `task2.c` and the timed copies of the programs in the folder above this one.
4. From inside this folder, run:

```
sbatch run_all.job
squeue -u $USER
cat caas_results.txt
```

`squeue` shows R while the job is running and PD while it is waiting, and the job disappears from the list once it has finished. If the Open MPI module has a different name on the cluster, check `module avail` and change the `module load` line in the job file.

## Results

- 10.31x faster than the serial baseline at 8 processes, with 86.4% parallel efficiency.
- Amdahl's Law predicted every measured point to within 2%.
- The gather was about 4.6 times slower across the network, but still only about 0.12% of the run.
