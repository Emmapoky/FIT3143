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
// Team:
//   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
//   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
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

// Taabish: on why 1000 and not something else. There is a trade off both ways.
// Make the chunk too small, say 1, and every thread spends its time on loop
// bookkeeping and the threads keep landing on the same cache lines when they
// write their flags. Make it too big, say a million, and we are back to the
// block version, because one thread ends up holding a long run of expensive
// candidates and finishes late. 1000 is large enough that the bookkeeping is
// nothing next to the actual divisions, and small enough that with 14 threads
// at n = 30 million there are still 30,000 chunks going around, so the work
// evens out. I tried a few sizes and anything from a few hundred to a few
// thousand behaved about the same, so the exact number is not delicate.

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

	// Taabish: threadNum needs to be its own array, one slot per thread.
	// My first version passed &i straight into pthread_create, which looked
	// fine but is a bug: every thread receives a pointer to the same variable,
	// and the loop keeps incrementing it while the threads are starting. Some
	// threads then read the wrong rank and two of them do the same chunks.
	// Giving each thread its own slot means the value cannot change underneath
	// it. That is a data race on i, and it is the one race in this program I
	// had to actually fix.
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
	//
	// Taabish: this is the payoff from Erwyna's flag array in task1.c. If each
	// thread had built its own list I would have to merge and sort them all
	// here, which is serial work that grows with n and would eat into the
	// speedup. Counting after the join instead of during it also means the
	// threads never touch a shared counter, so there is no need for a mutex or
	// an atomic add in the hot loop.
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
// We compared both versions and put the numbers in results_extra.csv. Compiling with
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
	//
	// Taabish: to be exact, threads do share cache lines at the chunk borders,
	// since one cache line covers 64 of these bytes. That is false sharing, so
	// it can cost a little speed, but it is not a correctness problem because
	// the bytes themselves are never written by two threads. Chunks of 1000
	// keep the borders rare enough that it does not show up in the timings.
	//
	// If I did need the threads to update something shared, a running count for
	// instance, then this is where a mutex would go, and it would be a genuine
	// critical section. I avoided that by counting after the join instead.

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
