# Running this on CAAS

**Owner: Taabish.** This is the one measurement we have not taken, and both the
Task 1 and the Task 2 rubric rows ask for it by name in their D and HD bands:
*"Performance analysis using CAAS or a locally set up cluster is included."*

Everything in this folder is ready to submit. It has not been run, because it
needs a Monash account on the cluster and the Australia VPN.

## Steps

1. Connect to the Monash Australia VPN (`vpn.monash.edu` via GlobalProtect).
   Required from anywhere, including Malaysia.
2. `ssh <your-monash-id>@<caas-host>` using the host name given in the unit's
   Additional Information and Resources section on Moodle.
3. Copy this whole `Week8_Lab` folder up, with FileZilla or `scp -r`.
4. From inside `Week8_Lab/caas`:

```
sbatch serial.job
sbatch mpi.job
sbatch hybrid.job
squeue -u $USER          # R means running, PD means pending
cat mpi.<jobid>.out      # once it disappears from squeue
```

## What to look for, and why it matters to our argument

On our laptop, communication was negligible: kappa reached only 0.004 of runtime
at 28 processes, because every rank shared one node and `MPI_Gatherv` was a
memory copy. `mpi.job` deliberately splits 8 ranks across 2 nodes, so the same
gather becomes real network traffic.

The number to bring back is the **gather phase time** from `task_1_instr.c`. If
it is orders of magnitude larger than the 0.036 s we measured locally, that
confirms the limitation we state on the closing slide and in section 8 of
`Task3_Performance_Evaluation.md`, and it turns an admitted gap into a measured
result.

To get the phase split rather than just the total, swap `task_1.c` for
`task_1_instr.c` in `mpi.job` and read the `PHASE,` line out of the output.

## If you want the whole sweep instead of one point

`run_benchmarks.sh` takes environment overrides, so a reduced sweep fits inside a
job's time limit without editing anything:

```
N_MAX=40000000 WIDTHS="1 2 4 8 16" REPS=1 ./run_benchmarks.sh
```

## Notes

- The `module load openmpi` line may need a different module name. Run
  `module avail` and use whatever the cluster actually calls it.
- `--partition=defq` may need changing to the partition the unit tells you to
  use. Do not change it to something you have not been told to use.
- On Linux, plain `-fopenmp` is correct. The libomp flags in the root README are
  a macOS quirk and are not needed here.
- **Choose a power of two for the process count** if you want a balanced
  partition. At any p with an odd prime factor d, one rank in d does no work.
  That is our headline Task 3 finding and it will show up on the cluster too,
  because it comes from arithmetic in the partitioning rather than from hardware.
