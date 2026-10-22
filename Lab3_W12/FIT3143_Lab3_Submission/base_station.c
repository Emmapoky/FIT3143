////////////////////////////////////////////////////////////////////////////
// base_station.c
// -------------------------------------------------------------------------
// FIT3143 Lab #3 Task 2: the base station.
//
// One MPI process, one thread. It listens for congestion reports from the
// charging nodes, works out the nearest nodes that should still have free
// ports, answers the reporting node, and logs everything. When the run is
// over it shuts every node down in two phases (TERMINATE, wait for every
// ACK, then SHUTDOWN) so nothing is left in flight when MPI_Finalize runs.
//
// Three versions of the receive side, picked with -B:
//   1  probe       MPI_Iprobe in a polling loop, then a blocking MPI_Recv
//                  and a blocking MPI_Send for the answer. The Week 12
//                  virtual topology example works this way.
//   2  irecv       one MPI_Irecv(MPI_ANY_SOURCE) always posted, checked
//                  with MPI_Test, answered with MPI_Isend.
//   3  persistent  one persistent receive per node (MPI_Recv_init), all
//                  checked in one MPI_Testsome call, persistent answers
//                  (MPI_Send_init), and the log written through a 1 MB
//                  buffer instead of one disk write per line.
//
// How the nearest node is chosen (spec "information update mechanism"):
//   Say node 0 reports and its neighbours are 1 and 3.
//   - If 1 AND 3 both reported inside the window (-w cycles), their reports
//     already covered 2, 4 and 6 and said they were full too, so the answer
//     is "no nodes available nearby".
//   - Otherwise we look 2 hops out (2, 4, 6), drop any node we know is full
//     from a report inside the window, and send back ALL that are left,
//     since they are tied at the same distance. If every 2 hop node is full
//     we keep going outwards, 3 hops, 4 hops, and stop at the first ring
//     that has someone free.
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

typedef struct {
    const Config *cfg;
    int n;                       // number of charging nodes
    MPI_Datatype tr, ts;
    int sz_report, sz_resp;
    double *stats;
    FILE *log;
    char *logbuf;                // version 3's 1 MB stdio buffer

    // what the base station knows about the grid
    double *last_report;         // wsn_now() of each node's last report, < 0 = never
    int *known_free;             // last free ports heard for each node
    double *known_time;          //   ... and when, < 0 = never
    int *reports_by;             // reports per node, for the log

    // answers: one buffer per node, so an answer still being sent never
    // gets overwritten by the next one
    Response *resp_buf;
    MPI_Request *resp_req;

    // version 3 persistent receives, one per node
    Report *rep_buf;
    MPI_Request *rep_req;

    long reports, cand, none_nearby, none_at_all, acks;
    long msgs_in, msgs_out;
    double bytes_in, bytes_out;
    double t_start;
} BS;

static double now(void) { return wsn_now(); }   // see common.c for why not MPI_Wtime

// Erwyna: rank -> grid position. This only works because main.c builds the
// grid with reorder = 0 and the split keyed on world rank, so node rank r
// sits at row r / cols, column r % cols, which is MPI's row major order.
static void pos(const BS *b, int r, int *x, int *y) { *x = r / b->cfg->cols; *y = r % b->cfg->cols; }
static int  at(const BS *b, int x, int y) { return x * b->cfg->cols + y; }
static int  inside(const BS *b, int x, int y) { return x >= 0 && y >= 0 && x < b->cfg->rows && y < b->cfg->cols; }

static int recent(double t, double nowt, double window) { return t >= 0 && nowt - t <= window; }

// Erwyna: "known full" means either it reported itself (a report only
// happens when a node AND all its neighbours are full), or a report inside
// the window named it as a neighbour with free ports at or under threshold.
static int known_full(const BS *b, int c, double nowt, double window) {
    if (recent(b->last_report[c], nowt, window)) return 1;
    return recent(b->known_time[c], nowt, window) && b->known_free[c] <= b->cfg->threshold;
}

// ---- the decision --------------------------------------------------------
static void find_candidates(BS *b, const Report *rp, Response *rs, char *why, size_t whylen) {
    const double t = now();
    const double window = b->cfg->window_cycles * b->cfg->cycle_ms / 1000.0;
    const int r = rp->rank;
    int rx, ry;
    pos(b, r, &rx, &ry);

    memset(rs, 0, sizeof *rs);
    rs->reporter = r;
    rs->t_echo = rp->t_send;

    // 1. did every neighbour of the reporter report inside the window?
    //    Checked BEFORE this report updates the table, so it only counts
    //    reports that came earlier, which is what the spec describes.
    const int dx[4] = { -1, 1, 0, 0 }, dy[4] = { 0, 0, -1, 1 };
    int n_nb = 0, n_recent = 0;
    char who[160] = "";
    for (int i = 0; i < 4; i++) {
        int nx = rx + dx[i], ny = ry + dy[i];
        if (!inside(b, nx, ny)) continue;
        int nb = at(b, nx, ny);
        n_nb++;
        int rec = recent(b->last_report[nb], t, window);
        n_recent += rec;
        char one[24];
        snprintf(one, sizeof one, "%s%d:%s", n_nb > 1 ? " " : "", nb, rec ? "yes" : "no");
        strncat(who, one, sizeof who - strlen(who) - 1);
    }

    // 2. now record what this report tells us
    b->last_report[r] = t;
    b->known_free[r] = rp->free_ports;
    b->known_time[r] = t;
    for (int i = 0; i < rp->n_neigh && i < MAX_NEIGH; i++) {
        int nb = rp->neigh_rank[i];
        if (nb < 0 || nb >= b->n) continue;
        b->known_free[nb] = rp->neigh_free[i];
        b->known_time[nb] = t;
    }

    if (n_nb > 0 && n_recent == n_nb) {
        rs->status = RESP_NONE_NEARBY;
        rs->distance = 1;
        snprintf(why, whylen, "all %d neighbours reported in the last %.2f s [%s]", n_nb, window, who);
        return;
    }

    // 3. search outwards ring by ring, starting 2 hops away. The ring at
    //    Manhattan distance d is walked directly (at most 4d cells), so a
    //    report costs O(d) work, not a scan of the whole grid.
    int max_d = (b->cfg->rows - 1) + (b->cfg->cols - 1);
    for (int d = 2; d <= max_d; d++) {
        for (int ox = -d; ox <= d; ox++) {
            int rest = d - abs(ox);
            int oys[2] = { -rest, rest };
            for (int s = 0; s < (rest ? 2 : 1); s++) {
                int cx = rx + ox, cy = ry + oys[s];
                if (!inside(b, cx, cy)) continue;
                int c = at(b, cx, cy);
                if (known_full(b, c, t, window)) continue;
                if (rs->n_cand < MAX_CAND) {
                    rs->cand_rank[rs->n_cand] = c;
                    rs->cand_x[rs->n_cand] = cx;
                    rs->cand_y[rs->n_cand] = cy;
                    rs->cand_free[rs->n_cand] = recent(b->known_time[c], t, window) ? b->known_free[c] : -1;
                    rs->n_cand++;
                }
            }
        }
        if (rs->n_cand > 0) {
            rs->status = RESP_CANDIDATES;
            rs->distance = d;
            snprintf(why, whylen, "%d of %d neighbours reported in the last %.2f s [%s]",
                     n_recent, n_nb, window, who);
            return;
        }
    }
    rs->status = RESP_NONE_AT_ALL;
    rs->distance = -1;
    snprintf(why, whylen, "every other node is known to be full [%s]", who);
}

// ---- one report: decide, answer, log --------------------------------------
static void handle_report(BS *b, const Report *rp) {
    double t_arrive = now();
    stats_add(b->stats, M_REPORT, t_arrive - rp->t_send);
    b->msgs_in++;
    b->bytes_in += b->sz_report;
    b->reports++;
    if (rp->rank >= 0 && rp->rank < b->n) b->reports_by[rp->rank]++;

    double t0 = now();
    int r = rp->rank;
    Response *rs = &b->resp_buf[r];
    // the previous answer to this node must have left before we reuse its
    // buffer. The node never sends a new report before it has that answer,
    // so this never actually waits.
    if (b->cfg->bs_version != BS_V_PROBE) MPI_Wait(&b->resp_req[r], MPI_STATUS_IGNORE);
    char why[256];
    find_candidates(b, rp, rs, why, sizeof why);
    if (rs->status == RESP_CANDIDATES) b->cand++;
    else if (rs->status == RESP_NONE_NEARBY) b->none_nearby++;
    else b->none_at_all++;

    // ---- answer ----
    rs->t_send = now();
    if (b->cfg->bs_version == BS_V_PROBE)
        MPI_Send(rs, 1, b->ts, r, TAG_RESPONSE, MPI_COMM_WORLD);
    else if (b->cfg->bs_version == BS_V_IRECV)
        MPI_Isend(rs, 1, b->ts, r, TAG_RESPONSE, MPI_COMM_WORLD, &b->resp_req[r]);
    else {
        MPI_Start(&b->resp_req[r]);          // persistent send set up for this node's buffer
        // Erwyna: kick the progress engine once. Without this the answer sat
        // in the persistent request until our next MPI call, one poll sleep
        // later, and version 3's report round trip came out ~250 us slower
        // than version 2's even though it does less work per report.
        int sent;
        MPI_Test(&b->resp_req[r], &sent, MPI_STATUS_IGNORE);
    }
    b->msgs_out++;
    b->bytes_out += b->sz_resp;

    // ---- log ----
    FILE *f = b->log;
    char stamp[40];
    fmt_wall(stamp, sizeof stamp);
    fprintf(f, "\n[%s] REPORT #%ld from node %d (%d,%d), its report #%d, cycle %d, sim t+%.1f s\n",
            stamp, b->reports, r, rp->x, rp->y, rp->reports_so_far, rp->cycle, t_arrive - b->t_start);
    fprintf(f, "  congestion found  %04d-%02d-%02d %02d:%02d:%02d.%03d\n",
            rp->year, rp->month, rp->day, rp->hour, rp->minute, rp->second, rp->msec);
    fprintf(f, "  reporter          free %d of %d ports (threshold %d), node version %d\n",
            rp->free_ports, rp->k, rp->threshold, rp->node_version);
    fprintf(f, "  neighbours        ");
    for (int i = 0; i < rp->n_neigh; i++)
        fprintf(f, "%s%d(%d,%d) free %d", i ? " | " : "", rp->neigh_rank[i], rp->neigh_x[i], rp->neigh_y[i], rp->neigh_free[i]);
    fprintf(f, "%s\n", rp->n_neigh ? "" : "none (1x1 grid)");
    fprintf(f, "  neighbour msgs    %d out (%d B), %d in (%d B), exchange took %.3f ms\n",
            rp->msgs_to_neigh, rp->bytes_to_neigh, rp->msgs_from_neigh, rp->bytes_from_neigh, rp->neigh_rtt * 1e3);
    fprintf(f, "  report            %d B, one way delay %.3f ms\n", b->sz_report, (t_arrive - rp->t_send) * 1e3);
    fprintf(f, "  window check      %s\n", why);
    if (rs->status == RESP_CANDIDATES) {
        fprintf(f, "  ANSWER            %d nearest available node(s), %d hops:", rs->n_cand, rs->distance);
        for (int i = 0; i < rs->n_cand; i++) {
            if (rs->cand_free[i] >= 0) fprintf(f, " %d(%d,%d) free %d", rs->cand_rank[i], rs->cand_x[i], rs->cand_y[i], rs->cand_free[i]);
            else                       fprintf(f, " %d(%d,%d) free ?", rs->cand_rank[i], rs->cand_x[i], rs->cand_y[i]);
        }
        fprintf(f, "\n");
    } else if (rs->status == RESP_NONE_NEARBY) {
        fprintf(f, "  ANSWER            no nodes available nearby\n");
    } else {
        fprintf(f, "  ANSWER            no node in the grid is available\n");
    }
    double proc = now() - t0;
    stats_add(b->stats, M_BSPROC, proc);
    fprintf(f, "  base station      decided, answered and logged in %.3f ms\n", proc * 1e3);

    if (!b->cfg->quiet) {
        if (rs->status == RESP_CANDIDATES)
            printf("[base station] report from node %d -> %d candidate(s) at %d hops\n", r, rs->n_cand, rs->distance);
        else
            printf("[base station] report from node %d -> no nodes available %s\n", r,
                   rs->status == RESP_NONE_NEARBY ? "nearby" : "anywhere");
    }
}

static void handle_ack(BS *b) {
    b->acks++;
    b->msgs_in++;
    b->bytes_in += sizeof(double);
}

// ---- shutdown --------------------------------------------------------------
// Erwyna: two phases, because one is not enough. If we sent a single
// "stop" and every node finalised straight away, a node could still be
// waiting on a reply from a neighbour that has already gone, or have a
// report on its way to us. Phase 1 (TERMINATE) stops new work. Each node
// answers with an ACK only when nothing of its own is in flight. Once
// every ACK is in, nothing can still be moving, and phase 2 (SHUTDOWN)
// lets them leave.
static void broadcast_tag(BS *b, int tag, MPI_Request *reqs, double *stamp) {
    *stamp = now();
    for (int i = 0; i < b->n; i++) {
        if (b->cfg->bs_version == BS_V_PROBE)
            MPI_Send(stamp, 1, MPI_DOUBLE, i, tag, MPI_COMM_WORLD);
        else
            MPI_Isend(stamp, 1, MPI_DOUBLE, i, tag, MPI_COMM_WORLD, &reqs[i]);
        b->msgs_out++;
        b->bytes_out += sizeof(double);
    }
}

// ---- version 1: probe ------------------------------------------------------
static void loop_probe(BS *b, double t_end) {
    int phase = 0;
    double stamp;
    while (phase < 2) {
        int flag;
        MPI_Status st;
        MPI_Iprobe(MPI_ANY_SOURCE, MPI_ANY_TAG, MPI_COMM_WORLD, &flag, &st);
        if (flag) {
            if (st.MPI_TAG == TAG_REPORT) {
                Report rp;
                MPI_Recv(&rp, 1, b->tr, st.MPI_SOURCE, TAG_REPORT, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                handle_report(b, &rp);
            } else if (st.MPI_TAG == TAG_ACK) {
                double ts;
                MPI_Recv(&ts, 1, MPI_DOUBLE, st.MPI_SOURCE, TAG_ACK, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                handle_ack(b);
            }
            continue;                      // drain before sleeping again
        }
        if (phase == 0 && now() >= t_end) { broadcast_tag(b, TAG_TERMINATE, NULL, &stamp); phase = 1; }
        if (phase == 1 && b->acks == b->n) { broadcast_tag(b, TAG_SHUTDOWN, NULL, &stamp); phase = 2; }
        sleep_us(b->cfg->poll_us);         // the "periodically listen" part
    }
}

// ---- version 2: one ANY_SOURCE Irecv ---------------------------------------
static void loop_irecv(BS *b, double t_end) {
    Report rp;
    double ack_ts, stamp_t, stamp_s;
    MPI_Request rreq, areq;
    MPI_Request *treq = malloc(sizeof(MPI_Request) * b->n);
    MPI_Request *sreq = malloc(sizeof(MPI_Request) * b->n);
    for (int i = 0; i < b->n; i++) treq[i] = sreq[i] = MPI_REQUEST_NULL;

    // Erwyna: the receives are posted up front, so a report that arrives
    // while we are busy logging lands straight in our buffer instead of
    // sitting in MPI's unexpected message queue
    MPI_Irecv(&rp, 1, b->tr, MPI_ANY_SOURCE, TAG_REPORT, MPI_COMM_WORLD, &rreq);
    MPI_Irecv(&ack_ts, 1, MPI_DOUBLE, MPI_ANY_SOURCE, TAG_ACK, MPI_COMM_WORLD, &areq);

    int phase = 0;
    while (phase < 2) {
        int got = 0, flag;
        MPI_Test(&rreq, &flag, MPI_STATUS_IGNORE);
        if (flag) {
            handle_report(b, &rp);
            MPI_Irecv(&rp, 1, b->tr, MPI_ANY_SOURCE, TAG_REPORT, MPI_COMM_WORLD, &rreq);
            got = 1;
        }
        // Erwyna: guard on NULL. After the last ACK we stop re-posting, and
        // MPI_Test on MPI_REQUEST_NULL returns flag = true every time, which
        // counted phantom ACKs forever and spun this loop at 100% CPU.
        flag = 0;
        if (areq != MPI_REQUEST_NULL) MPI_Test(&areq, &flag, MPI_STATUS_IGNORE);
        if (flag) {
            handle_ack(b);
            if (b->acks < b->n)
                MPI_Irecv(&ack_ts, 1, MPI_DOUBLE, MPI_ANY_SOURCE, TAG_ACK, MPI_COMM_WORLD, &areq);
            got = 1;
        }
        if (got) continue;
        if (phase == 0 && now() >= t_end) { broadcast_tag(b, TAG_TERMINATE, treq, &stamp_t); phase = 1; }
        if (phase == 1 && b->acks == b->n) { broadcast_tag(b, TAG_SHUTDOWN, sreq, &stamp_s); phase = 2; }
        sleep_us(b->cfg->poll_us);
    }
    // graceful: the report receive is still posted and will never match
    // now, so cancel it properly instead of leaving it for MPI_Finalize
    MPI_Cancel(&rreq);
    MPI_Wait(&rreq, MPI_STATUS_IGNORE);
    MPI_Waitall(b->n, treq, MPI_STATUSES_IGNORE);
    MPI_Waitall(b->n, sreq, MPI_STATUSES_IGNORE);
    MPI_Waitall(b->n, b->resp_req, MPI_STATUSES_IGNORE);
    free(treq);
    free(sreq);
}

// ---- version 3: persistent receives + MPI_Testsome --------------------------
static void loop_persistent(BS *b, double t_end) {
    double ack_ts, stamp_t, stamp_s;
    MPI_Request areq;
    MPI_Request *treq = malloc(sizeof(MPI_Request) * b->n);
    MPI_Request *sreq = malloc(sizeof(MPI_Request) * b->n);
    int *idx = malloc(sizeof(int) * b->n);
    for (int i = 0; i < b->n; i++) treq[i] = sreq[i] = MPI_REQUEST_NULL;

    // Erwyna: set the receives up ONCE, one per node with a fixed source
    // and its own buffer, then only restart them. MPI does the matching
    // set up a single time, and a burst of reports from different nodes
    // comes back from ONE MPI_Testsome call instead of one Test per report.
    for (int i = 0; i < b->n; i++) {
        MPI_Recv_init(&b->rep_buf[i], 1, b->tr, i, TAG_REPORT, MPI_COMM_WORLD, &b->rep_req[i]);
        MPI_Send_init(&b->resp_buf[i], 1, b->ts, i, TAG_RESPONSE, MPI_COMM_WORLD, &b->resp_req[i]);
    }
    MPI_Startall(b->n, b->rep_req);
    MPI_Irecv(&ack_ts, 1, MPI_DOUBLE, MPI_ANY_SOURCE, TAG_ACK, MPI_COMM_WORLD, &areq);

    int phase = 0;
    while (phase < 2) {
        int outcount = 0, flag, got = 0;
        MPI_Testsome(b->n, b->rep_req, &outcount, idx, MPI_STATUSES_IGNORE);
        if (outcount != MPI_UNDEFINED && outcount > 0) {
            for (int j = 0; j < outcount; j++) {
                handle_report(b, &b->rep_buf[idx[j]]);
                MPI_Start(&b->rep_req[idx[j]]);     // re-arm this node's receive
            }
            got = 1;
        }
        // Erwyna: guard on NULL. After the last ACK we stop re-posting, and
        // MPI_Test on MPI_REQUEST_NULL returns flag = true every time, which
        // counted phantom ACKs forever and spun this loop at 100% CPU.
        flag = 0;
        if (areq != MPI_REQUEST_NULL) MPI_Test(&areq, &flag, MPI_STATUS_IGNORE);
        if (flag) {
            handle_ack(b);
            if (b->acks < b->n)
                MPI_Irecv(&ack_ts, 1, MPI_DOUBLE, MPI_ANY_SOURCE, TAG_ACK, MPI_COMM_WORLD, &areq);
            got = 1;
        }
        if (got) continue;
        if (phase == 0 && now() >= t_end) { broadcast_tag(b, TAG_TERMINATE, treq, &stamp_t); phase = 1; }
        if (phase == 1 && b->acks == b->n) { broadcast_tag(b, TAG_SHUTDOWN, sreq, &stamp_s); phase = 2; }
        sleep_us(b->cfg->poll_us);
    }
    // graceful: cancel the n persistent receives that are still armed,
    // finish every send, then free every persistent request
    for (int i = 0; i < b->n; i++) {
        MPI_Cancel(&b->rep_req[i]);
        MPI_Wait(&b->rep_req[i], MPI_STATUS_IGNORE);
        MPI_Request_free(&b->rep_req[i]);
        MPI_Wait(&b->resp_req[i], MPI_STATUS_IGNORE);
        MPI_Request_free(&b->resp_req[i]);
    }
    MPI_Waitall(b->n, treq, MPI_STATUSES_IGNORE);
    MPI_Waitall(b->n, sreq, MPI_STATUSES_IGNORE);
    free(treq);
    free(sreq);
    free(idx);
}

// kept between run_base_station and base_station_finish
static BS *g_bs = NULL;

void run_base_station(const Config *cfg, int n_nodes,
                      MPI_Datatype t_report, MPI_Datatype t_resp,
                      double *stats, double *sim_seconds) {
    BS *b = calloc(1, sizeof(BS));
    g_bs = b;
    b->cfg = cfg; b->n = n_nodes; b->tr = t_report; b->ts = t_resp; b->stats = stats;
    MPI_Type_size(t_report, &b->sz_report);
    MPI_Type_size(t_resp, &b->sz_resp);
    b->last_report = malloc(sizeof(double) * n_nodes);
    b->known_time  = malloc(sizeof(double) * n_nodes);
    b->known_free  = malloc(sizeof(int) * n_nodes);
    b->reports_by  = calloc((size_t)n_nodes, sizeof(int));
    b->resp_buf    = calloc((size_t)n_nodes, sizeof(Response));
    b->resp_req    = malloc(sizeof(MPI_Request) * n_nodes);
    b->rep_buf     = calloc((size_t)n_nodes, sizeof(Report));
    b->rep_req     = malloc(sizeof(MPI_Request) * n_nodes);
    for (int i = 0; i < n_nodes; i++) {
        b->last_report[i] = b->known_time[i] = -1.0;
        b->known_free[i] = -1;
        b->resp_req[i] = b->rep_req[i] = MPI_REQUEST_NULL;
    }

    b->log = fopen(cfg->log_path, "w");
    if (!b->log) { perror(cfg->log_path); MPI_Abort(MPI_COMM_WORLD, 3); }
    if (cfg->bs_version == BS_V_PERSISTENT) {
        // Erwyna: full buffering through 1 MB, so logging is a memory copy
        // and the disk is touched a handful of times per run
        b->logbuf = malloc(1 << 20);
        setvbuf(b->log, b->logbuf, _IOFBF, 1 << 20);
    } else {
        setvbuf(b->log, NULL, _IOLBF, 0);   // one write per line, the naive way
    }

    char stamp[40];
    fmt_wall(stamp, sizeof stamp);
    double window_s = cfg->window_cycles * cfg->cycle_ms / 1000.0;
    fprintf(b->log,
        "==========================================================================\n"
        " FIT3143 Lab 3 base station log\n"
        " started            %s\n"
        " grid               %d x %d = %d charging nodes + 1 base station (%s)\n"
        " ports per node     %d, congested when free <= %d\n"
        " cycle              %d ms real = %d s simulated, %d cycles\n"
        " window (period)    %.2f cycles = %.3f s\n"
        " load scenario      %s\n"
        " versions           node %d (%s), base station %d (%s)\n"
        " message sizes      report %d B, answer %d B\n"
        "==========================================================================\n",
        stamp, cfg->rows, cfg->cols, n_nodes, cfg->rows == 1 ? "line topology" : "2D grid",
        cfg->k, cfg->threshold, cfg->cycle_ms, cfg->sim_sec_per_cycle, cfg->cycles,
        cfg->window_cycles, window_s, scenario_name(cfg->scenario),
        cfg->node_version, cfg->node_version == 1 ? "blocking" : cfg->node_version == 2 ? "nonblocking" : "neighbour collective",
        cfg->bs_version, cfg->bs_version == 1 ? "probe" : cfg->bs_version == 2 ? "irecv" : "persistent",
        b->sz_report, b->sz_resp);

    b->t_start = now();
    double t_end = b->t_start + cfg->cycles * (cfg->cycle_ms / 1000.0);
    if (cfg->bs_version == BS_V_PROBE) loop_probe(b, t_end);
    else if (cfg->bs_version == BS_V_IRECV) loop_irecv(b, t_end);
    else loop_persistent(b, t_end);
    *sim_seconds = now() - b->t_start;

    stats[S_C(C_MSGS_SENT)] = (double)b->msgs_out;
    stats[S_C(C_MSGS_RECV)] = (double)b->msgs_in;
    stats[S_C(C_BYTES_SENT)] = b->bytes_out;
    stats[S_C(C_BYTES_RECV)] = b->bytes_in;
}

// ---- summary ---------------------------------------------------------------
static double mean_us(const double *s, int m) { return s[S_CNT(m)] > 0 ? s[S_SUM(m)] / s[S_CNT(m)] * 1e6 : 0.0; }
static double max_us(const double *s, int m)  { return s[S_CNT(m)] > 0 ? s[S_MAX(m)] * 1e6 : 0.0; }

void base_station_finish(const Config *cfg, int n_nodes, const double *all,
                         const double *bs_stats, double sim_seconds, int wtime_global) {
    BS *b = g_bs;
    FILE *f = b->log;

    // combine every node's numbers, plus the base station's own
    double tot[STATS_LEN];
    stats_init(tot);
    for (int r = 0; r <= n_nodes; r++) {
        const double *s = (r == n_nodes) ? bs_stats : all + (size_t)r * STATS_LEN;
        for (int m = 0; m < NUM_M; m++) {
            if (s[S_CNT(m)] <= 0) continue;
            tot[S_CNT(m)] += s[S_CNT(m)];
            tot[S_SUM(m)] += s[S_SUM(m)];
            if (s[S_MIN(m)] < tot[S_MIN(m)]) tot[S_MIN(m)] = s[S_MIN(m)];
            if (s[S_MAX(m)] > tot[S_MAX(m)]) tot[S_MAX(m)] = s[S_MAX(m)];
        }
        if (r == n_nodes) continue;      // base station counters are added below
        for (int c = 0; c < NUM_C; c++) {
            if (c == C_LATE_MAX) { if (s[S_C(c)] > tot[S_C(c)]) tot[S_C(c)] = s[S_C(c)]; }
            else tot[S_C(c)] += s[S_C(c)];
        }
    }
    double msgs = tot[S_C(C_MSGS_SENT)] + (double)b->msgs_out;
    double bytes = tot[S_C(C_BYTES_SENT)] + b->bytes_out;
    double cyc = tot[S_C(C_CYCLES)] > 0 ? tot[S_C(C_CYCLES)] : 1;

    // per node table: the per worker timing the Lab 1 and Lab 2 feedback asked for
    fprintf(f, "\n==========================================================================\n");
    fprintf(f, " PER NODE\n");
    fprintf(f, " node  (x,y)  cycles congested queries local reports sent recv  query_rtt_ms report_rtt_ms blocked_s\n");
    for (int r = 0; r < n_nodes; r++) {
        const double *s = all + (size_t)r * STATS_LEN;
        int x, y;
        pos(b, r, &x, &y);
        fprintf(f, " %4d (%2d,%2d) %6.0f %9.0f %7.0f %5.0f %7.0f %5.0f %5.0f  %12.3f %13.3f %9.4f\n",
                r, x, y, s[S_C(C_CYCLES)], s[S_C(C_CONGESTED)], s[S_C(C_QUERIES)],
                s[S_C(C_LOCAL_REDIRECT)], s[S_C(C_REPORTS)], s[S_C(C_MSGS_SENT)], s[S_C(C_MSGS_RECV)],
                mean_us(s, M_QRTT) / 1e3, mean_us(s, M_RRTT) / 1e3, s[S_C(C_BLOCKED)]);
    }

    fprintf(f, "\n==========================================================================\n");
    fprintf(f, " SUMMARY\n");
    fprintf(f, " simulation time        %.3f s (%d cycles requested)\n", sim_seconds, cfg->cycles);
    fprintf(f, " congested node cycles  %.0f of %.0f sampled\n", tot[S_C(C_CONGESTED)], tot[S_C(C_CYCLES)]);
    fprintf(f, " neighbour exchanges    %.0f (%.0f solved locally by a neighbour with room)\n",
            tot[S_C(C_QUERIES)], tot[S_C(C_LOCAL_REDIRECT)]);
    fprintf(f, " alerts (reports)       %ld\n", b->reports);
    fprintf(f, "   answered with nodes  %ld\n", b->cand);
    fprintf(f, "   none nearby          %ld\n", b->none_nearby);
    fprintf(f, "   none anywhere        %ld\n", b->none_at_all);
    fprintf(f, " messages / events      %.0f messages, %.0f bytes in total\n", msgs, bytes);
    fprintf(f, "   base station         %ld in, %ld out (incl. %d TERMINATE, %d SHUTDOWN, %ld ACK)\n",
            b->msgs_in, b->msgs_out, n_nodes, n_nodes, b->acks);
    fprintf(f, " clock                  system real time clock for stamps (MPI_Wtime global: %s).\n"
               "                        One way delays are exact on one machine; across machines\n"
               "                        trust the round trips (query_rtt, report_rtt) first.\n", wtime_global ? "yes" : "no");
    fprintf(f, "\n delay per message type   count     mean_us      min_us      max_us\n");
    for (int m = 0; m < NUM_M; m++) {
        if (tot[S_CNT(m)] <= 0) continue;
        fprintf(f, " %-22s %7.0f %11.2f %11.2f %11.2f\n", M_NAMES[m], tot[S_CNT(m)],
                mean_us(tot, m), tot[S_MIN(m)] * 1e6, max_us(tot, m));
    }
    fprintf(f, "\n node comms thread blocked in MPI   %.4f s per node on average\n", tot[S_C(C_BLOCKED)] / n_nodes);
    fprintf(f, " cycle start lateness              mean %.3f ms, worst %.3f ms\n",
            tot[S_C(C_LATE_SUM)] / cyc * 1e3, tot[S_C(C_LATE_MAX)] * 1e3);
    fprintf(f, " shutdown                          %ld of %d ACKs, all requests completed and freed\n",
            b->acks, n_nodes);
    fprintf(f, "==========================================================================\n");

    printf("[base station] %dx%d, node v%d, bs v%d: %.2f s, %ld reports (%ld with nodes, %ld none nearby, %ld none anywhere), "
           "%.0f messages. Log: %s\n",
           cfg->rows, cfg->cols, cfg->node_version, cfg->bs_version, sim_seconds, b->reports, b->cand,
           b->none_nearby, b->none_at_all, msgs, cfg->log_path);

    // one row per run for the Task 3 graphs
    if (cfg->csv_path[0]) {
        FILE *c = fopen(cfg->csv_path, "a");
        if (c) {
            fseek(c, 0, SEEK_END);
            if (ftell(c) == 0) {
                fprintf(c, "rows,cols,nodes,k,threshold,cycles,cycle_ms,window_cycles,scenario,node_v,bs_v,"
                           "wtime_global,sim_s,reports,resp_cand,resp_none_nearby,resp_none_anywhere,"
                           "local_redirects,queries,congested_cycles,cycles,msgs,bytes");
                for (int m = 0; m < NUM_M; m++) fprintf(c, ",%s_n,%s_mean_us,%s_max_us", M_NAMES[m], M_NAMES[m], M_NAMES[m]);
                fprintf(c, ",blocked_s_per_node,late_mean_ms,late_max_ms,req_served\n");
            }
            fprintf(c, "%d,%d,%d,%d,%d,%d,%d,%.2f,%s,%d,%d,%d,%.4f,%ld,%ld,%ld,%ld,%.0f,%.0f,%.0f,%.0f,%.0f,%.0f",
                    cfg->rows, cfg->cols, n_nodes, cfg->k, cfg->threshold, cfg->cycles, cfg->cycle_ms,
                    cfg->window_cycles, scenario_name(cfg->scenario), cfg->node_version, cfg->bs_version,
                    wtime_global, sim_seconds, b->reports, b->cand, b->none_nearby, b->none_at_all,
                    tot[S_C(C_LOCAL_REDIRECT)], tot[S_C(C_QUERIES)], tot[S_C(C_CONGESTED)], tot[S_C(C_CYCLES)],
                    msgs, bytes);
            for (int m = 0; m < NUM_M; m++)
                fprintf(c, ",%.0f,%.3f,%.3f", tot[S_CNT(m)], mean_us(tot, m), max_us(tot, m));
            fprintf(c, ",%.5f,%.4f,%.4f,%.0f\n", tot[S_C(C_BLOCKED)] / n_nodes,
                    tot[S_C(C_LATE_SUM)] / cyc * 1e3, tot[S_C(C_LATE_MAX)] * 1e3, tot[S_C(C_REQ_SERVED)]);
            fclose(c);
        }
    }

    // graceful: flush the (possibly 1 MB) log buffer, then free everything
    fclose(f);
    free(b->logbuf);
    free(b->last_report); free(b->known_time); free(b->known_free); free(b->reports_by);
    free(b->resp_buf); free(b->resp_req); free(b->rep_buf); free(b->rep_req);
    free(b);
    g_bs = NULL;
}
