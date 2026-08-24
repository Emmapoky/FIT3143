/* Activity 2 (version 1) - distribute a terminal integer with MPI_Send / MPI_Recv.
 * Rank 0 reads an int from the terminal and sends it to every other rank.
 * Every rank prints its rank and the value it received.
 * Loop ends when a negative integer is entered. */
#include <stdio.h>
#include <mpi.h>

int main(int argc, char *argv[])
{
    int my_rank, size, value, i;
    MPI_Status status;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    do {
        if (my_rank == 0) {
            printf("Enter an integer (negative to quit): ");
            fflush(stdout);
            scanf("%d", &value);
            for (i = 1; i < size; i++) {
                MPI_Send(&value, 1, MPI_INT, i, 0, MPI_COMM_WORLD);
            }
        } else {
            MPI_Recv(&value, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, &status);
        }
        printf("Rank: %d. Received value: %d\n", my_rank, value);
        fflush(stdout);
    } while (value >= 0);

    MPI_Finalize();
    return 0;
}
