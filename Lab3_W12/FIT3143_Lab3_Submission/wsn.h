////////////////////////////////////////////////////////////////////////////
// wsn.h
// -------------------------------------------------------------------------
// FIT3143 Lab #3: distributed wireless sensor network of EV charging nodes.
//
// Everything both halves of the program have to agree on: message tags,
// the structs that go over the wire, the run configuration, and the layout
// of the timing/statistics array every rank hands back at the end.
//
// Written by: Erwyna Soo Wen Xin (36555789) and Taabish Farooq Bhat
//             (35473932) together, since node.c and base_station.c both
//             depend on it and we had to agree on it before splitting up.
//
// Team:
//   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
//   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
////////////////////////////////////////////////////////////////////////////
#ifndef WSN_H
#define WSN_H

#include <mpi.h>
#include <stdio.h>
#include <time.h>

// ---- limits -------------------------------------------------------------
#define MAX_PORTS     64     // k is capped so the shared port array can be fixed size
#define MAX_NEIGH     4      // up, down, left, right in a 2D grid
#define MAX_CAND      32     // nearest candidates the base station sends back
#define HIST_LEN      256    // availability history kept per node (Table 1 rows)

// ---- message tags -------------------------------------------------------
// One tag per message type, so a receive can ask for exactly the kind of
// message it wants and the delay of each type can be measured on its own.
#define TAG_REQ       10     // node -> neighbour : "how many free ports have you got?"
#define TAG_REPLY     11     // neighbour -> node : "this many"
#define TAG_REPORT    20     // node -> base station : congestion report
#define TAG_RESPONSE  21     // base station -> node : nearest available nodes
#define TAG_TERMINATE 30     // base station -> node : stop starting new work (phase 1)
#define TAG_ACK       31     // node -> base station : nothing of mine is in flight
#define TAG_SHUTDOWN  32     // base station -> node : safe to finalise (phase 2)

// ---- the versions we built and compared ---------------------------------
// Node side (Task 1), how a congested node gets its neighbours' data:
#define NODE_V_BLOCKING    1  // MPI_Send + blocking MPI_Probe/MPI_Recv wait loop
#define NODE_V_NONBLOCKING 2  // MPI_Isend/MPI_Irecv + MPI_Testall, never waits
#define NODE_V_COLLECTIVE  3  // MPI_Neighbor_allgather on the Cartesian communicator every cycle
// Base station side (Task 2), how reports are received and answered:
#define BS_V_PROBE         1  // MPI_Iprobe poll, then blocking MPI_Recv and MPI_Send
#define BS_V_IRECV         2  // one pre-posted MPI_Irecv(ANY_SOURCE) + MPI_Isend replies
#define BS_V_PERSISTENT    3  // one persistent MPI_Recv_init per node + MPI_Testsome + buffered log

// ---- base station answers -----------------------------------------------
#define RESP_CANDIDATES    1  // here are the nearest nodes that should have room
#define RESP_NONE_NEARBY   0  // every neighbour reported inside the window: nothing nearby
#define RESP_NONE_AT_ALL   2  // nothing anywhere in the grid looks free

// ---- load scenarios -----------------------------------------------------
#define SCEN_UNIFORM   0      // every node gets the same arrival rate
#define SCEN_HOTSPOT   1      // a busy block in the middle of the grid, quiet edges
#define SCEN_SATURATED 2      // everything fills up: forces the "none nearby" branch
#define SCEN_IDLE      3      // nothing ever congests: checks the quiet path

// ---- run configuration (same on every rank, parsed from argv) -----------
typedef struct {
    int rows, cols;          // grid is rows x cols, so rows = 1 is the line topology
    int k;                   // charging ports per node
    int threshold;           // congested when free ports <= threshold
    int cycles;              // how many update cycles the simulation runs for
    int cycle_ms;            // real milliseconds per cycle
    int sim_sec_per_cycle;   // simulated seconds per cycle (Table 1 uses 10)
    double window_cycles;    // base station "predefined period", in cycles
    double arrive, depart;   // per port, per cycle probabilities
    int scenario;
    int node_version, bs_version;
    int cooldown;            // cycles a node waits after a report before reporting again
    int poll_us;             // sleep between polls so idle ranks give the core back
    unsigned seed;
    int quiet;               // 1 = do not print every event to stdout
    char log_path[256];      // base station log
    char csv_path[256];      // one summary row per run is appended here ("" = off)
    char node_log_dir[256];  // per node port history logs ("" = off)
} Config;

// ---- what goes over the wire --------------------------------------------
// Neighbour request and reply share one layout. The requester also sends its
// own state, so the neighbour learns it for free.
typedef struct {
    int rank, x, y;          // world rank and grid coordinates of the sender
    int free_ports, k;       // sender's availability right now
    int cycle;               // sender's cycle number
    double t_send;           // wsn_now() when sent (for one way delay)
    double t_echo;           // in a reply: the t_send of the request it answers
} NeighbourMsg;

// The congestion report. Everything the spec asks for, plus the timing we
// need for Task 3, in one message so the node only makes one call.
typedef struct {
    int rank, x, y;                       // who is reporting
    int cycle, k, threshold, free_ports;  // its state when it found the congestion
    int year, month, day, hour, minute, second, msec;  // when it found it (wall clock)
    int n_neigh;                          // how many neighbours it has (2 to 4, 1 in a line end)
    int neigh_rank[MAX_NEIGH];
    int neigh_x[MAX_NEIGH], neigh_y[MAX_NEIGH];
    int neigh_free[MAX_NEIGH];            // what each neighbour said
    int msgs_to_neigh, msgs_from_neigh;   // messages exchanged for this incident
    int bytes_to_neigh, bytes_from_neigh; // and their sizes in bytes
    int reports_so_far;                   // how many reports this node has sent
    int node_version;                     // which Task 1 version produced it
    double t_detect;                      // wsn_now() when congestion was confirmed
    double t_send;                        // wsn_now() when the report left
    double neigh_rtt;                     // how long the neighbour exchange took
} Report;

// The base station's answer.
typedef struct {
    int reporter;            // who this answers
    int status;              // RESP_CANDIDATES / RESP_NONE_NEARBY / RESP_NONE_AT_ALL
    int distance;            // Manhattan distance of the candidates (hops on the grid)
    int n_cand;
    int cand_rank[MAX_CAND];
    int cand_x[MAX_CAND], cand_y[MAX_CAND];
    int cand_free[MAX_CAND]; // last free ports the base station heard, -1 if never
    double t_send;           // wsn_now() when the base station sent it
    double t_echo;           // the report's t_send, so the node can get the round trip
} Response;

// ---- per rank statistics, gathered to the base station at the end -------
// For every message type we keep count, sum, min and max of its delay.
enum {
    M_REQ = 0,   // one way: request leaving a node -> arriving at the neighbour
    M_REPLY,     // one way: reply leaving the neighbour -> arriving back
    M_QRTT,      // round trip of the whole neighbour exchange (all replies in)
    M_REPORT,    // one way: report leaving the node -> arriving at the base station
    M_RESP,      // one way: base station answer -> arriving at the node
    M_RRTT,      // round trip: report sent -> answer received
    M_TERM,      // one way: termination message
    M_COLL,      // time inside MPI_Neighbor_allgather (version 3 only)
    M_BSPROC,    // base station: time to decide candidates for one report
    NUM_M
};
static const char *const M_NAMES[NUM_M] = {
    "req", "reply", "query_rtt", "report", "response", "report_rtt",
    "terminate", "nbr_collective", "bs_process"
};

enum {
    C_CYCLES = 0,       // cycles this node actually sampled
    C_CONGESTED,        // cycles where it was at or under the threshold
    C_QUERIES,          // neighbour exchanges it started
    C_LOCAL_REDIRECT,   // times a neighbour had room, so no report was needed
    C_REPORTS,          // reports sent to the base station
    C_RESP_CAND, C_RESP_NONE, C_RESP_NOWHERE,
    C_MSGS_SENT, C_MSGS_RECV,
    C_BYTES_SENT, C_BYTES_RECV,
    C_BLOCKED,          // seconds the comms thread spent blocked inside MPI
    C_LATE_SUM, C_LATE_MAX, // how late each cycle started (blocking shows up here)
    C_REQ_SERVED,       // neighbour requests this node answered
    NUM_C
};

#define STATS_LEN (4 * NUM_M + NUM_C)
#define S_CNT(i) (4 * (i) + 0)
#define S_SUM(i) (4 * (i) + 1)
#define S_MIN(i) (4 * (i) + 2)
#define S_MAX(i) (4 * (i) + 3)
#define S_C(i)   (4 * NUM_M + (i))

// ---- shared helpers (common.c) ------------------------------------------
int  parse_config(int argc, char **argv, Config *cfg, int world_size, int world_rank);
void build_datatypes(MPI_Datatype *t_neigh, MPI_Datatype *t_report, MPI_Datatype *t_resp);
void stats_init(double *s);
void stats_add(double *s, int type, double value);
void wall_stamp(int *y, int *mo, int *d, int *h, int *mi, int *se, int *ms);
void fmt_wall(char *buf, size_t n);
const char *scenario_name(int s);
void sleep_us(int us);
double wsn_now(void);

// ---- the two roles ------------------------------------------------------
// node.c (Task 1)
void run_charging_node(const Config *cfg, MPI_Comm grid_comm, int bs_rank,
                       MPI_Datatype t_neigh, MPI_Datatype t_report,
                       MPI_Datatype t_resp, double *stats);
// base_station.c (Task 2)
void run_base_station(const Config *cfg, int n_nodes,
                      MPI_Datatype t_report, MPI_Datatype t_resp,
                      double *stats, double *sim_seconds);
void base_station_finish(const Config *cfg, int n_nodes, const double *all_stats,
                         const double *bs_stats, double sim_seconds,
                         int wtime_global);

#endif
