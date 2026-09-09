////////////////////////////////////////////////////////////////////////////
// task1_instr.c
// -------------------------------------------------------------------------
// FIT3143 Lab #2 Task 3: task1.c with phase timers bolted on.
//
// The search, the partitioning and the collectives are Taabish's, untouched.
// All I added is timers, so anything this reports is a cost the real task1.c
// pays too.
//
// Written by: Erwyna Soo Wen Xin (36555789)
// Search and collectives by: Taabish Farooq Bhat (35473932)
//
// Team:
//   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
//   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
//
// Erwyna: kept this as a separate file rather than timing task1.c directly.
// The MPI_Reduce calls that collect the phase times cost something themselves,
// so leaving them in would make our own Task 1 numbers worse than the code we
// are actually submitting.
//
// The phases, and which Amdahl term each one feeds:
//   bcast    n out to every rank                  kappa
//   comp     the search loop, the only part       r_p
//            that gets faster with more ranks
//   gather   Gather + Gatherv of the primes       kappa
//   sort     qsort on the root                    r_s
//   write    fprintf on the root                  r_s
//
// Phase times are the max across ranks, not rank 0's. A collective only
// finishes once the slowest rank turns up, so the max is what you actually
// wait for. Rank 0's own number would hide the imbalance, which is the thing
// I am looking for.
//
// Compile: mpicc -O2 task1_instr.c -o task1_instr -lm
// Run:     mpirun -np <procs> ./task1_instr <n>
// Output:  one PHASE, line on stdout for run_benchmarks.sh to grep.
////////////////////////////////////////////////////////////////////////////
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <math.h>
#include <mpi.h>
#include <stdint.h>

static inline bool is_prime(uint64_t num) {
    if (num <= 1) return false;
    if (num <= 3) return true;
    if (num % 2 == 0 || num % 3 == 0) return false;

    for (uint64_t i = 5; i * i <= num; i += 6) {
        if (num % i == 0 || num % (i + 2) == 0) return false;
    }
    return true;
}

int compare_uint64(const void *a, const void *b) {
    uint64_t arg1 = *(const uint64_t *)a;
    uint64_t arg2 = *(const uint64_t *)b;
    if (arg1 < arg2) return -1;
    if (arg1 > arg2) return 1;
    return 0;
}

int main(int argc, char *argv[]) {
    int rank, size;
    uint64_t n = 0;
    double t_start, t_a, t_b, t_bb, t_c, t_d, t_e, t_end;
    double d_bcast, d_comp, d_imbal, d_gather, d_sort = 0.0, d_write = 0.0, d_total;
    double m_bcast, m_comp, m_imbal, m_gather, n_comp, s_comp;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // Erwyna: barrier so every rank starts its clock together. Otherwise the
    // ranks that clear MPI_Init first start timing early and swallow the
    // launch skew of the slow ones. Same trap as the four second MPI_Recv in
    // the Week 7 extra class that was really just waiting.
    MPI_Barrier(MPI_COMM_WORLD);
    t_start = MPI_Wtime();

    if (rank == 0) {
        if (argc < 2) {
            fprintf(stderr, "Usage: mpirun -np <procs> %s <n>\n", argv[0]);
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        n = strtoull(argv[1], NULL, 10);
    }

    MPI_Bcast(&n, 1, MPI_UNSIGNED_LONG_LONG, 0, MPI_COMM_WORLD);
    t_a = MPI_Wtime();

    size_t capacity = 1024;
    size_t local_count = 0;
    uint64_t *local_primes = (uint64_t *)malloc(capacity * sizeof(uint64_t));
    if (!local_primes) {
        fprintf(stderr, "Rank %d failed to allocate memory.\n", rank);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    if (rank == 0 && n > 2) {
        local_primes[local_count++] = 2;
    }

    // Cyclic / stride partitioning over the odd numbers below n.
    uint64_t start_val = 3 + (2 * rank);
    uint64_t step = 2 * size;

    for (uint64_t i = start_val; i < n; i += step) {
        if (is_prime(i)) {
            if (local_count >= capacity) {
                capacity *= 2;
                local_primes = (uint64_t *)realloc(local_primes, capacity * sizeof(uint64_t));
            }
            local_primes[local_count++] = i;
        }
    }
    t_b = MPI_Wtime();

    // Erwyna: this barrier is the whole point of the file. Without it a rank
    // that finishes early goes straight into MPI_Gather and waits there, and
    // that waiting gets billed as communication. It is not communication, it
    // is imbalance, and the two need completely different fixes. The barrier
    // pulls the wait out into its own phase so the gather time after it is
    // the real cost of shifting the data.
    MPI_Barrier(MPI_COMM_WORLD);
    t_bb = MPI_Wtime();

    int *recv_counts = NULL;
    int *displacements = NULL;
    int local_cnt_int = (int)local_count;

    if (rank == 0) {
        recv_counts = (int *)malloc(size * sizeof(int));
    }

    MPI_Gather(&local_cnt_int, 1, MPI_INT, recv_counts, 1, MPI_INT, 0, MPI_COMM_WORLD);

    uint64_t *all_primes = NULL;
    int total_primes = 0;

    if (rank == 0) {
        displacements = (int *)malloc(size * sizeof(int));
        displacements[0] = 0;
        total_primes += recv_counts[0];

        for (int i = 1; i < size; i++) {
            displacements[i] = displacements[i - 1] + recv_counts[i - 1];
            total_primes += recv_counts[i];
        }

        all_primes = (uint64_t *)malloc(total_primes * sizeof(uint64_t));
    }

    MPI_Gatherv(local_primes, local_cnt_int, MPI_UNSIGNED_LONG_LONG,
                all_primes, recv_counts, displacements, MPI_UNSIGNED_LONG_LONG,
                0, MPI_COMM_WORLD);
    t_c = MPI_Wtime();

    if (rank == 0) {
        qsort(all_primes, total_primes, sizeof(uint64_t), compare_uint64);
        t_d = MPI_Wtime();

        FILE *fout = fopen("primes_task1_instr.txt", "w");
        if (fout) {
            for (int i = 0; i < total_primes; i++) {
                fprintf(fout, "%llu\n", (unsigned long long)all_primes[i]);
            }
            fclose(fout);
        }
        t_e = MPI_Wtime();

        d_sort  = t_d - t_c;
        d_write = t_e - t_d;

        free(recv_counts);
        free(displacements);
        free(all_primes);
    }

    free(local_primes);

    t_end   = MPI_Wtime();
    d_bcast  = t_a  - t_start;
    d_comp   = t_b  - t_a;
    d_imbal  = t_bb - t_b;
    d_gather = t_c  - t_bb;
    d_total  = t_end - t_start;

    // Max over ranks, as above. comp also gets a min and a sum so I can put a
    // number on the imbalance: max over mean is 1.00 when the split is even,
    // and min tells me if a rank is doing nothing at all.
    MPI_Reduce(&d_bcast,  &m_bcast,  1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_comp,   &m_comp,   1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_comp,   &n_comp,   1, MPI_DOUBLE, MPI_MIN, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_comp,   &s_comp,   1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_imbal,  &m_imbal,  1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_gather, &m_gather, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    // RANKDUMP=1 gives one line per rank. This is what actually proves the
    // residue class problem instead of just hinting at it.
    if (getenv("RANKDUMP")) {
        printf("RANK,%d,%d,%.6f,%zu\n", size, rank, d_comp, local_count);
        fflush(stdout);
    }

    if (rank == 0) {
        // PHASE,n,procs,threads,primes,bcast,comp,imbal,gather,sort,write,total,comp_min,comp_mean
        printf("PHASE,%llu,%d,1,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f\n",
               (unsigned long long)n, size, total_primes,
               m_bcast, m_comp, m_imbal, m_gather, d_sort, d_write, d_total,
               n_comp, s_comp / size);
    }

    MPI_Finalize();
    return 0;
}
