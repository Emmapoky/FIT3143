////////////////////////////////////////////////////////////////////////////
// task_2_instr.c
// -------------------------------------------------------------------------
// FIT3143 Lab #2 Task 3: instrumented copy of task_2.c (hybrid MPI + OpenMP).
//
// Same idea as task_1_instr.c. Taabish's hybrid search is untouched, I have
// only wrapped the phases in timers so I can split the run time into the part
// that scales and the part that does not.
//
// Written by: Erwyna Soo Wen Xin (36555789)
// Search / partitioning / collectives by: Taabish Farooq Bhat (35473932)
//
// Team:
//   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
//   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
//
// Erwyna: the hybrid has one phase task_1.c does not have, the merge of the
// per thread buffers into one per rank buffer. I time it separately rather
// than folding it into t_comp, because it is memcpy work that grows with the
// thread count instead of shrinking with it. If I hid it inside the compute
// phase it would make the parallel fraction look better than it is and the
// Amdahl curve would be optimistic for exactly the configurations where the
// thread count is high, which is where I care most about being honest.
//
// Compile: mpicc -O2 -Xpreprocessor -fopenmp -I$(brew --prefix libomp)/include \
//            -L$(brew --prefix libomp)/lib -lomp task_2_instr.c -o task_2_instr -lm
// Run:     OMP_NUM_THREADS=<t> mpirun -np <procs> ./task_2_instr <n>
////////////////////////////////////////////////////////////////////////////
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <math.h>
#include <mpi.h>
#include <omp.h>
#include <stdint.h>
#include <string.h>

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
    int rank, size, provided;
    uint64_t n = 0;
    double t_start, t_a, t_b, t_m, t_mm, t_c, t_d, t_e, t_end;
    double d_bcast, d_comp, d_merge, d_imbal, d_gather, d_sort = 0.0, d_write = 0.0, d_total;
    double m_bcast, m_comp, m_merge, m_imbal, m_gather, n_comp, s_comp;

    MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provided);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

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

    uint64_t total_odds = (n > 3) ? ((n - 1 - 3) / 2 + 1) : 0;

    int max_threads = omp_get_max_threads();
    size_t *thread_counts = (size_t *)calloc(max_threads, sizeof(size_t));
    size_t thread_capacity = (total_odds / (size * max_threads)) + 1024;

    uint64_t **thread_buffers = (uint64_t **)malloc(max_threads * sizeof(uint64_t *));
    for (int t = 0; t < max_threads; t++) {
        thread_buffers[t] = (uint64_t *)malloc(thread_capacity * sizeof(uint64_t));
    }

    #pragma omp parallel
    {
        int tid = omp_get_thread_num();
        size_t local_cap = thread_capacity;
        size_t local_cnt = 0;
        uint64_t *local_buf = thread_buffers[tid];

        #pragma omp for schedule(dynamic, 1000)
        for (uint64_t i = 3 + (2 * rank); i < n; i += (2 * size)) {
            if (is_prime(i)) {
                if (local_cnt >= local_cap) {
                    local_cap *= 2;
                    local_buf = (uint64_t *)realloc(local_buf, local_cap * sizeof(uint64_t));
                    thread_buffers[tid] = local_buf;
                }
                local_buf[local_cnt++] = i;
            }
        }
        thread_counts[tid] = local_cnt;
    }
    t_b = MPI_Wtime();

    size_t rank_total = 0;
    if (rank == 0 && n > 2) rank_total += 1;
    for (int t = 0; t < max_threads; t++) {
        rank_total += thread_counts[t];
    }

    uint64_t *rank_primes = (uint64_t *)malloc(rank_total * sizeof(uint64_t));
    size_t offset = 0;

    if (rank == 0 && n > 2) {
        rank_primes[offset++] = 2;
    }

    for (int t = 0; t < max_threads; t++) {
        if (thread_counts[t] > 0) {
            memcpy(rank_primes + offset, thread_buffers[t], thread_counts[t] * sizeof(uint64_t));
            offset += thread_counts[t];
        }
        free(thread_buffers[t]);
    }
    free(thread_buffers);
    free(thread_counts);
    t_m = MPI_Wtime();

    // Same barrier, same reason as task_1_instr.c: separate waiting for
    // the slowest rank from the real cost of the gather.
    MPI_Barrier(MPI_COMM_WORLD);
    t_mm = MPI_Wtime();

    int *recv_counts = NULL;
    int *displacements = NULL;
    int rank_cnt_int = (int)rank_total;

    if (rank == 0) {
        recv_counts = (int *)malloc(size * sizeof(int));
    }

    MPI_Gather(&rank_cnt_int, 1, MPI_INT, recv_counts, 1, MPI_INT, 0, MPI_COMM_WORLD);

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

    MPI_Gatherv(rank_primes, rank_cnt_int, MPI_UNSIGNED_LONG_LONG,
                all_primes, recv_counts, displacements, MPI_UNSIGNED_LONG_LONG,
                0, MPI_COMM_WORLD);
    t_c = MPI_Wtime();

    if (rank == 0) {
        qsort(all_primes, total_primes, sizeof(uint64_t), compare_uint64);
        t_d = MPI_Wtime();

        FILE *fout = fopen("primes_task2_instr.txt", "w");
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

    free(rank_primes);

    t_end    = MPI_Wtime();
    d_bcast  = t_a  - t_start;
    d_comp   = t_b  - t_a;
    d_merge  = t_m  - t_b;
    d_imbal  = t_mm - t_m;
    d_gather = t_c  - t_mm;
    d_total  = t_end - t_start;

    MPI_Reduce(&d_bcast,  &m_bcast,  1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_comp,   &m_comp,   1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_comp,   &n_comp,   1, MPI_DOUBLE, MPI_MIN, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_comp,   &s_comp,   1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_merge,  &m_merge,  1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_imbal,  &m_imbal,  1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&d_gather, &m_gather, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        // PHASE,n,procs,threads,primes,bcast,comp,merge,imbal,gather,sort,write,total,comp_min,comp_mean
        printf("PHASE,%llu,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f\n",
               (unsigned long long)n, size, max_threads, total_primes,
               m_bcast, m_comp, m_merge, m_imbal, m_gather, d_sort, d_write, d_total,
               n_comp, s_comp / size);
    }

    MPI_Finalize();
    return 0;
}
