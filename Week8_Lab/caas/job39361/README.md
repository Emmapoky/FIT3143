# CAAS run, job 39361

**Team:** Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu) and Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)

We ran Task 1 and Task 2 on Monash CAAS on 9 September 2026 as job 39361. The job used 8 MPI processes, 4 on each of two compute nodes (`student-caas-n01` and `student-caas-n02`), so the gather had to travel over the network instead of being a memory copy inside one machine.

| File | What it is |
|---|---|
| `run_all.job` | The exact job file that ran as job 39361, and the only job file we ever submitted to CAAS. Earlier submissions of the same file (jobs 39353, 39354, 39355, 39357 and 39360) stopped early, each leaving only a 123 byte log. Just before job 39361 we patched two lines on the head node with `sed`: the serial baseline builds from `../serial_instr.c`, and the correctness check reads `primes_serial_instr.txt`. |
| `caas_results.txt` | The summary the job wrote, exactly as `cat caas_results.txt` printed it on the head node after the job finished. |
| `CAAS_Analysis.pdf` | What we worked out from those numbers. |
| `caas_headnode_check_2026-09-17.txt` | `ls -l` of our CAAS job folder and Slurm's `sacct` record of job 39361, copied from the head node on 17 September 2026. It shows the job and all nine steps COMPLETED across `student-caas-n[01-02]`, and that the job file and results file on CAAS are the same size as the copies here. |

## Things to know when reading these files

- **File names.** At the time of the run our programs were called `task_1.c`, `task_1_instr.c` and `task_2.c`. They were renamed `task1.c`, `task1_instr.c` and `task2.c` afterwards, which is why the build lines in `run_all.job` use the old names. To run the job again with the submitted files, change those three names in the build lines.
- **Program versions.** The run used our 9 September versions of `task1.c` and `task2.c`. On 15 September we added the per rank and per thread timing printouts and the input checks. The search, the partitioning and the MPI and OpenMP calls did not change, but it is why this output has no per rank lines.
- **Balance across ranks.** The PHASE lines still show it: the columns `comp`, `comp_min` and `comp_mean` are the slowest, fastest and average rank's search time. At 2, 4 and 8 processes the slowest and fastest rank were within 0.3% of each other (at 8 processes, 6.443 s against 6.455 s), so the split was balanced across both nodes.
- **Sorted output.** The job checked its Task 1 output against the serial reference ("Task 1 output MATCHES the serial reference"). The prime files it wrote stayed on CAAS. The sorted output of the submitted programs at the same n is in `supporting/primes_output/`, with SHA-256 checksums.

## Results

- 10.31x faster than the serial baseline at 8 processes, with 86.4% parallel efficiency.
- Amdahl's Law predicted every measured point to within 2%.
- The gather was about 4.6 times slower across the network, but still only about 0.12% of the run.
