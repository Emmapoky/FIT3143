////////////////////////////////////////////////////////////////////////////
// task1.c
// -------------------------------------------------------------------------
// FIT3143 Lab #1 Task 1: Serial prime number search.
//
// Finds every prime that is strictly less than an integer n given by the user
// and prints them in ascending order. Small n goes to the terminal, large n
// goes to a text file. The program also times itself so we have a baseline to
// compare Task 2 and Task 3 against.
//
// Written by: Erwyna Soo Wen Xin (36555789)
//
// Team:
//   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
//   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
//
// Compile: gcc task1.c -o task1 -lm
// Run:     ./task1 <n>
////////////////////////////////////////////////////////////////////////////
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define STDOUT_LIMIT 100	// n at or below this prints to the terminal instead of a file

// Function prototypes
int IsPrime(long k);
void WriteToFile(char *pFilename, char *pFlags, long inN, long inCount);

int main(int argc, char **argv)
{
	long n;
	long k;
	long count = 0;
	char *pFlags = NULL;	// pFlags[k] is 1 if k is prime, 0 if not
	struct timespec start, end;
	double time_taken;

	if(argc < 2)
	{
		printf("Usage: %s <n>\n", argv[0]);
		return 0;
	}

	n = atol(argv[1]);
	if(n < 2)
	{
		printf("There are no primes below %ld\n", n);
		return 0;
	}

	printf("Serial prime search\n\n");
	printf("Commence search up to %ld\n", n);

	// Get current clock time.
	clock_gettime(CLOCK_MONOTONIC, &start);

	// One byte per candidate. We flag the primes as we find them instead of
	// appending to a list, so the numbers stay in order automatically when we
	// read the array back from the front.
	pFlags = (char*)calloc(n, sizeof(char));	// Heap array
	if(pFlags == NULL)
	{
		printf("Error: Cannot allocate memory\n");
		return 0;
	}

	for(k = 2; k < n; k++)
	{
		if(IsPrime(k))
		{
			pFlags[k] = 1;
			count++;
		}
	}

	// Get the clock current time again
	// Subtract end from start to get the CPU time used.
	// We stop the timer here, before writing the file, because writing is disk
	// work and not part of the calculation we are trying to speed up.
	clock_gettime(CLOCK_MONOTONIC, &end);
	time_taken = (end.tv_sec - start.tv_sec) * 1e9;
	time_taken = (time_taken + (end.tv_nsec - start.tv_nsec)) * 1e-9;

	printf("Search complete\n");

	if(n <= STDOUT_LIMIT)
	{
		// Small n, so just print to the terminal
		for(k = 2; k < n; k++)
		{
			if(pFlags[k])
				printf("%ld ", k);
		}
		printf("\n");
	}
	else
	{
		// Large n, so write to a file instead of flooding the terminal
		printf("Commence Writing\n");
		WriteToFile("primes_serial.txt", pFlags, n, count);
		printf("Write complete\n");
	}

	printf("n: %ld. Threads: 1. Primes found: %ld\n", n, count);
	printf("Computational time only(s): %lf\n", time_taken);

	free(pFlags);
	return 0;
}

// Function definition
// Returns 1 if k is prime and 0 if it is not.
//
// We only test divisors up to the square root of k. If k is not prime then it
// can be written as k = m * p, and m and p cannot both be bigger than the
// square root of k, because then m * p would be bigger than k. So if there is a
// factor at all, one of them has to be at or below the square root. That means
// we can stop there instead of going all the way to k minus 1.
//
// We also deal with 2 on its own so that the loop can skip every even divisor
// and step by 2, which halves the number of divisions again.
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
			return 0;	// found a factor so k is not prime
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

	fprintf(pFile, "%ld\n", inCount);	// first line is how many primes we found

	// Reading the flag array from the front gives us ascending order for free
	for(k = 2; k < inN; k++)
	{
		if(pFlags[k])
			fprintf(pFile, "%ld\n", k);
	}

	fclose(pFile);
}
