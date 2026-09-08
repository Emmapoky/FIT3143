#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <mpi.h>

#define BUFF_ELEMENTS 10

int main(int argc, char* argv[])
{
	int my_rank;
	int p;

	MPI_Init(&argc, &argv);
	MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
	MPI_Comm_size(MPI_COMM_WORLD, &p);

	int localValue = my_rank + 1;
	printf("Rank: %d. Local Value: %d\n", my_rank, localValue);

	int globalValue = 0;

	// MPI Reduce
	//MPI_Reduce(&localValue, &globalValue, 1, MPI_INT, MPI_SUM, (p-1), MPI_COMM_WORLD);
	
	// Alternative - MPI All Reduce. Comment out MPI_Reduce and uncomment MPI_Allreduce to test this method.
	MPI_Allreduce(&localValue, &globalValue, 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD);

	printf("Rank: %d. Global Value: %d\n", my_rank, globalValue);

	MPI_Finalize();
}
