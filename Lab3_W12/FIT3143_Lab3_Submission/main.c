////////////////////////////////////////////////////////////////////////////
// main.c
// -------------------------------------------------------------------------
// FIT3143 Lab #3: distributed wireless sensor network (WSN) of EV charging
// nodes, simulated with Open MPI (between nodes) and OpenMP (between the
// charging ports inside one node).
//
// How it runs:
//   1. Every rank parses the same argv (rows, cols and the options).
//   2. MPI_Comm_split puts ranks 0 .. rows*cols-1 (the charging nodes) into
//      their own communicator. The last rank is the base station and sits
//      out of it, same layout as the Week 12 virtual topology example.
//   3. The nodes turn that communicator into a rows x cols, non periodic
//      Cartesian grid with MPI_Cart_create. rows = 1 gives the line topology
//      we need for Task 3b, with no extra code.
//   4. Each rank runs its role: run_charging_node (node.c, Task 1) or
//      run_base_station (base_station.c, Task 2).
//   5. After the two phase shutdown every rank hands its timing array to
//      the base station with one MPI_Gather, the base station writes the
//      summary, and every rank frees what it made and calls MPI_Finalize.
//
// Written by: Taabish Farooq Bhat (35473932)
//
// Team:
//   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
//   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
//
// Compile: make            (or see the Makefile for the plain mpicc line)
// Run:     mpirun -np <rows*cols+1> ./wsn <rows> <cols> [options]
//          e.g. mpirun -np 10 ./wsn 3 3        (3x3 grid + base station)
////////////////////////////////////////////////////////////////////////////
#include "wsn.h"
#include <stdlib.h>

int main(int argc, char **argv) {
    int provided, world_rank, world_size;

    // Taabish: FUNNELED, not MULTIPLE. Inside a node the OpenMP port threads
    // never touch MPI, only the master thread (thread 0) does, so FUNNELED
    // is all we need and it avoids the locking MULTIPLE adds to every call.
    MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provided);
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);
    if (provided < MPI_THREAD_FUNNELED) {
        if (world_rank == 0) fprintf(stderr, "MPI library cannot give MPI_THREAD_FUNNELED\n");
        MPI_Finalize();
        return 1;
    }

    Config cfg;
    if (!parse_config(argc, argv, &cfg, world_size, world_rank)) {
        // every rank reaches the same verdict from the same argv, so they
        // all leave here together and nobody hangs in a collective later
        MPI_Finalize();
        return 1;
    }

    int bs_rank = world_size - 1;            // base station is the LAST rank
    int n_nodes = world_size - 1;
    int is_node = (world_rank != bs_rank);

    // Taabish: MPI_Comm_split is collective over MPI_COMM_WORLD, so the base
    // station has to call it too even though it wants no part of the grid.
    // MPI_UNDEFINED hands it MPI_COMM_NULL back. Key = world rank keeps the
    // node ranks in the same order inside the new communicator.
    MPI_Comm node_comm, grid_comm = MPI_COMM_NULL;
    MPI_Comm_split(MPI_COMM_WORLD, is_node ? 0 : MPI_UNDEFINED, world_rank, &node_comm);

    if (is_node) {
        // Taabish: periods 0,0 because a charging station on the edge of the
        // map has nobody past the edge. A wrapped grid (torus) would make the
        // corner stations neighbours of the far side of the city.
        // reorder = 0 so grid rank r really is grid position r (row major);
        // the base station relies on that to turn a rank into (x, y) itself.
        int dims[2] = { cfg.rows, cfg.cols }, periods[2] = { 0, 0 };
        MPI_Cart_create(node_comm, 2, dims, periods, 0, &grid_comm);
    }

    MPI_Datatype t_neigh, t_report, t_resp;
    build_datatypes(&t_neigh, &t_report, &t_resp);

    // is MPI_Wtime the same clock on every rank? We record the answer in the
    // log. On our Macs it is not, which is why delays use wsn_now (common.c).
    int *wt_global = NULL, wt_flag = 0, wtime_global = 0;
    MPI_Comm_get_attr(MPI_COMM_WORLD, MPI_WTIME_IS_GLOBAL, &wt_global, &wt_flag);
    if (wt_flag && wt_global) wtime_global = *wt_global;

    double stats[STATS_LEN];
    stats_init(stats);
    double sim_seconds = 0.0;

    // everyone starts the clock together, so cycle 1 means the same moment
    // on every node and the base station's run length lines up with it
    MPI_Barrier(MPI_COMM_WORLD);

    if (is_node)
        run_charging_node(&cfg, grid_comm, bs_rank, t_neigh, t_report, t_resp, stats);
    else
        run_base_station(&cfg, n_nodes, t_report, t_resp, stats, &sim_seconds);

    // Taabish: one MPI_Gather instead of every node sending its stats with
    // its own Send. It is a single collective after the shutdown, so it costs
    // nothing during the simulation itself.
    double *all = NULL;
    if (!is_node) all = malloc(sizeof(double) * STATS_LEN * (size_t)world_size);
    MPI_Gather(stats, STATS_LEN, MPI_DOUBLE, all, STATS_LEN, MPI_DOUBLE, bs_rank, MPI_COMM_WORLD);

    if (!is_node) {
        base_station_finish(&cfg, n_nodes, all, stats, sim_seconds, wtime_global);
        free(all);
    }

    // graceful shutdown: free everything we created, in reverse order
    MPI_Type_free(&t_neigh);
    MPI_Type_free(&t_report);
    MPI_Type_free(&t_resp);
    if (grid_comm != MPI_COMM_NULL) MPI_Comm_free(&grid_comm);
    if (node_comm != MPI_COMM_NULL) MPI_Comm_free(&node_comm);
    MPI_Finalize();
    return 0;
}
