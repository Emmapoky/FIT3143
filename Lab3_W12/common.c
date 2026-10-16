////////////////////////////////////////////////////////////////////////////
// common.c
// -------------------------------------------------------------------------
// FIT3143 Lab #3: helpers both roles use. Argument parsing, the MPI derived
// datatypes for our three structs, wall clock stamps and the small
// statistics accumulator behind every delay number in Task 3.
//
// Written by: Erwyna Soo Wen Xin (36555789)
//
// Team:
//   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
//   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
////////////////////////////////////////////////////////////////////////////
#include "wsn.h"
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include <sys/time.h>
#include <unistd.h>
#include <getopt.h>

static void usage(void) {
    fprintf(stderr,
        "usage: mpirun -np <rows*cols+1> ./wsn <rows> <cols> [options]\n"
        "  -k ports per node            (default 6)\n"
        "  -t threshold, congested when free <= t (default 1)\n"
        "  -c cycles to simulate        (default 40)\n"
        "  -p real ms per cycle         (default 100)\n"
        "  -w base station window in cycles (default 3)\n"
        "  -a arrival prob per port per cycle (default 0.45)\n"
        "  -d departure prob per port per cycle (default 0.30)\n"
        "  -s scenario uniform|hotspot|saturated|idle (default hotspot)\n"
        "  -V node version 1 blocking | 2 nonblocking | 3 collective (default 2)\n"
        "  -B base station version 1 probe | 2 irecv | 3 persistent (default 3)\n"
        "  -C cooldown cycles after a report (default 2)\n"
        "  -P poll sleep in microseconds (default 200)\n"
        "  -S seed (default 3143)\n"
        "  -o base station log file     (default base_station.log)\n"
        "  -r append a summary row to this CSV\n"
        "  -L write per node port history logs into this folder\n"
        "  -q quiet\n");
}

// parse_config
// Every rank parses argv itself. That is cheaper than broadcasting a struct,
// and mpirun hands every rank the same argv anyway. Only rank 0 complains,
// otherwise the same error prints once per process.
int parse_config(int argc, char **argv, Config *cfg, int world_size, int world_rank) {
    memset(cfg, 0, sizeof *cfg);
    cfg->k = 6;  cfg->threshold = 1;  cfg->cycles = 40;  cfg->cycle_ms = 100;
    cfg->sim_sec_per_cycle = 10;      // Table 1 in the spec samples every 10 s
    cfg->window_cycles = 3.0;  cfg->arrive = 0.45;  cfg->depart = 0.30;
    cfg->scenario = SCEN_HOTSPOT;  cfg->node_version = NODE_V_NONBLOCKING;
    cfg->bs_version = BS_V_PERSISTENT;  cfg->cooldown = 2;  cfg->poll_us = 200;
    cfg->seed = 3143;
    strcpy(cfg->log_path, "base_station.log");

    if (argc < 3) { if (world_rank == 0) usage(); return 0; }
    cfg->rows = atoi(argv[1]);
    cfg->cols = atoi(argv[2]);

    // getopt starts after rows and cols
    optind = 3;
    int c;
    while ((c = getopt(argc, argv, "k:t:c:p:w:a:d:s:V:B:C:P:S:o:r:L:q")) != -1) {
        switch (c) {
        case 'k': cfg->k = atoi(optarg); break;
        case 't': cfg->threshold = atoi(optarg); break;
        case 'c': cfg->cycles = atoi(optarg); break;
        case 'p': cfg->cycle_ms = atoi(optarg); break;
        case 'w': cfg->window_cycles = atof(optarg); break;
        case 'a': cfg->arrive = atof(optarg); break;
        case 'd': cfg->depart = atof(optarg); break;
        case 's':
            if      (!strcmp(optarg, "uniform"))   cfg->scenario = SCEN_UNIFORM;
            else if (!strcmp(optarg, "hotspot"))   cfg->scenario = SCEN_HOTSPOT;
            else if (!strcmp(optarg, "saturated")) cfg->scenario = SCEN_SATURATED;
            else if (!strcmp(optarg, "idle"))      cfg->scenario = SCEN_IDLE;
            else { if (world_rank == 0) usage(); return 0; }
            break;
        case 'V': cfg->node_version = atoi(optarg); break;
        case 'B': cfg->bs_version = atoi(optarg); break;
        case 'C': cfg->cooldown = atoi(optarg); break;
        case 'P': cfg->poll_us = atoi(optarg); break;
        case 'S': cfg->seed = (unsigned)strtoul(optarg, NULL, 10); break;
        case 'o': snprintf(cfg->log_path, sizeof cfg->log_path, "%s", optarg); break;
        case 'r': snprintf(cfg->csv_path, sizeof cfg->csv_path, "%s", optarg); break;
        case 'L': snprintf(cfg->node_log_dir, sizeof cfg->node_log_dir, "%s", optarg); break;
        case 'q': cfg->quiet = 1; break;
        default: if (world_rank == 0) usage(); return 0;
        }
    }

    // Same check as the lecturer's virtual topology example: the grid has
    // to account for every process except the base station.
    const char *err = NULL;
    if (cfg->rows < 1 || cfg->cols < 1)                 err = "rows and cols must be >= 1";
    else if (cfg->rows * cfg->cols != world_size - 1)   err = "rows*cols must equal np - 1 (the last rank is the base station)";
    else if (cfg->k < 1 || cfg->k > MAX_PORTS)          err = "k must be 1..64";
    else if (cfg->threshold < 0 || cfg->threshold >= cfg->k) err = "threshold must be 0..k-1";
    else if (cfg->node_version < 1 || cfg->node_version > 3) err = "-V must be 1, 2 or 3";
    else if (cfg->bs_version < 1 || cfg->bs_version > 3)    err = "-B must be 1, 2 or 3";
    else if (cfg->cycles < 1 || cfg->cycle_ms < 1)      err = "cycles and cycle_ms must be >= 1";
    if (err) {
        if (world_rank == 0) { fprintf(stderr, "error: %s\n", err); usage(); }
        return 0;
    }
    return 1;
}

// build_datatypes
// MPI_Type_create_struct describes our C structs to MPI field by field, so a
// whole report goes in ONE call instead of one send per field or an
// MPI_Pack/MPI_Unpack copy on each side. Each struct is laid out ints first
// then doubles, so two blocks describe it. offsetof would also work, but
// MPI_Get_address on a real instance is what the Week 5 sample code does and
// it picks up any padding the compiler adds between the int and double blocks.
// MPI_Type_create_resized pins the extent to sizeof(struct), so arrays of
// these structs would also stride correctly.
static void make_struct_type(int n_int, int n_dbl, const void *base,
                             const void *first_int, const void *first_dbl,
                             size_t size, MPI_Datatype *out) {
    int blocklen[2] = { n_int, n_dbl };
    MPI_Aint b, a0, a1, disp[2];
    MPI_Datatype types[2] = { MPI_INT, MPI_DOUBLE }, tmp;
    MPI_Get_address(base, &b);
    MPI_Get_address(first_int, &a0);
    MPI_Get_address(first_dbl, &a1);
    disp[0] = a0 - b;
    disp[1] = a1 - b;
    MPI_Type_create_struct(2, blocklen, disp, types, &tmp);
    MPI_Type_create_resized(tmp, 0, (MPI_Aint)size, out);
    MPI_Type_commit(out);
    MPI_Type_free(&tmp);
}

void build_datatypes(MPI_Datatype *t_neigh, MPI_Datatype *t_report, MPI_Datatype *t_resp) {
    NeighbourMsg nm;
    Report rp;
    Response rs;
    // the int counts are computed from the struct layout, not typed by hand,
    // so adding a field to wsn.h cannot silently desync the datatype
    make_struct_type((int)((char *)&nm.t_send - (char *)&nm.rank) / (int)sizeof(int), 2,
                     &nm, &nm.rank, &nm.t_send, sizeof nm, t_neigh);
    make_struct_type((int)((char *)&rp.t_detect - (char *)&rp.rank) / (int)sizeof(int), 3,
                     &rp, &rp.rank, &rp.t_detect, sizeof rp, t_report);
    make_struct_type((int)((char *)&rs.t_send - (char *)&rs.reporter) / (int)sizeof(int), 2,
                     &rs, &rs.reporter, &rs.t_send, sizeof rs, t_resp);
}

// ---- statistics ---------------------------------------------------------
void stats_init(double *s) {
    memset(s, 0, sizeof(double) * STATS_LEN);
    for (int i = 0; i < NUM_M; i++) s[S_MIN(i)] = DBL_MAX;
}

void stats_add(double *s, int type, double v) {
    s[S_CNT(type)] += 1.0;
    s[S_SUM(type)] += v;
    if (v < s[S_MIN(type)]) s[S_MIN(type)] = v;
    if (v > s[S_MAX(type)]) s[S_MAX(type)] = v;
}

// ---- clocks -------------------------------------------------------------
// Wall clock date and time for the report and the log. localtime_r, not
// localtime, because port threads may be running at the same moment and
// localtime returns a pointer to one shared static buffer.
void wall_stamp(int *y, int *mo, int *d, int *h, int *mi, int *se, int *ms) {
    struct timeval tv;
    struct tm tmv;
    gettimeofday(&tv, NULL);
    localtime_r(&tv.tv_sec, &tmv);
    *y = tmv.tm_year + 1900; *mo = tmv.tm_mon + 1; *d = tmv.tm_mday;
    *h = tmv.tm_hour; *mi = tmv.tm_min; *se = tmv.tm_sec; *ms = (int)(tv.tv_usec / 1000);
}

void fmt_wall(char *buf, size_t n) {
    int y, mo, d, h, mi, se, ms;
    wall_stamp(&y, &mo, &d, &h, &mi, &se, &ms);
    snprintf(buf, n, "%04d-%02d-%02d %02d:%02d:%02d.%03d", y, mo, d, h, mi, se, ms);
}

const char *scenario_name(int s) {
    switch (s) {
    case SCEN_UNIFORM: return "uniform";
    case SCEN_HOTSPOT: return "hotspot";
    case SCEN_SATURATED: return "saturated";
    default: return "idle";
    }
}

// wsn_now
// The clock every delay in Task 3 is measured with. We started with
// MPI_Wtime, but on our Macs Open MPI reports MPI_WTIME_IS_GLOBAL = 0 and
// each process's MPI_Wtime has its own zero, so a send stamp from one rank
// minus a receive stamp on another gave NEGATIVE one way delays. The system
// real time clock is the same clock for every process on one machine, so
// one way delays are exact there. Across CAAS nodes it is only as close as
// NTP keeps them, which is why every exchange also records its round trip
// on ONE process's clock (query_rtt, report_rtt): those never need syncing.
double wsn_now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (double)ts.tv_sec + ts.tv_nsec * 1e-9;
}

void sleep_us(int us) { if (us > 0) usleep((useconds_t)us); }
