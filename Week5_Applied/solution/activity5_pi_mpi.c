/* Activity 5 - parallel Pi approximation with MPI_Bcast + MPI_Reduce.
 * Based on MPI_PI_StarterCode.c; only the three "To be completed" blocks are
 * filled in (broadcast of N, workload distribution, aggregation at root).
 * Run: mpirun -np 4 ./activity5_pi_mpi 100000000 */
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
	MPI_Bcast(&N, 1, MPI_UNSIGNED_LONG, root, MPI_COMM_WORLD);

	/* Upon receiving the value N, start the calculation... */

	// To be completed - Workload distribution. Allocate computation to each MPI process. Use the variabled declared above.
	start = MPI_Wtime();
	partition_size = (int)(N / (unsigned long)size);
	partition_remainder = (int)(N % (unsigned long)size);
	if(my_rank < partition_remainder){
		// the first 'partition_remainder' ranks take one extra iteration each
		start_point = my_rank * (partition_size + 1);
		end_point = start_point + partition_size + 1;
	}else{
		start_point = my_rank * partition_size + partition_remainder;
		end_point = start_point + partition_size;
	}
	for(i = start_point; i < end_point; i++){
		local_sum += 4.0 / (1 + pow((2.0 * i + 1.0)/(2.0 * N), 2));
	}
	end = MPI_Wtime();
	time_taken = end - start;

	// To be completed - Aggregate the resuls into the root process. The root process prints the final pi value.
	MPI_Reduce(&local_sum, &global_sum, 1, MPI_DOUBLE, MPI_SUM, root, MPI_COMM_WORLD);
	if(my_rank == root){
		piVal = global_sum / (double)N;
		printf("Calculated Pi value (Parallel-MPI) = %12.9f\n", piVal);
		printf("Compute time on rank %d (s): %lf\n", my_rank, time_taken);
		endOverall = MPI_Wtime();
		time_taken_overall = endOverall - startOverall;
		printf("Overall time (s): %lf\n", time_taken_overall);
	}

	MPI_Finalize();

	return 0;
}
