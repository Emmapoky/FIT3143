////////////////////////////////////////////////////////////////////////////
// task2.c
// -------------------------------------------------------------------------
// FIT3143 Lab #2 Task 2: prime search with Open MPI and OpenMP together.
//
// Same search as task1.c, but every MPI process now runs a team of OpenMP
// threads. The MPI stride picks each process's share of the odd numbers, and
// OpenMP splits that share across the threads inside the process. Writes the
// sorted primes to primes_task2.txt.
//
// How it runs:
//   1. Rank 0 reads n from the command line and broadcasts it. Inside each
//      process n is an ordinary variable, so every thread can read it.
//   2. Every process searches its stride with an OpenMP parallel for. Each
//      thread keeps its primes in its own buffer and times its own share.
//   3. Each process merges its thread buffers into one array.
//   4. The root gathers the counts, then the primes with one MPI_Gatherv,
//      then every process's timings.
//   5. The root's main thread sorts, writes the file and prints a summary
//      that includes every thread's search time.
//
// Written by: Taabish Farooq Bhat (35473932)
//
// Team:
//   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
//   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
//
// Compile: mpicc -O2 task2.c -o task2 -fopenmp
//          on macOS: -Xpreprocessor -fopenmp -I$(brew --prefix libomp)/include
//                    -L$(brew --prefix libomp)/lib -lomp
// Run:     OMP_NUM_THREADS=<t> mpirun -np <procs> ./task2 <n>
////////////////////////////////////////////////////////////////////////////
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>   // memcpy, used to merge the thread buffers
#include <mpi.h>
#include <omp.h>

// is_prime
// Same test as task1.c: trial division up to sqrt(num), and after ruling out
// 2 and 3, only trying divisors of the form 6k - 1 and 6k + 1.
static inline bool is_prime(uint64_t num) {
    if (num <= 1) return false;
    if (num <= 3) return true;
    if (num % 2 == 0 || num % 3 == 0) return false;

    for (uint64_t i = 5; i * i <= num; i += 6) {
        if (num % i == 0 || num % (i + 2) == 0) return false;
    }
    return true;
}

// compare_uint64
// qsort comparator for uint64_t, same as task1.c.
static int compare_uint64(const void *a, const void *b) {
    uint64_t arg1 = *(const uint64_t *)a;
    uint64_t arg2 = *(const uint64_t *)b;
    if (arg1 < arg2) return -1;
    if (arg1 > arg2) return 1;
    return 0;
}

// fail
// Prints what went wrong and stops every rank. Only called from the main
// thread, because with MPI_THREAD_FUNNELED only the main thread may use MPI.
static void fail(const char *msg, int rank) {
    fprintf(stderr, "Rank %d: %s\n", rank, msg);
    MPI_Abort(MPI_COMM_WORLD, 1);
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

    // Make sure the library really gave us FUNNELED before any threads start.
    if (provided < MPI_THREAD_FUNNELED) {
        fail("this MPI library does not support MPI_THREAD_FUNNELED", rank);
    }

    start_time = MPI_Wtime();

    // Only the root reads n, and it has to be a plain whole number.
    if (rank == 0) {
        if (argc < 2) {
            fprintf(stderr, "Usage: mpirun -np <procs> %s <n>\n", argv[0]);
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        char *end = NULL;
        n = strtoull(argv[1], &end, 10);
        if (argv[1][0] < '0' || argv[1][0] > '9' || *end != '\0') {
            fail("n must be a positive whole number", rank);
        }
    }

    // n goes out to every process. Inside a process it is shared by all the
    // threads, which only ever read it.
    MPI_Bcast(&n, 1, MPI_UNSIGNED_LONG_LONG, 0, MPI_COMM_WORLD);

    comp_start = MPI_Wtime();

    // Number of odd candidates from 3 up to n, only used to size the buffers.
    uint64_t total_odds = (n > 3) ? ((n - 1 - 3) / 2 + 1) : 0;

    // One buffer per thread, each with room for every odd candidate in one
    // thread's share. That's far more than the primes need (about 1 candidate
    // in 9 is prime at n = 130 million), so the realloc in the loop is only a
    // safety net. Each thread only writes to its own buffer, so there is no
    // lock and no false sharing in the loop.
    int max_threads = omp_get_max_threads();
    size_t thread_capacity = (total_odds / (size * max_threads)) + 1024;
    size_t *thread_counts = calloc(max_threads, sizeof(size_t));
    double *thread_times = calloc(max_threads, sizeof(double));
    uint64_t **thread_buffers = malloc(max_threads * sizeof(uint64_t *));
    if (!thread_counts || !thread_times || !thread_buffers) {
        fail("could not allocate the per thread arrays", rank);
    }
    for (int t = 0; t < max_threads; t++) {
        thread_buffers[t] = malloc(thread_capacity * sizeof(uint64_t));
        if (!thread_buffers[t]) fail("could not allocate a thread buffer", rank);
    }

    // Taabish: dynamic scheduling matters here. A thread that draws a cheap
    // chunk comes straight back for another one, so they even out on their own
    // instead of being fixed up front like the MPI stride is.
    #pragma omp parallel
    {
        // Private to each thread: its id, its buffer, its count and its clock.
        int tid = omp_get_thread_num();
        size_t local_cap = thread_capacity;
        size_t local_cnt = 0;
        uint64_t *local_buf = thread_buffers[tid];
        double thread_start = omp_get_wtime();

        // nowait drops the wait at the end of the loop, so each thread can
        // stop its own clock as soon as it runs out of chunks. The threads
        // still all join at the end of the parallel region.
        #pragma omp for schedule(dynamic, 1000) nowait
        for (uint64_t i = 3 + (2 * rank); i < n; i += (2 * size)) {
            if (is_prime(i)) {
                if (local_cnt >= local_cap) {
                    local_cap *= 2;
                    uint64_t *bigger = realloc(local_buf, local_cap * sizeof(uint64_t));
                    if (!bigger) {
                        // abort(), not MPI_Abort: this is a worker thread, and
                        // under FUNNELED only the main thread may call MPI.
                        fprintf(stderr, "Rank %d thread %d ran out of memory\n", rank, tid);
                        abort();
                    }
                    local_buf = bigger;
                    thread_buffers[tid] = local_buf;
                }
                local_buf[local_cnt++] = i;
            }
        }

        thread_times[tid] = omp_get_wtime() - thread_start;
        thread_counts[tid] = local_cnt;
    }

    // Merge the thread buffers into one array for this process, with 2 put
    // first on rank 0, ready for the gather.
    size_t rank_total = 0;
    if (rank == 0 && n > 2) rank_total += 1;
    for (int t = 0; t < max_threads; t++) {
        rank_total += thread_counts[t];
    }

    uint64_t *rank_primes = malloc((rank_total > 0 ? rank_total : 1) * sizeof(uint64_t));
    if (!rank_primes) fail("could not allocate the merged prime array", rank);
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

    // Put this process's timings in one row: its search time first, then one
    // time per thread. Processes could be started with different thread
    // counts, so all ranks first agree on the largest count and pad the spare
    // slots with -1. Then one MPI_Gather brings every row to the root.
    int widest = 0;
    MPI_Allreduce(&max_threads, &widest, 1, MPI_INT, MPI_MAX, MPI_COMM_WORLD);
    int row_len = widest + 1;
    double *my_row = malloc(row_len * sizeof(double));
    if (!my_row) fail("could not allocate the timing row", rank);
    my_row[0] = comp_end - comp_start;
    for (int t = 0; t < widest; t++) {
        my_row[t + 1] = (t < max_threads) ? thread_times[t] : -1.0;
    }
    free(thread_times);

    // Counts go up first so the root can work out where each process's block
    // belongs, same two stage gather as task1.c.
    int *recv_counts = NULL;
    int *displacements = NULL;
    int rank_cnt_int = (int)rank_total;

    if (rank == 0) {
        recv_counts = malloc(size * sizeof(int));
        if (!recv_counts) fail("could not allocate the count array", rank);
    }

    MPI_Gather(&rank_cnt_int, 1, MPI_INT, recv_counts, 1, MPI_INT, 0, MPI_COMM_WORLD);

    uint64_t *all_primes = NULL;
    int total_primes = 0;

    if (rank == 0) {
        displacements = malloc(size * sizeof(int));
        if (!displacements) fail("could not allocate the displacement array", rank);
        displacements[0] = 0;
        total_primes += recv_counts[0];

        for (int i = 1; i < size; i++) {
            displacements[i] = displacements[i - 1] + recv_counts[i - 1];
            total_primes += recv_counts[i];
        }

        all_primes = malloc((total_primes > 0 ? total_primes : 1) * sizeof(uint64_t));
        if (!all_primes) fail("could not allocate the result array", rank);
    }

    MPI_Gatherv(rank_primes, rank_cnt_int, MPI_UNSIGNED_LONG_LONG,
                all_primes, recv_counts, displacements, MPI_UNSIGNED_LONG_LONG,
                0, MPI_COMM_WORLD);

    double *all_rows = NULL;
    if (rank == 0) {
        all_rows = malloc((size_t)size * row_len * sizeof(double));
        if (!all_rows) fail("could not allocate the timing table", rank);
    }
    MPI_Gather(my_row, row_len, MPI_DOUBLE, all_rows, row_len, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    free(my_row);

    // The root's main thread sorts and writes. The primes arrive interleaved
    // because of the stride, so the qsort is not optional.
    if (rank == 0) {
        qsort(all_primes, total_primes, sizeof(uint64_t), compare_uint64);

        FILE *fout = fopen("primes_task2.txt", "w");
        if (!fout) fail("could not open primes_task2.txt for writing", rank);
        for (int i = 0; i < total_primes; i++) {
            fprintf(fout, "%llu\n", (unsigned long long)all_primes[i]);
        }
        fclose(fout);

        end_time = MPI_Wtime();

        // The slowest process sets the computation time, because everyone
        // waits for it at the gather. The thread times show how evenly OpenMP
        // shared the work inside each process.
        double slowest_rank = 0.0, slowest_thread = 0.0, thread_sum = 0.0;
        int thread_total = 0;
        for (int r = 0; r < size; r++) {
            double *row = all_rows + (size_t)r * row_len;
            if (row[0] > slowest_rank) slowest_rank = row[0];
            for (int t = 1; t < row_len; t++) {
                if (row[t] < 0.0) continue;
                if (row[t] > slowest_thread) slowest_thread = row[t];
                thread_sum += row[t];
                thread_total++;
            }
        }

        printf("Task 2 (Hybrid Open MPI + OpenMP) Summary:\n");
        printf("  Input n: %llu\n", (unsigned long long)n);
        printf("  MPI Processes: %d | OMP Threads per Process: %d\n", size, max_threads);
        printf("  Total Primes Found: %d\n", total_primes);
        printf("  Computation Time: %.4f seconds (slowest process)\n", slowest_rank);
        printf("  Total Wall Clock Time: %.4f seconds\n", end_time - start_time);
        printf("  Search time per thread, in seconds:\n");
        for (int r = 0; r < size; r++) {
            double *row = all_rows + (size_t)r * row_len;
            printf("    rank %3d, %9d primes:", r, recv_counts[r]);
            for (int t = 1; t < row_len; t++) {
                if (row[t] >= 0.0) printf(" %.4f", row[t]);
            }
            printf("\n");
        }
        if (thread_total > 0 && thread_sum > 0.0) {
            // 1.00 means every thread did the same amount of work.
            printf("  Slowest thread / average thread: %.2f\n",
                   slowest_thread / (thread_sum / thread_total));
        }

        free(recv_counts);
        free(displacements);
        free(all_primes);
        free(all_rows);
    }

    free(rank_primes);
    MPI_Finalize();
    return 0;
}
