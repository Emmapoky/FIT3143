////////////////////////////////////////////////////////////////////////////
// task2.c
// -------------------------------------------------------------------------
// FIT3143 Lab #2 Task 2: prime search with Open MPI and OpenMP together.
//
// Same search as task1.c, but every MPI process now runs a team of threads.
// The stride picks the process's share, OpenMP splits that share across the
// threads. Writes to primes_task2.txt.
//
// Written by: Taabish Farooq Bhat (35473932)
//
// Team:
//   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
//   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
//
// Compile: mpicc -O2 task2.c -o task2 -lm -fopenmp
//          on macOS: -Xpreprocessor -fopenmp -I$(brew --prefix libomp)/include
//                    -L$(brew --prefix libomp)/lib -lomp
// Run:     OMP_NUM_THREADS=<t> mpirun -np <procs> ./task2 <n>
////////////////////////////////////////////////////////////////////////////
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <math.h>
#include <mpi.h>
#include <omp.h>
#include <stdint.h>
#include <string.h>   // Taabish: memcpy needs this, missed it the first time round

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
    // Same two pairs of timers as task1.c: whole run, and the search on its own.
    double start_time, comp_start, comp_end, end_time;

    // Taabish: FUNNELED is enough here. Only the main thread ever calls MPI,
    // the worker threads just search, so asking for a stronger level would be
    // paying for locking we never use.
    MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provided);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    start_time = MPI_Wtime();

    if (rank == 0) {
        if (argc < 2) {
            fprintf(stderr, "Usage: mpirun -np <procs> %s <n>\n", argv[0]);
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        n = strtoull(argv[1], NULL, 10);
    }

    MPI_Bcast(&n, 1, MPI_UNSIGNED_LONG_LONG, 0, MPI_COMM_WORLD);

    comp_start = MPI_Wtime();

    // Determine candidate counts per rank
    // Rough count of candidates, only used to size the thread buffers.
    uint64_t total_odds = (n > 3) ? ((n - 1 - 3) / 2 + 1) : 0;
    
    // One buffer per thread. Nothing shared on the hot path, so no lock and
    // no false sharing.
    int max_threads = omp_get_max_threads();
    size_t *thread_counts = (size_t *)calloc(max_threads, sizeof(size_t));
    size_t thread_capacity = (total_odds / (size * max_threads)) + 1024;
    
    uint64_t **thread_buffers = (uint64_t **)malloc(max_threads * sizeof(uint64_t *));
    for (int t = 0; t < max_threads; t++) {
        thread_buffers[t] = (uint64_t *)malloc(thread_capacity * sizeof(uint64_t));
    }

    // Taabish: dynamic scheduling matters here. A thread that draws a cheap
    // chunk comes straight back for another one, so they even out on their own
    // instead of being fixed up front like the MPI stride is.
    #pragma omp parallel
    {
        // Each thread keeps its own count and pointer, so nothing in the loop
        // below touches shared state.
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

    // Flatten the per thread buffers into one array for this rank before the
    // gather.
    // Total for this rank: every thread's haul, plus 2 if we are rank 0.
    size_t rank_total = 0;
    if (rank == 0 && n > 2) rank_total += 1; // Include prime 2
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

    comp_end = MPI_Wtime();

    // Gather overall results to Root
    // Counts go up first so the root can work out where each rank's block
    // belongs, same two stage gather as task1.c.
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

    // Root sorts and writes. Arrives interleaved because of the stride, so
    // the qsort is not optional.
    if (rank == 0) {
        qsort(all_primes, total_primes, sizeof(uint64_t), compare_uint64);

        FILE *fout = fopen("primes_task2.txt", "w");
        if (fout) {
            for (int i = 0; i < total_primes; i++) {
                fprintf(fout, "%llu\n", (unsigned long long)all_primes[i]);
            }
            fclose(fout);
        }

        end_time = MPI_Wtime();

        printf("Task 2 (Hybrid Open MPI + OpenMP) Summary:\n");
        printf("  Input n: %llu\n", (unsigned long long)n);
        printf("  MPI Processes: %d | OMP Threads per Process: %d\n", size, max_threads);
        printf("  Total Primes Found: %d\n", total_primes);
        printf("  Computation Time: %.4f seconds\n", comp_end - comp_start);
        printf("  Total Wall Clock Time: %.4f seconds\n", end_time - start_time);

        free(recv_counts);
        free(displacements);
        free(all_primes);
    }

    free(rank_primes);
    MPI_Finalize();
    return 0;
}