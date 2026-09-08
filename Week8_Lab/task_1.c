#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <math.h>
#include <mpi.h>
#include <stdint.h>

/**
 * Optimized primality test using trial division up to sqrt(num).
 * Skips even numbers; checks divisibility by 3 and 6k +/- 1.
 */
static inline bool is_prime(uint64_t num) {
    if (num <= 1) return false;
    if (num <= 3) return true;
    if (num % 2 == 0 || num % 3 == 0) return false;
    
    for (uint64_t i = 5; i * i <= num; i += 6) {
        if (num % i == 0 || num % (i + 2) == 0) return false;
    }
    return true;
}

// Comparator function for qsort
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
    double start_time, comp_start, comp_end, end_time;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    start_time = MPI_Wtime();

    // Rank 0 parses command-line argument
    if (rank == 0) {
        if (argc < 2) {
            fprintf(stderr, "Usage: mpirun -np <procs> %s <n>\n", argv[0]);
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        n = strtoull(argv[1], NULL, 10);
    }

    // Broadcast upper limit 'n' to all processes
    MPI_Bcast(&n, 1, MPI_UNSIGNED_LONG_LONG, 0, MPI_COMM_WORLD);

    // Dynamic array for local prime candidates
    size_t capacity = 1024;
    size_t local_count = 0;
    uint64_t *local_primes = (uint64_t *)malloc(capacity * sizeof(uint64_t));
    if (!local_primes) {
        fprintf(stderr, "Rank %d failed to allocate memory.\n", rank);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    comp_start = MPI_Wtime();

    // Rank 0 handles the prime number 2 if n > 2
    if (rank == 0 && n > 2) {
        local_primes[local_count++] = 2;
    }

    // Cyclic/Stride Partitioning over odd numbers strictly less than n
    // Process 'rank' handles numbers: 3 + 2*(rank + k*size)
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

    comp_end = MPI_Wtime();

    // Gather local counts to Root
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

    // Gather all local prime arrays into root's global array
    MPI_Gatherv(local_primes, local_cnt_int, MPI_UNSIGNED_LONG_LONG,
                all_primes, recv_counts, displacements, MPI_UNSIGNED_LONG_LONG,
                0, MPI_COMM_WORLD);

    // Root process sorts and writes output
    if (rank == 0) {
        qsort(all_primes, total_primes, sizeof(uint64_t), compare_uint64);

        FILE *fout = fopen("primes_task1.txt", "w");
        if (fout) {
            for (int i = 0; i < total_primes; i++) {
                fprintf(fout, "%llu\n", (unsigned long long)all_primes[i]);
            }
            fclose(fout);
        }

        end_time = MPI_Wtime();

        printf("Task 1 (Open MPI) Summary:\n");
        printf("  Input n: %llu\n", (unsigned long long)n);
        printf("  Total Primes Found: %d\n", total_primes);
        printf("  Computation Time: %.4f seconds\n", comp_end - comp_start);
        printf("  Total Wall Clock Time: %.4f seconds\n", end_time - start_time);

        free(recv_counts);
        free(displacements);
        free(all_primes);
    }

    free(local_primes);
    MPI_Finalize();
    return 0;
}