# FIT3143 Week 5 Applied - MPI Practice

> Note on authorship: the `solution/` code in this folder was drafted with AI assistance
> (Claude) and then compiled and executed locally to verify it. This practice activity is
> optional and unassessed (0 marks, no submission), but the AI-use note is kept here per
> Monash policy. Everything under `untouched/` is exactly as the teaching team provided it.

## Layout

- `untouched/` - the contents of `Applied_Week_5.zip` exactly as downloaded from Moodle.
  Do not edit anything here; it is the reference for seeing what was changed.
- `solution/` - working versions of Activities 1 to 5 from the "Week 5 MPI Practice" PDF.
  Compiled binaries live in `solution/build/`.

## What was edited, file by file

| Solution file | Base | What was added |
|---|---|---|
| `activity1_helloworld.c` | solution printed in the practice PDF | typed in as given (modern `int main(int, char**)` signature) |
| `activity2_sendrecv.c` | none (written from scratch) | whole file: rank 0 reads an int, `MPI_Send`s to every rank, loop until negative |
| `activity2_bcast.c` | none (written from scratch) | whole file: same behaviour via one `MPI_Bcast` |
| `activity3_typestruct.c` | template in the practice PDF (Activity 3) | 3 missing pieces: struct members `int a; double b;`, the `MPI_Type_create_struct(...)` call, the `MPI_Bcast(&values, 1, Valuetype, ...)` call |
| `activity4_packunpack.c` | template in the practice PDF (Activity 4) | 4 missing lines: two `MPI_Pack` calls (rank 0) and two `MPI_Unpack` calls (all ranks) |
| `activity5_pi_serial.c` | `untouched/Sample_Code/pi.c` | unchanged copy, kept here for side-by-side benchmarking |
| `activity5_pi_mpi.c` | `untouched/Sample_Code/MPI_PI_StarterCode.c` | the three "To be completed" blocks: `MPI_Bcast` of N, contiguous block partitioning (first `N % size` ranks take one extra iteration), `MPI_Reduce` sum + root prints Pi and timings |

Everything not listed in the right column is the tutor's scaffold, kept verbatim
(including its comment typos). `diff untouched/Sample_Code/MPI_PI_StarterCode.c
solution/activity5_pi_mpi.c` shows the exact edits.

## Build and run (Mac, Open MPI via Homebrew)

```
cd solution
mpicc -Wall -o build/activity5_pi_mpi activity5_pi_mpi.c -lm
mpirun -np 4 ./build/activity5_pi_mpi 100000000
```

Interactive programs (activities 2 to 4) read from the terminal on rank 0; enter a
negative integer to quit. VS Code tasks "MPI: mpicc build active file (Mac)" and
"MPI: run active file with 4 processes (Mac)" do the same from the editor.

## Verified results (M-series Mac, 14 cores, 2026-08-25)

| Program | N | Time (s) | Speedup vs serial |
|---|---|---|---|
| `activity5_pi_serial` | 100,000,000 | 0.879 | 1.0 |
| `activity5_pi_mpi -np 4` | 100,000,000 | 0.227 | 3.9x |
| `activity5_pi_mpi -np 8` | 100,000,000 | 0.120 | 7.3x |

Pi = 3.141592654 in all runs (matches to 9 decimal places). A remainder case
(N=100, np=3) was also checked to confirm the partitioning covers every interval
exactly once.

## Quirks to remember for the oral/demo

- The Pi starter's `argc < 2` check only makes the root rank exit; the other ranks
  would then block forever in `MPI_Bcast`. That is in the provided scaffold - always
  pass N on the command line (`mpirun -np 4 ./prog 100000000`).
- `MPI_Bcast` needs the same `count` on every rank; that is why Activity 4 broadcasts
  the full `buf_size` even though `position` may be smaller.
- Output line ordering across ranks is nondeterministic; `fflush(stdout)` after each
  `printf` keeps lines from interleaving mid-line.
