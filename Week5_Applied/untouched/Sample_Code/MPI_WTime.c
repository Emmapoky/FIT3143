#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <mpi.h>

int main(int argc, char* argv[])
{
	int my_rank;
	int p;
	//struct timespec start, end;
	//double time_taken;
	double start, end, time_taken; 

	MPI_Init(&argc, &argv);
	MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
	MPI_Comm_size(MPI_COMM_WORLD, &p);
	
	// Get current clock time.
	//clock_gettime(CLOCK_MONOTONIC, &start); 
	start = MPI_Wtime();
	
	// Do something 
	sleep(3); // sleep for 3 seconds 
	
	// Get the clock current time again
	// Subtract end from start to get the CPU time used.
	//clock_gettime(CLOCK_MONOTONIC, &end); 
	//time_taken = (end.tv_sec - start.tv_sec) * 1e9; 
    	//time_taken = (time_taken + (end.tv_nsec - start.tv_nsec)) * 1e-9; 
    	
    	end = MPI_Wtime();
    	time_taken = end - start; 

    	printf("Rank: %d. Overall time (s): %lf\n", my_rank, time_taken);
	
	MPI_Finalize();
	return 0;
}


