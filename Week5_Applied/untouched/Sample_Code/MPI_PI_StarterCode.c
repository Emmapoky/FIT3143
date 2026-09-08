#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <mpi.h>

int main(int argc, char* argv[]){

	int i = 0;
	int root = 0; // a variable points to rank number for the root process
	unsigned long N; // Upperlimit for the calculation
	double start, end, time_taken; // Variables for counting execution time
	int start_point, end_point, partition_size, partition_remainder; // Start and end points for the partition
	int my_rank, size; // Process rank and size
	double local_sum = 0.0, global_sum = 0.0, piVal = 0.0; 
	double startOverall, endOverall, time_taken_overall;

	// Initiate MPI computation
	MPI_Init(&argc, &argv);

	// Get the rank number of the process
	MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
	MPI_Comm_size(MPI_COMM_WORLD, &size);

	if(my_rank == root){
		startOverall = MPI_Wtime();
		if(argc < 2){
			printf("Error, insufficient arguments\n");
			MPI_Finalize();
			return 0;
		}
		N =  atoi(argv[1]);
		printf("Rank %d. N: %ld\n", my_rank, N);
		fflush(stdout);
	}

	// To be completed - Broadcast the N to all processes
	// Enter your code here
	
	/* Upon receiving the value N, start the calculation... */
	
	// To be completed - Workload distribution. Allocate computation to each MPI process. Use the variabled declared above.
	// Enter your code here
	
	// To be completed - Aggregate the resuls into the root process. The root process prints the final pi value.
	// Enter your code here
	
	
	MPI_Finalize();

	return 0;
}
