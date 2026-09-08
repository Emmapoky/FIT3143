/* Activity 2 (version 2) - distribute a terminal integer with MPI_Bcast.
 * Same behaviour as activity2_sendrecv.c but one collective call replaces the
 * send/recv pairs; rank 0 is the broadcast root. */
#include <stdio.h>
#include <mpi.h>

int main(int argc, char *argv[])
{
    int my_rank, value;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);

    do {
        if (my_rank == 0) {
            printf("Enter an integer (negative to quit): ");
            fflush(stdout);
            scanf("%d", &value);
        }
        MPI_Bcast(&value, 1, MPI_INT, 0, MPI_COMM_WORLD);
        printf("Rank: %d. Received value: %d\n", my_rank, value);
        fflush(stdout);
    } while (value >= 0);

    MPI_Finalize();
    return 0;
}
