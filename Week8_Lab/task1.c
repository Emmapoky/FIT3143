////////////////////////////////////////////////////////////////////////////
// task1.c
// -------------------------------------------------------------------------
// FIT3143 Lab #2 Task 1: prime search with Open MPI.
//
// Finds every prime strictly below n and writes them in ascending order to
// primes_task1.txt, one per line.
//
// How it runs:
//   1. Rank 0 reads n from the command line and broadcasts it.
//   2. Every rank works out its own share of the odd numbers from its rank
//      and the process count (the cyclic stride in main), so no work has to
//      be sent out.
//   3. Every rank searches its share, keeps its primes in its own buffer and
//      times its own search.
//   4. The root gathers the counts, then all the primes with one MPI_Gatherv,
//      then every rank's search time.
//   5. The root sorts, writes the file and prints a summary that includes
//      each rank's search time, so any imbalance shows up straight away.
//
// Written by: Taabish Farooq Bhat (35473932)
//
// Team:
//   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
//   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
//
// Compile: mpicc -O2 task1.c -o task1
// Run:     mpirun -np <procs> ./task1 <n>
////////////////////////////////////////////////////////////////////////////
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <mpi.h>

// is_prime
// Returns true if num is prime.
// Trial division, but only up to sqrt(num): if num = a * b then a and b can't
// both be bigger than sqrt(num), so any factor above it has a partner below
// it. Every prime above 3 is 6k - 1 or 6k + 1, so after ruling out 2 and 3 I
// only try i and i + 2 for i = 5, 11, 17, ... and never waste a division on a
// multiple of 2 or 3.
static inline bool is_prime(uint64_t num) {
    if (num <= 1) return false;
    if (num <= 3) return true;                      // 2 and 3
    if (num % 2 == 0 || num % 3 == 0) return false;

    for (uint64_t i = 5; i * i <= num; i += 6) {    // i * i instead of sqrt()
        if (num % i == 0 || num % (i + 2) == 0) return false;
    }
    return true;
}

// compare_uint64
// qsort comparator for uint64_t. Compares instead of subtracting, because
// a - b on unsigned 64 bit numbers wraps around and gives the wrong sign.
static int compare_uint64(const void *a, const void *b) {
    uint64_t arg1 = *(const uint64_t *)a;
    uint64_t arg2 = *(const uint64_t *)b;
    if (arg1 < arg2) return -1;
    if (arg1 > arg2) return 1;
    return 0;
}

// fail
// Prints what went wrong and stops every rank, not just this one.
static void fail(const char *msg, int rank) {
    fprintf(stderr, "Rank %d: %s\n", rank, msg);
    MPI_Abort(MPI_COMM_WORLD, 1);
}

int main(int argc, char *argv[]) {
    int rank, size;
    uint64_t n = 0;
    // start/end bracket the whole run, comp_start/comp_end just this rank's
    // search, so we can see what the sort and the write are costing.
    double start_time, comp_start, comp_end, end_time;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    start_time = MPI_Wtime();

    // Only the root reads n. It has to be a plain whole number, so something
    // like "-5" or "10abc" gets rejected before it is sent anywhere.
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

    // Every rank needs n to work out its own share.
    MPI_Bcast(&n, 1, MPI_UNSIGNED_LONG_LONG, 0, MPI_COMM_WORLD);

    // Growable buffer for the primes this rank finds. It doubles when it
    // fills, since there's no way to know the count up front without doing
    // the search twice.
    size_t capacity = 1024;
    size_t local_count = 0;
    uint64_t *local_primes = malloc(capacity * sizeof(uint64_t));
    if (!local_primes) fail("could not allocate the prime buffer", rank);

    comp_start = MPI_Wtime();

    // 2 is the only even prime and the stride below only walks odd numbers,
    // so rank 0 adds it by hand.
    if (rank == 0 && n > 2) {
        local_primes[local_count++] = 2;
    }

    // Cyclic stride over the odd numbers below n. Rank r starts at 3 + 2r and
    // jumps by 2p, so the ranks interleave. With p = 4, rank 0 gets 3, 11,
    // 19, ... and rank 1 gets 5, 13, 21, ... and so on.
    //
    // Taabish: went cyclic instead of block because is_prime gets slower the
    // bigger the number. Split it into blocks and the last rank is stuck with
    // all the expensive ones while everyone else sits waiting.
    //
    // Known limit, found in our Task 3 measurements: if p has an odd factor d,
    // one rank in every d only ever gets multiples of d, which is_prime throws
    // out straight away, so that rank does almost nothing. Powers of two split
    // evenly. The per rank times printed at the end make this easy to see.
    uint64_t start_val = 3 + (2 * rank);
    uint64_t step = 2 * size;

    for (uint64_t i = start_val; i < n; i += step) {
        if (is_prime(i)) {
            if (local_count >= capacity) {
                capacity *= 2;
                uint64_t *bigger = realloc(local_primes, capacity * sizeof(uint64_t));
                if (!bigger) fail("ran out of memory growing the prime buffer", rank);
                local_primes = bigger;
            }
            local_primes[local_count++] = i;
        }
    }

    comp_end = MPI_Wtime();
    double my_search_time = comp_end - comp_start;

    // Counts first, so the root knows how big each rank's block is before it
    // tries to receive anything.
    int *recv_counts = NULL;
    int *displacements = NULL;
    int local_cnt_int = (int)local_count;

    if (rank == 0) {
        recv_counts = malloc(size * sizeof(int));
        if (!recv_counts) fail("could not allocate the count array", rank);
    }

    MPI_Gather(&local_cnt_int, 1, MPI_INT, recv_counts, 1, MPI_INT, 0, MPI_COMM_WORLD);

    uint64_t *all_primes = NULL;
    int total_primes = 0;

    if (rank == 0) {
        // Each rank's block starts where the previous one ended, so the
        // offsets are just a running total of the counts.
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

    // Taabish: Gatherv rather than Gather because the ranks find different
    // numbers of primes, so the blocks are uneven. The displacement array is
    // what tells it where each one lands.
    MPI_Gatherv(local_primes, local_cnt_int, MPI_UNSIGNED_LONG_LONG,
                all_primes, recv_counts, displacements, MPI_UNSIGNED_LONG_LONG,
                0, MPI_COMM_WORLD);

    // One more small gather, one double per rank: how long each rank's
    // search took, so the root can show how evenly the work was split.
    double *rank_times = NULL;
    if (rank == 0) {
        rank_times = malloc(size * sizeof(double));
        if (!rank_times) fail("could not allocate the timing array", rank);
    }
    MPI_Gather(&my_search_time, 1, MPI_DOUBLE, rank_times, 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    // The cyclic split means the primes arrive interleaved, not sorted, so
    // the root has to qsort before writing.
    if (rank == 0) {
        qsort(all_primes, total_primes, sizeof(uint64_t), compare_uint64);

        FILE *fout = fopen("primes_task1.txt", "w");
        if (!fout) fail("could not open primes_task1.txt for writing", rank);
        for (int i = 0; i < total_primes; i++) {
            fprintf(fout, "%llu\n", (unsigned long long)all_primes[i]);
        }
        fclose(fout);

        // Stopped after the write, so this covers everything the user waits
        // for apart from mpirun starting up.
        end_time = MPI_Wtime();

        // Everyone waits at the gather for the slowest rank, so its search
        // time is the computation time worth reporting.
        double slowest = 0.0, total_search = 0.0;
        for (int r = 0; r < size; r++) {
            if (rank_times[r] > slowest) slowest = rank_times[r];
            total_search += rank_times[r];
        }

        printf("Task 1 (Open MPI) Summary:\n");
        printf("  Input n: %llu\n", (unsigned long long)n);
        printf("  MPI Processes: %d\n", size);
        printf("  Total Primes Found: %d\n", total_primes);
        printf("  Computation Time: %.4f seconds (slowest rank)\n", slowest);
        printf("  Total Wall Clock Time: %.4f seconds\n", end_time - start_time);
        printf("  Search time per rank:\n");
        for (int r = 0; r < size; r++) {
            printf("    rank %3d: %8.4f s  %9d primes\n", r, rank_times[r], recv_counts[r]);
        }
        if (total_search > 0.0) {
            // 1.00 means every rank did the same amount of work.
            printf("  Slowest rank / average rank: %.2f\n", slowest / (total_search / size));
        }

        free(recv_counts);
        free(displacements);
        free(all_primes);
        free(rank_times);
    }

    free(local_primes);
    MPI_Finalize();
    return 0;
}
