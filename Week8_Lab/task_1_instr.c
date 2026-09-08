////////////////////////////////////////////////////////////////////////////
// task_1_instr.c
// -------------------------------------------------------------------------
// FIT3143 Lab #2 Task 3: instrumented copy of task_1.c.
//
// This is task_1.c with phase timers added and nothing else changed. The
// search loop, the partitioning and the collectives are byte for byte the
// ones Taabish wrote, so any time this program reports is a time the real
// task_1.c also pays.
//
// Written by: Erwyna Soo Wen Xin (36555789)
// Search / partitioning / collectives by: Taabish Farooq Bhat (35473932)
//
// Team:
//   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
//   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
//
// Erwyna: why a separate instrumented file instead of putting the timers in
// task_1.c. Two reasons. task_1.c is what we submit as the Task 1 answer and
// I did not want to clutter it with a dozen MPI_Reduce calls that only exist
// to serve the Task 3 write up. And the reductions themselves cost time, so
// leaving them in would make our headline Task 1 numbers slightly worse than
// the code we are actually claiming. Measuring instrument separate from the
// thing being measured.
//
// Erwyna: the five phases and why I split them exactly here.
//   t_bcast   n goes out to every rank. Communication.
//   t_comp    the search loop. This is the ONLY part that gets faster when we
//             add processes, so this is the parallel fraction r_p.
//   t_gather  Gather of the counts + Gatherv of the primes. Communication,
//             and it gets WORSE with more processes, so this is kappa.
//   t_sort    qsort on the root. Root only, no amount of ranks helps.
//   t_write   fprintf of ~1.8 million lines. Root only. Serial fraction r_s.
//
// For t_comp and t_gather I take the MAX across ranks, not rank 0's own
// value. A collective finishes when the slowest rank arrives, so the max is
// what the wall clock actually feels. Taking rank 0's value would quietly
// hide any load imbalance, which is exactly the thing I am trying to measure.
//
// Compile: mpicc -O2 task_1_instr.c -o task_1_instr -lm
// Run:     mpirun -np <procs> ./task_1_instr <n>
// Output:  one CSV line on stdout prefixed with PHASE, so run_benchmarks.sh
//          can grep it straight out without parsing prose.
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

    // Erwyna: barrier so every rank starts its clock at the same instant.
    // Without it, ranks that finish MPI_Init early start timing early and
    // their "communication" time silently swallows the launch skew of the
    // slow ranks. This is the same trap the Week 7 extra class showed with
    // the four second MPI_Recv that was really three seconds of waiting.
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

    // Erwyna: this barrier is the whole point of the second version of
    // this file. Without it, a rank that finishes its share early goes
    // straight into MPI_Gather and sits there until the slowest rank
    // arrives, and that waiting is charged to "communication". It is
    // not communication, it is load imbalance, and the two want very
    // different fixes. The barrier drains the wait into its own
    // measurable phase so the gather time that follows is the real
    // cost of moving the data.
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

    // Erwyna: max over ranks, per the comment at the top of the file.
    // comp also gets a MIN and a SUM so I can quantify the imbalance
    // directly: max/mean is 1.00 when the split is even and climbs from
    // there, and min tells me whether some rank is doing nothing at all.
    MPI_Reduce(&d_bcast,  &m_bcast,  1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_comp,   &m_comp,   1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_comp,   &n_comp,   1, MPI_DOUBLE, MPI_MIN, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_comp,   &s_comp,   1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_imbal,  &m_imbal,  1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_gather, &m_gather, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    // Erwyna: set RANKDUMP=1 to get one line per rank. This is what
    // proves the residue-class problem rather than just hinting at it.
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
