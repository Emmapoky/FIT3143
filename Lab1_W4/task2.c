////////////////////////////////////////////////////////////////////////////
// task2.c
// -------------------------------------------------------------------------
// FIT3143 Lab #1 Task 2: Prime number search using POSIX Threads.
//
// Same search as task1.c but the work is shared between threads. The thread
// count is read from the command line so we can test different numbers of
// threads for the graphs.
//
// Written by: Taabish Farooq Bhat (35473932)
//
// Compile: gcc task2.c -o task2 -lm -lpthread
// Run:     ./task2 <n> <threads>
////////////////////////////////////////////////////////////////////////////
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <pthread.h>
#include <time.h>

#define STDOUT_LIMIT 100
#define MAX_THREADS  64
#define CHUNK        1000	// how many numbers a thread takes at a time

// Global variables so every thread can reach them, same idea as the vector
// cell product example from the Week 3 lab prep
long  g_n = 0;
int   g_numThreads = 1;
char *g_pFlags = NULL;

// Function prototypes
void *ThreadFunc(void *pArg);
int IsPrime(long k);
void WriteToFile(char *pFilename, char *pFlags, long inN, long inCount);

int main(int argc, char **argv)
{
	long k;
	long count = 0;
	int i = 0;
	pthread_t tid[MAX_THREADS];		// Stores the POSIX thread IDs
	int threadNum[MAX_THREADS];		// Pass a unique thread ID
	struct timespec start, end;
	double time_taken;

	if(argc < 3)
	{
		printf("Usage: %s <n> <threads>\n", argv[0]);
		return 0;
	}

	g_n = atol(argv[1]);
	g_numThreads = atoi(argv[2]);

	if(g_n < 2)
	{
		printf("There are no primes below %ld\n", g_n);
		return 0;
	}
	if(g_numThreads < 1 || g_numThreads > MAX_THREADS)
	{
		printf("Error: threads must be between 1 and %d\n", MAX_THREADS);
		return 0;
	}

	printf("Parallel prime search with POSIX Threads\n\n");
	printf("Commence search up to %ld using %d threads\n", g_n, g_numThreads);

	// Get current clock time.
	clock_gettime(CLOCK_MONOTONIC, &start);

	g_pFlags = (char*)calloc(g_n, sizeof(char));	// Heap array
	if(g_pFlags == NULL)
	{
		printf("Error: Cannot allocate memory\n");
		return 0;
	}

	// Fork
	for(i = 0; i < g_numThreads; i++)
	{
		threadNum[i] = i;
		pthread_create(&tid[i], 0, ThreadFunc, &threadNum[i]);	// &i
	}

	// Join
	for(i = 0; i < g_numThreads; i++)
	{
		pthread_join(tid[i], NULL);
	}
	// All threads have safely been terminated

	// Get the clock current time again
	// Subtract end from start to get the CPU time used.
	clock_gettime(CLOCK_MONOTONIC, &end);
	time_taken = (end.tv_sec - start.tv_sec) * 1e9;
	time_taken = (time_taken + (end.tv_nsec - start.tv_nsec)) * 1e-9;

	printf("Search complete\n");

	// Count and output. The flag array is already in order so we do not need to
	// sort anything or merge separate lists together.
	for(k = 2; k < g_n; k++)
	{
		if(g_pFlags[k])
			count++;
	}

	if(g_n <= STDOUT_LIMIT)
	{
		for(k = 2; k < g_n; k++)
		{
			if(g_pFlags[k])
				printf("%ld ", k);
		}
		printf("\n");
	}
	else
	{
		printf("Commence Writing\n");
		WriteToFile("primes_pthread.txt", g_pFlags, g_n, count);
		printf("Write complete\n");
	}

	printf("n: %ld. Threads: %d. Primes found: %ld\n", g_n, g_numThreads, count);
	printf("Computational time only(s): %lf\n", time_taken);

	free(g_pFlags);
	return 0;
}

// Function definition
//
// Our workload distribution scheme.
//
// The vector cell product example in the Week 3 lab prep gave each thread one
// big block, using sp for the start point and ep for the end point. We tried
// that first here and it did not speed things up nearly as much as we expected.
// The reason is that our work is not the same size for every number. IsPrime
// checks divisors up to the square root of k, so a big number takes more
// divisions than a small one. If thread 0 gets the small half and the last
// thread gets the big half, the last thread is still going long after the
// others have finished, and the whole program has to wait for it at the join.
//
// So instead of one block each, we hand out small blocks of CHUNK numbers in
// turn. Thread 0 takes the first chunk, thread 1 the next, and so on, then it
// wraps back around. Every thread ends up with a mix of small and big numbers,
// so they all finish at about the same time.
//
// We compared both versions and put the numbers in the slides. Compiling with
// -DUSE_BLOCK builds the first attempt so the comparison can be repeated.
void *ThreadFunc(void *pArg)
{
	int my_rank = *((int*)pArg);
	long k;

#ifdef USE_BLOCK
	// First attempt: one block per thread, like the vector cell product example
	long npt  = g_n / g_numThreads;		// npt = numbers per thread
	long nptr = g_n % g_numThreads;		// nptr = numbers per thread remainder
	long sp = my_rank * npt;		// start point
	long ep = sp + npt;			// end point
	if(my_rank == g_numThreads - 1)
		ep += nptr;			// last thread picks up the remainder

	if(sp < 2)
		sp = 2;				// 0 and 1 are not primes so skip them

	for(k = sp; k < ep; k++)
	{
		if(IsPrime(k))
			g_pFlags[k] = 1;
	}
#else
	// Final version: take a chunk, skip the chunks belonging to the other
	// threads, take the next one, and keep going until we run off the end
	long chunkIndex;
	long sp, ep;

	for(chunkIndex = my_rank; ; chunkIndex += g_numThreads)
	{
		sp = 2 + (chunkIndex * CHUNK);	// start point of this chunk
		if(sp >= g_n)
			break;			// nothing left for this thread to do

		ep = sp + CHUNK;		// end point of this chunk
		if(ep > g_n)
			ep = g_n;		// last chunk may be a short one

		for(k = sp; k < ep; k++)
		{
			if(IsPrime(k))
				g_pFlags[k] = 1;
		}
	}
#endif

	// Each thread only ever writes to the positions it was given, so no two
	// threads touch the same element. That means there is no race condition
	// here and we do not need a mutex around this loop.

	return NULL;
}

// Function definition
// Exactly the same test as task1.c so the comparison is fair
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
