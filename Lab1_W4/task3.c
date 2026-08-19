////////////////////////////////////////////////////////////////////////////
// task3.c
// -------------------------------------------------------------------------
// FIT3143 Lab #1 Task 3: Prime number search using OpenMP.
//
// Same search again, but this time the loop is shared out by OpenMP instead of
// by threads we create ourselves.
//
// Written by: Taabish Farooq Bhat (35473932)
//
// Team:
//   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
//   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
//
// Compile: gcc task3.c -o task3 -lm -fopenmp
// Run:     ./task3 <n> <threads>
//
// Note: if you forget the -fopenmp flag the pragmas are ignored and the program
// still compiles and runs, it just runs on one thread. We got caught by this
// early on when our speedup came out as exactly 1.
////////////////////////////////////////////////////////////////////////////
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <omp.h>
#include <time.h>

#define STDOUT_LIMIT 100
#define CHUNK        1000	// same chunk size we settled on in task2.c

// Function prototypes
int IsPrime(long k);
void WriteToFile(char *pFilename, char *pFlags, long inN, long inCount);

int main(int argc, char **argv)
{
	long n;
	long k;
	long count = 0;
	char *pFlags = NULL;
	struct timespec start, end;
	double time_taken;

	if(argc < 2)
	{
		printf("Usage: %s <n> [threads]\n", argv[0]);
		return 0;
	}

	n = atol(argv[1]);
	if(n < 2)
	{
		printf("There are no primes below %ld\n", n);
		return 0;
	}

	// If a thread count is given we set it here, otherwise OpenMP picks the
	// default for the machine, which is usually the number of cores
	if(argc >= 3)
		omp_set_num_threads(atoi(argv[2]));

	printf("Parallel prime search with OpenMP\n\n");
	printf("Commence search up to %ld using %d threads\n", n, omp_get_max_threads());

	// Get current clock time.
	clock_gettime(CLOCK_MONOTONIC, &start);

	pFlags = (char*)calloc(n, sizeof(char));	// Heap array
	if(pFlags == NULL)
	{
		printf("Error: Cannot allocate memory\n");
		return 0;
	}

	// Our workload distribution scheme.
	//
	// In task2.c we had to write the sharing out ourselves. Here the for
	// pragma does it for us, and the schedule clause decides how.
	//
	// We used schedule(dynamic, CHUNK) for the same reason we used chunks in
	// task2.c. Checking a big number takes longer than checking a small one
	// because IsPrime goes up to the square root, so the work is not spread
	// evenly across the loop. With schedule(static) the blocks are decided
	// before the loop starts and the thread holding the biggest numbers ends up
	// finishing last while the others sit idle. With dynamic, a thread comes
	// back for another chunk as soon as it finishes one, so the slow parts get
	// shared out as the loop runs.
	//
	// We did time all three at n = 30,000,000 with 14 threads. Dynamic came
	// out about 9 percent faster than static (10.44x against 9.55x speedup),
	// with guided in between (10.42x). That matches the reasoning above: with
	// this many threads an unlucky static split leaves whole cores idle near
	// the end of the loop, and dynamic fills them with the remaining chunks.
	// The timings are in results_extra.csv.
	//
	// Like in task2.c each element of pFlags is only written by one thread, so
	// there is no race and we do not need a critical section here.
	#pragma omp parallel for schedule(dynamic, CHUNK)
	for(k = 2; k < n; k++)
	{
		if(IsPrime(k))
			pFlags[k] = 1;
	}

	// Get the clock current time again
	// Subtract end from start to get the CPU time used.
	clock_gettime(CLOCK_MONOTONIC, &end);
	time_taken = (end.tv_sec - start.tv_sec) * 1e9;
	time_taken = (time_taken + (end.tv_nsec - start.tv_nsec)) * 1e-9;

	printf("Search complete\n");

	for(k = 2; k < n; k++)
	{
		if(pFlags[k])
			count++;
	}

	if(n <= STDOUT_LIMIT)
	{
		for(k = 2; k < n; k++)
		{
			if(pFlags[k])
				printf("%ld ", k);
		}
		printf("\n");
	}
	else
	{
		printf("Commence Writing\n");
		WriteToFile("primes_omp.txt", pFlags, n, count);
		printf("Write complete\n");
	}

	printf("n: %ld. Threads: %d. Primes found: %ld\n", n, omp_get_max_threads(), count);
	printf("Computational time only(s): %lf\n", time_taken);

	free(pFlags);
	return 0;
}

// Function definition
// Exactly the same test as task1.c and task2.c so the comparison is fair
int IsPrime(long k)
{
	long d;
	long limit;

	if(k < 2)
		return 0;
	if(k == 2)
		return 1;
	if(k % 2 == 0)
		return 0;

	limit = (long)sqrt((double)k);

	for(d = 3; d <= limit; d += 2)
	{
		if(k % d == 0)
			return 0;
	}

	return 1;
}

// Function definition
void WriteToFile(char *pFilename, char *pFlags, long inN, long inCount)
{
	long k;
	FILE *pFile = fopen(pFilename, "w");
	if(pFile == NULL)
	{
		printf("Error: Cannot open file\n");
		return;
	}

	fprintf(pFile, "%ld\n", inCount);

	for(k = 2; k < inN; k++)
	{
		if(pFlags[k])
			fprintf(pFile, "%ld\n", k);
	}

	fclose(pFile);
}
