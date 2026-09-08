/* Applied #1: minimal MPI skeleton of the EV charging WSN simulator.
 *
 * Student Name: Erwyna Soo Wen Xin
 * Student ID: 36555789
 * Student Email: esoo0013@student.monash.edu
 *
 * Layout: ranks 0..(n-1) are charging nodes in a 2-D Cartesian grid,
 * the last rank is the base station (the star overlay).
 *
 * Compile: mpicc wsn_skeleton.c -o wsn_skeleton
 * Run:     mpirun -np 10 ./wsn_skeleton      (9 nodes in a 3x3 grid + 1 base station)
 * If the laptop has fewer than 10 cores: mpirun --oversubscribe -np 10 ./wsn_skeleton
 */

#include <mpi.h>      // MPI_Init, MPI_Send, MPI_Recv, the Cartesian topology calls
#include <stdio.h>    // printf, fprintf
#include <stdlib.h>   // rand_r

#define PORTS_PER_NODE 5
#define THRESHOLD 0.8              /* alert when more than 80% of ports are in use */

/* me: tags are just integer labels stamped on each message. MPI matches a receive
 * to a send by (communicator, source, tag), so tags let one pair of processes
 * exchange several different kinds of message without mixing them up. I picked
 * 100-103 so they are easy to read in the trace; the numbers themselves mean nothing. */
#define MSG_BS_ALERT 100           /* node -> base station: my neighbourhood is saturated */
#define MSG_BS_REDIRECT 101        /* base station -> node: send cars to this node instead */
#define MSG_NEIGHBOUR_QUERY 102    /* node -> adjacent node: how full are you? */
#define MSG_NEIGHBOUR_REPLY 103    /* adjacent node -> node: this is how full I am */

int main(int argc, char **argv) {
    int world_rank, world_size;

    /* me: MPI_Init starts the MPI runtime. Every process runs this same program,
     * top to bottom. The only thing that makes them behave differently is the rank
     * they get back here, which is why the code below branches on rank. */
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);   // my ID, 0 .. world_size-1
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);   // how many processes were launched

    /* me: I map one charging node onto one MPI process, and give the base station its
     * own process. So the total launched with -np is (number of nodes + 1). I made the
     * base station the LAST rank on purpose: that way the charging nodes keep ranks
     * 0..n-1 with no gap, and their ranks line up with grid positions. */
    int n_nodes = world_size - 1;
    int base_station = world_size - 1;

    /* me: the grid has to be square for a clean sqrt(n) x sqrt(n) layout, so I work out
     * the side length by counting up instead of calling sqrt(). That avoids linking the
     * maths library and avoids a float rounding error deciding my grid size. */
    int side = 0;
    while (side * side < n_nodes) side++;
    if (side * side != n_nodes) {
        if (world_rank == 0)      // only rank 0 prints, otherwise every process repeats the error
            fprintf(stderr, "Run with a square grid + 1, e.g. -np 10 (3x3+1)\n");
        MPI_Finalize();
        return 1;
    }

    /* me: MPI_Comm_split is COLLECTIVE, which means every process in MPI_COMM_WORLD has
     * to call it, and they all have to reach it at the same point in the program. If the
     * base station skipped this call the other processes would sit here waiting for it
     * forever. That is why the call sits ABOVE the if/else and not inside one branch.
     * I hit exactly that hang while writing this, which is how I know.
     *
     * me: colour 0 puts all the charging nodes into a new communicator together.
     * MPI_UNDEFINED is the base station saying "I take part in the call but I do not want
     * to be in any of the resulting groups", and it gets MPI_COMM_NULL back. */
    int is_node = (world_rank != base_station);
    MPI_Comm node_world;
    MPI_Comm_split(MPI_COMM_WORLD, is_node ? 0 : MPI_UNDEFINED,
                   world_rank, &node_world);

    if (!is_node) {
        /* BASE STATION 
         * me: the base station is the server in the star overlay. It logs what comes in
         * and answers with a redirect. It is deliberately the only process that keeps a
         * global view; the charging nodes only ever know about themselves and their
         * four neighbours. */
        int alert;
        MPI_Status st;

        for (int i = 0; i < n_nodes; i++) {
            /* me: MPI_ANY_SOURCE means "take the next alert from whoever sends one",
             * rather than forcing a fixed order. Real nodes cross their threshold at
             * unpredictable times, so pinning an order here would be unrealistic and
             * would also stall if the node I named happened to be quiet.
             * me: the sender's real rank still comes back to me inside the status
             * struct as st.MPI_SOURCE, which is how I know who to reply to. */
            MPI_Recv(&alert, 1, MPI_INT, MPI_ANY_SOURCE, MSG_BS_ALERT,
                     MPI_COMM_WORLD, &st);

            printf("[BS] alert from node %d (in-use ports: %d)\n", st.MPI_SOURCE, alert);

            /* me: SIMPLIFICATION. In the full design the base station holds a table of
             * every node's coordinates and free ports, and picks the nearest node that
             * still has a free port using Manhattan distance on the grid coordinates
             * (|row1-row2| + |col1-col2|), which is the right distance measure because
             * traffic can only travel along grid links, not diagonally.
             * Here I just hand back the next rank so the message path is testable. */
            int redirect_to = (st.MPI_SOURCE + 1) % n_nodes;

            MPI_Send(&redirect_to, 1, MPI_INT, st.MPI_SOURCE, MSG_BS_REDIRECT,
                     MPI_COMM_WORLD);
        }
    } else {
        /* CHARGING NODE */

        /* me: MPI_Cart_create takes the flat list of node ranks and tells MPI to treat
         * them as a 2-D grid. The payoff is the next two lines: I never have to compute
         * "who is above me" with my own index arithmetic, which is where off-by-one bugs
         * come from at the edges.
         
         * me: periods = {0,0} means the grid does NOT wrap around. That matters for
         * realism: a charging station on the edge of the map has no neighbour past the
         * edge, so it should not be talking to a node on the far side of the city.
         * A wrap-around grid would be a torus, and that is not what the spec describes. */
        MPI_Comm grid_comm;
        int dims[2] = { side, side }, periods[2] = { 0, 0 };
        MPI_Cart_create(node_world, 2, dims, periods, 0, &grid_comm);

        /* me: MPI_Cart_shift asks "for a step of +1 along this dimension, who is behind
         * me and who is ahead of me". Dimension 0 is rows, so it gives me up and down.
         * Dimension 1 is columns, so it gives me left and right.
         
         * me: for a node on an edge, the missing neighbour comes back as MPI_PROC_NULL
         * (it prints as -2). Sends and receives to MPI_PROC_NULL are legal and do
         * nothing, so border nodes need no special-case code at all. That is the main
         * reason I used the Cartesian topology instead of computing neighbours myself. */
        int up, down, left, right;
        MPI_Cart_shift(grid_comm, 0, 1, &up, &down);
        MPI_Cart_shift(grid_comm, 1, 1, &left, &right);

        /* me: this stands in for the charging ports. In the full design each node process
         * runs PORTS_PER_NODE POSIX threads, one per port, all writing to a shared
         * in-use array guarded by a mutex. 
    
         * That is the hybrid part of the design:
         * threads share memory INSIDE one machine, MPI passes messages BETWEEN machines.
         * me: rand_r takes its own seed variable rather than using global state, so each
         * process seeds independently and I get a different port count per node instead
         * of every node reporting the same number. */
        unsigned seed = (unsigned)world_rank + 1;
        int ports_in_use = rand_r(&seed) % (PORTS_PER_NODE + 1);

        if ((double)ports_in_use / PORTS_PER_NODE > THRESHOLD) {
            /* me: SIMPLIFICATION, this is where the neighbour round trip goes. The full
             * version posts MSG_NEIGHBOUR_QUERY to up/down/left/right with MPI_Isend and
             * matching MPI_Irecv, collects the four replies, and only escalates to the
             * base station if every neighbour is over the threshold too.
             
             * me: those have to be the non-blocking Isend/Irecv, not plain Send/Recv.
             * Two adjacent nodes can cross the threshold in the same cycle and query each
             * other at the same moment. With blocking calls both would sit waiting for
             * the other to receive first, and that is a deadlock. Non-blocking lets each
             * node answer incoming queries while its own are still in flight. */
        }

        /* me: SIMPLIFICATION, every node alerts once so the message path can be tested
         * end to end. In the real thing an alert only fires after the neighbour check
         * above comes back saturated. */
        MPI_Send(&ports_in_use, 1, MPI_INT, base_station, MSG_BS_ALERT,
                 MPI_COMM_WORLD);

        /* me: plain blocking Send then Recv is safe HERE even though I argued against it
         * above, and I should be able to say why. The deadlock case is a cycle, two
         * processes each waiting on the other. This is not a cycle: it is many nodes
         * sending to one base station, which is looping on receives and replying. Nobody
         * waits on somebody who is waiting on them. */
        int redirect_to;
        MPI_Recv(&redirect_to, 1, MPI_INT, base_station, MSG_BS_REDIRECT,
                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);   // MPI_STATUS_IGNORE: I already know the sender

        printf("[node %d] neighbours u%d d%d l%d r%d, in-use %d/%d, redirect -> node %d\n",
               world_rank, up, down, left, right, ports_in_use, PORTS_PER_NODE, redirect_to);

        /* me: communicators are a resource, so I free the ones I created. Only the node
         * ranks free node_world, because the base station never got a real one back from
         * the split, it got MPI_COMM_NULL, and freeing that is an error. */
        MPI_Comm_free(&grid_comm);
        MPI_Comm_free(&node_world);
    }

    /* me: MPI_Finalize shuts the runtime down. No MPI call is allowed after this. */
    MPI_Finalize();
    return 0;
}