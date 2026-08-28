/* Applied #1 prep: minimal MPI skeleton of the EV-charging WSN simulator.
 * AI-written prep scaffolding (Claude, 2026-08-25), for understanding the
 * architecture before the applied session. Not a submission. Declare AI use
 * if any of this ends up in submitted work.
 *
 * Layout: ranks 0..(n-1) are charging nodes in a 2-D Cartesian grid
 * (MPI_Cart_create), the last rank is the base station (star overlay).
 *
 * Compile: mpicc wsn_skeleton.c -o wsn_skeleton
 * Run:     mpirun -np 10 ./wsn_skeleton        (9 nodes in a 3x3 grid + 1 base station)
 */
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

#define PORTS_PER_NODE 5
#define THRESHOLD 0.8              /* alert when > 80% of ports in use */

#define MSG_BS_ALERT 100           /* node -> base station: quadrant saturated  */
#define MSG_BS_REDIRECT 101        /* base station -> node: nearest free node   */
#define MSG_NEIGHBOUR_QUERY 102    /* node -> adjacent node: how full are you?  */
#define MSG_NEIGHBOUR_REPLY 103

int main(int argc, char **argv) {
    int world_rank, world_size;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);

    int n_nodes = world_size - 1;                /* last rank is the base station */
    int base_station = world_size - 1;
    int side = 0;
    while (side * side < n_nodes) side++;        /* square grid side, no libm needed */
    if (side * side != n_nodes) {
        if (world_rank == 0)
            fprintf(stderr, "Run with a square grid + 1, e.g. -np 10 (3x3+1)\n");
        MPI_Finalize();
        return 1;
    }

    /* MPI_Comm_split is COLLECTIVE over MPI_COMM_WORLD: every rank calls it
     * here, at the same point, before any point-to-point traffic starts.
     * Colour 0 = charging nodes, MPI_UNDEFINED = base station opts out. */
    int is_node = (world_rank != base_station);
    MPI_Comm node_world;
    MPI_Comm_split(MPI_COMM_WORLD, is_node ? 0 : MPI_UNDEFINED,
                   world_rank, &node_world);

    if (!is_node) {
        /* ---- base station: log alerts, reply with a redirect target ---- */
        int alert;
        MPI_Status st;
        for (int i = 0; i < n_nodes; i++) {      /* toy loop: one alert per node */
            MPI_Recv(&alert, 1, MPI_INT, MPI_ANY_SOURCE, MSG_BS_ALERT,
                     MPI_COMM_WORLD, &st);
            printf("[BS] alert from node %d (in-use ports: %d)\n", st.MPI_SOURCE, alert);
            int redirect_to = (st.MPI_SOURCE + 1) % n_nodes; /* placeholder: real code
                                                                searches nearest free node */
            MPI_Send(&redirect_to, 1, MPI_INT, st.MPI_SOURCE, MSG_BS_REDIRECT,
                     MPI_COMM_WORLD);
        }
    } else {
        /* ---- charging node: join the 2-D Cartesian grid of node ranks ---- */
        MPI_Comm grid_comm;
        int dims[2] = { side, side }, periods[2] = { 0, 0 };
        MPI_Cart_create(node_world, 2, dims, periods, 0, &grid_comm);

        int up, down, left, right;
        MPI_Cart_shift(grid_comm, 0, 1, &up, &down);     /* neighbours found for us */
        MPI_Cart_shift(grid_comm, 1, 1, &left, &right);

        /* Port state: in the full design this array is updated by PORTS_PER_NODE
         * threads (Pthreads/OpenMP) sharing memory inside this process. */
        unsigned seed = (unsigned)world_rank + 1;
        int ports_in_use = rand_r(&seed) % (PORTS_PER_NODE + 1);

        if ((double)ports_in_use / PORTS_PER_NODE > THRESHOLD) {
            /* full design: MPI_Isend MSG_NEIGHBOUR_QUERY to up/down/left/right,
             * gather replies, and only alert the BS if the whole quadrant is full */
        }
        MPI_Send(&ports_in_use, 1, MPI_INT, base_station, MSG_BS_ALERT,
                 MPI_COMM_WORLD);                 /* toy: every node alerts once */
        int redirect_to;
        MPI_Recv(&redirect_to, 1, MPI_INT, base_station, MSG_BS_REDIRECT,
                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        printf("[node %d] neighbours u%d d%d l%d r%d, in-use %d/%d, redirect -> node %d\n",
               world_rank, up, down, left, right, ports_in_use, PORTS_PER_NODE, redirect_to);
        MPI_Comm_free(&grid_comm);
        MPI_Comm_free(&node_world);
    }

    MPI_Finalize();
    return 0;
}
