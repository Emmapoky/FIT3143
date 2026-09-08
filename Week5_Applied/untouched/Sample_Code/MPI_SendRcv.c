#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <mpi.h>

// Point to point communication
int main()
{
	int my_rank;
	int p, i;
	//MPI_Status status;

	MPI_Init(NULL, NULL);
	MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
	MPI_Comm_size(MPI_COMM_WORLD, &p);
	
	int val = -1;
	do{
		if(my_rank == 0) // typically rank 0 is classified as root rank
		{
			printf("Enter a round number (>= 0 ): ");
			fflush(stdout);
			scanf("%d", &val);
			for(i = 0; i < p; i++){
				MPI_Send(&val, 1, MPI_INT, i, 0, MPI_COMM_WORLD);
			}
		}
		else
		{
			MPI_Recv(&val, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
			printf("Processors: %d. Received Value: %d\n", my_rank, val);
			fflush(stdout);
		}
		
	}while(val >= 0);

	MPI_Finalize( );
	return 0;
}
