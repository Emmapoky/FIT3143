////////////////////////////////////////////////////////////////////////////
// serial_instr.c
// -------------------------------------------------------------------------
// FIT3143 Lab #2 Task 3: instrumented copy of Week 4 Lab #1 task1.c.
//
// The Week 4 serial program stops its timer before it writes the file, on
// purpose, because Week 4 only ever compared computation against computation.
// Lab #2 asks for the OVERALL speedup "including communication, computation,
// sorting and file writing", so I need the write time as well, and I need it
// measured the same way as the MPI versions measure theirs.
//
// The search itself is Week 4's, unchanged. All I have added is a second
// timer around WriteToFile and a machine readable output line.
//
// Written by: Erwyna Soo Wen Xin (36555789)
// Original Week 4 serial search by: Erwyna Soo Wen Xin (36555789)
//
// Team:
//   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
//   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
//
// Erwyna: this file is the denominator for every speedup number in the deck,
// so it matters that it is the same code Week 4 was graded on and not a
// tidied up rewrite. Diff it against Lab1_W4/task1.c and the only differences
// are the two clock_gettime calls and the PHASE printf.
//
// Compile: gcc -O2 serial_instr.c -o serial_instr -lm
// Run:     ./serial_instr <n>
////////////////////////////////////////////////////////////////////////////
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

int IsPrime(long k);
void WriteToFile(char *pFilename, char *pFlags, long inN, long inCount);

static double elapsed(struct timespec a, struct timespec b) {
    return (b.tv_sec - a.tv_sec) + (b.tv_nsec - a.tv_nsec) * 1e-9;
}

int main(int argc, char **argv)
{
    long n, k, count = 0;
    char *pFlags = NULL;
    struct timespec t0, t1, t2;

    if (argc < 2) {
        printf("Usage: %s <n>\n", argv[0]);
        return 0;
    }

    n = atol(argv[1]);
    if (n < 2) {
        printf("There are no primes below %ld\n", n);
        return 0;
    }

    clock_gettime(CLOCK_MONOTONIC, &t0);

    pFlags = (char*)calloc(n, sizeof(char));
    if (pFlags == NULL) {
        printf("Error: Cannot allocate memory\n");
        return 0;
    }

    for (k = 2; k < n; k++) {
        if (IsPrime(k)) {
            pFlags[k] = 1;
            count++;
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);   // end of the search, Week 4's stop point

    WriteToFile("primes_serial_instr.txt", pFlags, n, count);

    clock_gettime(CLOCK_MONOTONIC, &t2);   // end of the write

    // PHASE,n,procs,threads,primes,comp,write,total
    printf("PHASE,%ld,1,1,%ld,%.6f,%.6f,%.6f\n",
           n, count, elapsed(t0, t1), elapsed(t1, t2), elapsed(t0, t2));

    free(pFlags);
    return 0;
}

int IsPrime(long k)
{
    long d, limit;

    if (k < 2) return 0;
    if (k == 2) return 1;
    if (k % 2 == 0) return 0;

    limit = (long)sqrt((double)k);

    for (d = 3; d <= limit; d += 2) {
        if (k % d == 0) return 0;
    }
    return 1;
}

void WriteToFile(char *pFilename, char *pFlags, long inN, long inCount)
{
    long k;
    FILE *pFile = fopen(pFilename, "w");
    if (pFile == NULL) {
        printf("Error: Cannot open file\n");
        return;
    }

    fprintf(pFile, "%ld\n", inCount);

    for (k = 2; k < inN; k++) {
        if (pFlags[k])
            fprintf(pFile, "%ld\n", k);
    }

    fclose(pFile);
}
