#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <mpi.h>


int main(int argc, char** argv) // Command line argument
{
	// A pointer to a pointer (i.e., **) is a variable that stores the address of a pointer.

	int my_rank;
	int p;
	char processName[MPI_MAX_PROCESSOR_NAME]; // Stack array
	int length;

	MPI_Init(&argc, &argv); // Initializes the communicator
	MPI_Comm_rank(MPI_COMM_WORLD, &my_rank); // MPI_COMM_WORLD is your default communicator
	MPI_Comm_size(MPI_COMM_WORLD, &p);
	MPI_Get_processor_name(processName, &length); // Optional
	
	printf("Hello there. I am %d of %d. Process Name: %s. Length: %d\n", my_rank, p, processName, length);

	MPI_Finalize( );

	return 0;
}

