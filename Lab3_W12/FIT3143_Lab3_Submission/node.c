////////////////////////////////////////////////////////////////////////////
// node.c
// -------------------------------------------------------------------------
// FIT3143 Lab #3 Task 1: the EV charging node.
//
// One MPI process = one charging node at (x, y) in the Cartesian grid.
// Inside it, an OpenMP team of k + 1 threads:
//   thread 0        the comms thread. The only thread that calls MPI
//                   (MPI_THREAD_FUNNELED). Runs the cycle clock, samples
//                   the ports, talks to the neighbours and the base station.
//   threads 1 .. k  one per charging port. Each cycle a port either gets a
//                   car (arrival) or loses one (departure) at random, and
//                   writes its in use / free status into the shared array.
//
// Each cycle the comms thread counts the free ports. At or under the
// threshold it asks its up/down/left/right neighbours how many free ports
// they have. If any neighbour has room, the EVs are sent there and that is
// the end of it. If none do, it sends one report to the base station, gets
// back the nearest available nodes, and "forwards" them to the EVs.
//
// Three versions of the neighbour exchange, picked with -V:
//   1  blocking     MPI_Send the requests, then sit in MPI_Probe/MPI_Recv
//                   until every reply is in. The ports stall meanwhile.
//   2  nonblocking  MPI_Isend + MPI_Irecv, then keep running cycles and
//                   check with MPI_Testall. Nothing ever waits.
//   3  collective   every node shares its free count with every neighbour
//                   every cycle with MPI_Neighbor_allgather, so a congested
//                   node already has the numbers and sends no request at all.
//
// Written by: Taabish Farooq Bhat (35473932)
//
// Team:
//   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
//   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
////////////////////////////////////////////////////////////////////////////
#include "wsn.h"
#include <omp.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>

#define POOL 64   // outstanding nonblocking replies a node can have at once

// ---- the shared array ---------------------------------------------------
// Taabish: this is the "shared array accessible to all threads" from the
// spec. Every port thread writes ONLY its own slot of status[] and
// done_tick[], so two ports never write the same int and there is no data
// race between them. The comms thread is the only writer of tick, stop and
// divert, and the only reader that needs all slots at once. That one writer
// per field rule is why we get away with OpenMP atomics instead of a lock.
typedef struct {
    int status[MAX_PORTS];      // 1 = in use, 0 = free
    int done_tick[MAX_PORTS];   // last cycle each port finished updating
    int tick;                   // current cycle, bumped by the comms thread
    int stop;                   // 1 = ports should exit
    int divert;                 // > 0: EVs are being sent elsewhere, fewer arrivals
    double arrive, depart;      // this node's arrival / departure probability
    int cycle_ms;
    // availability history, Table 1 in the spec. Comms thread only.
    struct { time_t wall; int sim_sec; int avail; } hist[HIST_LEN];
    int hist_n;
} PortTable;

typedef struct {
    const Config *cfg;
    MPI_Comm grid;
    int bs;                             // base station world rank
    int me, x, y;                       // my world rank and grid position
    // neighbours in MPI_Neighbor_allgather order: up, down, left, right.
    // MPI_PROC_NULL where the grid ends.
    int nb_raw[MAX_NEIGH];
    int n_nb, nb[MAX_NEIGH], nb_x[MAX_NEIGH], nb_y[MAX_NEIGH];  // just the real ones
    MPI_Datatype tn, tr, ts;
    int sz_neigh, sz_report;            // bytes per message, from MPI_Type_size
    double *stats;
    PortTable *pt;

    int cycle, free_now;
    int term_received, stop_initiating, acked, shutdown;
    int cooldown_left, reports;

    // the neighbour exchange in flight (versions 1 and 2)
    int q_active;
    double q_t0;
    NeighbourMsg q_out[MAX_NEIGH], q_in[MAX_NEIGH];
    MPI_Request q_sreq[MAX_NEIGH], q_rreq[MAX_NEIGH];
    int q_got[MAX_NEIGH];

    // the report in flight
    int r_active;
    double r_t0;
    Report rep;
    Response resp;
    MPI_Request r_sreq, r_rreq;

    // replies we sent with MPI_Isend and have not seen complete yet
    MPI_Request pool[POOL];
    NeighbourMsg pool_buf[POOL];

    FILE *nlog;                         // optional per node log
} Node;

static double now(void) { return wsn_now(); }   // see common.c for why not MPI_Wtime

static void count_send(Node *n, int bytes) {
    n->stats[S_C(C_MSGS_SENT)] += 1;
    n->stats[S_C(C_BYTES_SENT)] += bytes;
}
static void count_recv(Node *n, int bytes) {
    n->stats[S_C(C_MSGS_RECV)] += 1;
    n->stats[S_C(C_BYTES_RECV)] += bytes;
}

// ---- load model ---------------------------------------------------------
// Taabish: the hotspot scenario is our low availability test case. A block
// of nodes around the middle of the grid fills up and stays full, so the
// nodes inside it see full neighbours and have to go to the base station,
// while the nodes on its border find room next door. That exercises both
// branches of the spec on every run. "saturated" fills everything, which is
// how we test the base station's "no nodes available nearby" answer.
static void set_load(Node *n) {
    const Config *c = n->cfg;
    double a = c->arrive, d = c->depart;
    if (c->scenario == SCEN_HOTSPOT) {
        int cx = c->rows / 2, cy = c->cols / 2;
        int small = c->rows < c->cols ? c->rows : c->cols;
        int radius = small / 3 > 1 ? small / 3 : 1;
        int dist = abs(n->x - cx) + abs(n->y - cy);
        if (dist <= radius) { a = 0.90; d = 0.05; }   // busy: about 95% occupied
        else                { a = 0.25; d = 0.35; }   // quiet: about 42% occupied
    } else if (c->scenario == SCEN_SATURATED) { a = 0.95; d = 0.02; }
    else if (c->scenario == SCEN_IDLE)        { a = 0.05; d = 0.60; }
    n->pt->arrive = a;
    n->pt->depart = d;
}

// ---- the charging port threads ------------------------------------------
// Taabish: each port only wakes up when the comms thread starts a new cycle,
// so all k ports update once per cycle and the comms thread can wait until
// all of them have before it counts. rand_r with its own seed per thread,
// because rand() shares one hidden state between threads and is not safe.
static void port_loop(Node *n, int p) {
    PortTable *pt = n->pt;
    unsigned seed = n->cfg->seed ^ (unsigned)(n->me * 7919) ^ (unsigned)((p + 1) * 104729);
    int my_tick = 0;

    // start half full so the first few cycles are not all empty
    int s = (rand_r(&seed) % 2);
    #pragma omp atomic write seq_cst
    pt->status[p] = s;

    for (;;) {
        int stop, t;
        #pragma omp atomic read seq_cst
        stop = pt->stop;
        if (stop) break;
        #pragma omp atomic read seq_cst
        t = pt->tick;
        if (t == my_tick) { sleep_us(1000); continue; }   // no new cycle yet
        my_tick = t;

        int divert;
        #pragma omp atomic read seq_cst
        divert = pt->divert;
        double arrive = pt->arrive * (divert > 0 ? 0.3 : 1.0);  // EVs sent elsewhere
        double u = (double)rand_r(&seed) / RAND_MAX;
        if (s) { if (u < pt->depart) s = 0; }   // a car leaves
        else   { if (u < arrive)     s = 1; }   // a car arrives

        // status first, then done_tick, both seq_cst: once the comms thread
        // sees done_tick == t it is guaranteed to see this cycle's status
        #pragma omp atomic write seq_cst
        pt->status[p] = s;
        #pragma omp atomic write seq_cst
        pt->done_tick[p] = my_tick;

        // nothing to do until the next cycle, so sleep most of it instead of
        // spinning, then go back to checking every millisecond
        sleep_us(pt->cycle_ms * 700);
    }
}

// ---- message helpers ----------------------------------------------------
static void fill_neigh_msg(Node *n, NeighbourMsg *m, double echo) {
    m->rank = n->me; m->x = n->x; m->y = n->y;
    m->free_ports = n->free_now; m->k = n->cfg->k; m->cycle = n->cycle;
    m->t_echo = echo;
    m->t_send = now();
}

// a free slot in the reply pool, waiting on one if they are all in use
static int pool_slot(Node *n) {
    for (int i = 0; i < POOL; i++) {
        if (n->pool[i] == MPI_REQUEST_NULL) return i;
        int done = 0;
        MPI_Test(&n->pool[i], &done, MPI_STATUS_IGNORE);
        if (done) return i;
    }
    int idx;
    MPI_Waitany(POOL, n->pool, &idx, MPI_STATUS_IGNORE);
    return idx;
}

// answer one neighbour request that MPI_Probe/MPI_Iprobe has already found
static void serve_request(Node *n, MPI_Status *st) {
    NeighbourMsg req;
    MPI_Recv(&req, 1, n->tn, st->MPI_SOURCE, TAG_REQ, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    stats_add(n->stats, M_REQ, now() - req.t_send);
    count_recv(n, n->sz_neigh);
    n->stats[S_C(C_REQ_SERVED)] += 1;

    if (n->cfg->node_version == NODE_V_BLOCKING) {
        // Taabish: version 1 replies with plain MPI_Send. A 48 byte message
        // goes out eagerly in Open MPI so this returns at once in practice,
        // but the standard lets MPI_Send block until it is received, and two
        // nodes replying to each other could then deadlock. That risk is one
        // of the reasons version 2 exists.
        NeighbourMsg rep;
        fill_neigh_msg(n, &rep, req.t_send);
        double t = now();
        MPI_Send(&rep, 1, n->tn, st->MPI_SOURCE, TAG_REPLY, MPI_COMM_WORLD);
        n->stats[S_C(C_BLOCKED)] += now() - t;
    } else {
        int i = pool_slot(n);
        fill_neigh_msg(n, &n->pool_buf[i], req.t_send);
        MPI_Isend(&n->pool_buf[i], 1, n->tn, st->MPI_SOURCE, TAG_REPLY, MPI_COMM_WORLD, &n->pool[i]);
    }
    count_send(n, n->sz_neigh);
}

static void on_terminate(Node *n) {
    double t_sent;
    MPI_Recv(&t_sent, 1, MPI_DOUBLE, n->bs, TAG_TERMINATE, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    stats_add(n->stats, M_TERM, now() - t_sent);
    count_recv(n, (int)sizeof(double));
    n->term_received = 1;
    // version 3 has to agree on the stop with the others first (see sample_cycle)
    if (n->cfg->node_version != NODE_V_COLLECTIVE) n->stop_initiating = 1;
    if (n->nlog) fprintf(n->nlog, "cycle %d: termination message from base station\n", n->cycle);
}

static void on_shutdown(Node *n) {
    double t_sent;
    MPI_Recv(&t_sent, 1, MPI_DOUBLE, n->bs, TAG_SHUTDOWN, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    count_recv(n, (int)sizeof(double));
    n->shutdown = 1;
}

// check for anything that can arrive at any time: neighbour requests,
// termination and shutdown. Drains all waiting requests in one go.
static void service_incoming(Node *n) {
    int flag;
    MPI_Status st;
    for (;;) {
        MPI_Iprobe(MPI_ANY_SOURCE, TAG_REQ, MPI_COMM_WORLD, &flag, &st);
        if (!flag) break;
        serve_request(n, &st);
    }
    MPI_Iprobe(n->bs, TAG_TERMINATE, MPI_COMM_WORLD, &flag, &st);
    if (flag) on_terminate(n);
    MPI_Iprobe(n->bs, TAG_SHUTDOWN, MPI_COMM_WORLD, &flag, &st);
    if (flag) on_shutdown(n);
}

// ---- after the neighbour data is in --------------------------------------
static void send_report(Node *n, const int *nfree, double q_rtt, int msgs_out, int msgs_in);

// Taabish: one function decides for all three versions, so they differ only
// in HOW they get the neighbours' numbers, never in what they do with them.
static void decide(Node *n, const int *nfree, double q_rtt, int msgs_out, int msgs_in) {
    const int thr = n->cfg->threshold;
    int best = -1, best_free = thr;
    for (int i = 0; i < n->n_nb; i++)
        if (nfree[i] > best_free) { best_free = nfree[i]; best = i; }

    if (best >= 0) {
        // a neighbour has room, so this is handled locally, no report
        n->stats[S_C(C_LOCAL_REDIRECT)] += 1;
        #pragma omp atomic write seq_cst
        n->pt->divert = 2;
        if (!n->cfg->quiet)
            printf("[node %d (%d,%d)] cycle %d: full (%d free), EVs sent to neighbour %d (%d free)\n",
                   n->me, n->x, n->y, n->cycle, n->free_now, n->nb[best], best_free);
        if (n->nlog)
            fprintf(n->nlog, "cycle %d: %d free, neighbour %d has %d free, EVs redirected there\n",
                    n->cycle, n->free_now, n->nb[best], best_free);
        n->cooldown_left = n->cfg->cooldown;
    } else {
        send_report(n, nfree, q_rtt, msgs_out, msgs_in);
    }
}

// fill and send the congestion report: one message, one call
static void send_report(Node *n, const int *nfree, double q_rtt, int msgs_out, int msgs_in) {
    Report *r = &n->rep;
    memset(r, 0, sizeof *r);
    r->rank = n->me; r->x = n->x; r->y = n->y;
    r->cycle = n->cycle; r->k = n->cfg->k; r->threshold = n->cfg->threshold;
    r->free_ports = n->free_now;
    wall_stamp(&r->year, &r->month, &r->day, &r->hour, &r->minute, &r->second, &r->msec);
    r->n_neigh = n->n_nb;
    for (int i = 0; i < n->n_nb; i++) {
        r->neigh_rank[i] = n->nb[i];
        r->neigh_x[i] = n->nb_x[i];
        r->neigh_y[i] = n->nb_y[i];
        r->neigh_free[i] = nfree[i];
    }
    for (int i = n->n_nb; i < MAX_NEIGH; i++) { r->neigh_rank[i] = -1; r->neigh_free[i] = -1; }
    int unit = (n->cfg->node_version == NODE_V_COLLECTIVE) ? (int)sizeof(int) : n->sz_neigh;
    r->msgs_to_neigh = msgs_out;
    r->msgs_from_neigh = msgs_in;
    r->bytes_to_neigh = msgs_out * unit;
    r->bytes_from_neigh = msgs_in * unit;
    r->reports_so_far = ++n->reports;
    r->node_version = n->cfg->node_version;
    r->neigh_rtt = q_rtt;
    r->t_detect = now();
    n->stats[S_C(C_REPORTS)] += 1;

    if (!n->cfg->quiet)
        printf("[node %d (%d,%d)] cycle %d: me and all %d neighbours full, reporting to base station\n",
               n->me, n->x, n->y, n->cycle, n->n_nb);
    if (n->nlog)
        fprintf(n->nlog, "cycle %d: %d free and every neighbour at or under threshold, report #%d sent\n",
                n->cycle, n->free_now, n->reports);

    n->r_t0 = now();
    r->t_send = n->r_t0;
    if (n->cfg->node_version == NODE_V_BLOCKING) {
        double t = now();
        MPI_Send(r, 1, n->tr, n->bs, TAG_REPORT, MPI_COMM_WORLD);
        n->stats[S_C(C_BLOCKED)] += now() - t;
    } else {
        // Taabish: post the receive for the answer BEFORE sending the report,
        // so the answer can never arrive with nowhere to land
        MPI_Irecv(&n->resp, 1, n->ts, n->bs, TAG_RESPONSE, MPI_COMM_WORLD, &n->r_rreq);
        MPI_Isend(r, 1, n->tr, n->bs, TAG_REPORT, MPI_COMM_WORLD, &n->r_sreq);
    }
    count_send(n, n->sz_report);
    n->r_active = 1;
}

static void on_response(Node *n) {
    double t = now();
    Response *rs = &n->resp;
    stats_add(n->stats, M_RESP, t - rs->t_send);
    stats_add(n->stats, M_RRTT, t - n->r_t0);
    count_recv(n, (int)sizeof(Response));
    n->r_active = 0;
    n->cooldown_left = n->cfg->cooldown;

    if (rs->status == RESP_CANDIDATES) {
        n->stats[S_C(C_RESP_CAND)] += 1;
        #pragma omp atomic write seq_cst
        n->pt->divert = 3;
    } else if (rs->status == RESP_NONE_NEARBY) n->stats[S_C(C_RESP_NONE)] += 1;
    else n->stats[S_C(C_RESP_NOWHERE)] += 1;

    // "forward to the EVs": in the simulation that is this message
    char list[512] = "";
    for (int i = 0; i < rs->n_cand && strlen(list) < sizeof list - 32; i++) {
        char one[40];
        snprintf(one, sizeof one, "%s%d(%d,%d)", i ? " " : "", rs->cand_rank[i], rs->cand_x[i], rs->cand_y[i]);
        strcat(list, one);
    }
    if (!n->cfg->quiet) {
        if (rs->status == RESP_CANDIDATES)
            printf("[node %d (%d,%d)] base station says go to: %s (%d hops)\n", n->me, n->x, n->y, list, rs->distance);
        else
            printf("[node %d (%d,%d)] base station says: no nodes available %s\n", n->me, n->x, n->y,
                   rs->status == RESP_NONE_NEARBY ? "nearby" : "anywhere");
    }
    if (n->nlog) {
        if (rs->status == RESP_CANDIDATES)
            fprintf(n->nlog, "  base station answer after %.3f ms: EVs forwarded to %s, %d hops away\n",
                    (t - n->r_t0) * 1e3, list, rs->distance);
        else
            fprintf(n->nlog, "  base station answer after %.3f ms: no nodes available %s\n",
                    (t - n->r_t0) * 1e3, rs->status == RESP_NONE_NEARBY ? "nearby" : "anywhere");
    }
}

// ---- version 1: blocking -------------------------------------------------
// Taabish: the waits below still have to answer other nodes' requests. If
// they only waited for replies, two neighbours full at the same time would
// each wait for the other's reply while ignoring the other's request, and
// that is a deadlock. So the wait is "MPI_Probe for anything, deal with
// whatever it is", and the time spent inside MPI_Probe is what C_BLOCKED
// measures. During that time this node runs no cycles at all.
static void blocking_wait(Node *n, int want_replies, int want_response) {
    MPI_Status st;
    int got = 0;
    while ((want_replies && got < n->n_nb) || (want_response && n->r_active)) {
        double t = now();
        MPI_Probe(MPI_ANY_SOURCE, MPI_ANY_TAG, MPI_COMM_WORLD, &st);
        n->stats[S_C(C_BLOCKED)] += now() - t;

        switch (st.MPI_TAG) {
        case TAG_REQ: serve_request(n, &st); break;
        case TAG_REPLY: {
            NeighbourMsg m;
            MPI_Recv(&m, 1, n->tn, st.MPI_SOURCE, TAG_REPLY, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            stats_add(n->stats, M_REPLY, now() - m.t_send);
            count_recv(n, n->sz_neigh);
            for (int i = 0; i < n->n_nb; i++)
                if (n->nb[i] == st.MPI_SOURCE && !n->q_got[i]) { n->q_in[i] = m; n->q_got[i] = 1; got++; break; }
            break;
        }
        case TAG_RESPONSE:
            MPI_Recv(&n->resp, 1, n->ts, n->bs, TAG_RESPONSE, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            on_response(n);
            break;
        case TAG_TERMINATE: on_terminate(n); break;
        case TAG_SHUTDOWN:  on_shutdown(n);  break;   // cannot happen before our ACK
        default: {
            // never expected; receive it so it is not left behind at finalise
            int sz;
            MPI_Get_count(&st, MPI_BYTE, &sz);
            char *junk = malloc((size_t)sz + 1);
            MPI_Recv(junk, sz, MPI_BYTE, st.MPI_SOURCE, st.MPI_TAG, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            free(junk);
        }
        }
    }
}

static void blocking_exchange(Node *n) {
    n->stats[S_C(C_QUERIES)] += 1;
    memset(n->q_got, 0, sizeof n->q_got);
    double t0 = now();
    for (int i = 0; i < n->n_nb; i++) {
        fill_neigh_msg(n, &n->q_out[i], 0.0);
        double t = now();
        MPI_Send(&n->q_out[i], 1, n->tn, n->nb[i], TAG_REQ, MPI_COMM_WORLD);
        n->stats[S_C(C_BLOCKED)] += now() - t;
        count_send(n, n->sz_neigh);
    }
    blocking_wait(n, 1, 0);
    double rtt = now() - t0;
    if (n->n_nb) stats_add(n->stats, M_QRTT, rtt);

    int nfree[MAX_NEIGH];
    for (int i = 0; i < n->n_nb; i++) nfree[i] = n->q_in[i].free_ports;
    decide(n, nfree, rtt, n->n_nb, n->n_nb);
    if (n->r_active) blocking_wait(n, 0, 1);    // version 1 also waits for the answer
}

// ---- version 2: nonblocking ----------------------------------------------
static void start_nb_exchange(Node *n) {
    n->stats[S_C(C_QUERIES)] += 1;
    n->q_t0 = now();
    // receives first, then sends, for the same reason as the report
    for (int i = 0; i < n->n_nb; i++)
        MPI_Irecv(&n->q_in[i], 1, n->tn, n->nb[i], TAG_REPLY, MPI_COMM_WORLD, &n->q_rreq[i]);
    for (int i = 0; i < n->n_nb; i++) {
        fill_neigh_msg(n, &n->q_out[i], 0.0);
        MPI_Isend(&n->q_out[i], 1, n->tn, n->nb[i], TAG_REQ, MPI_COMM_WORLD, &n->q_sreq[i]);
        count_send(n, n->sz_neigh);
    }
    n->q_active = 1;
    if (n->n_nb == 0) {            // 1x1 grid: nobody to ask
        n->q_active = 0;
        decide(n, NULL, 0.0, 0, 0);
    }
}

static void progress_nb(Node *n) {
    if (n->q_active) {
        int done = 0;
        MPI_Testall(n->n_nb, n->q_rreq, &done, MPI_STATUSES_IGNORE);
        if (done) {
            double t = now();
            // every reply is in, so every request was received: this returns at once
            MPI_Waitall(n->n_nb, n->q_sreq, MPI_STATUSES_IGNORE);
            int nfree[MAX_NEIGH];
            for (int i = 0; i < n->n_nb; i++) {
                stats_add(n->stats, M_REPLY, t - n->q_in[i].t_send);
                count_recv(n, n->sz_neigh);
                nfree[i] = n->q_in[i].free_ports;
            }
            stats_add(n->stats, M_QRTT, t - n->q_t0);
            n->q_active = 0;
            decide(n, nfree, t - n->q_t0, n->n_nb, n->n_nb);
        }
    }
    if (n->r_active && n->cfg->node_version != NODE_V_BLOCKING) {
        int done = 0;
        MPI_Test(&n->r_rreq, &done, MPI_STATUS_IGNORE);
        if (done) {
            MPI_Wait(&n->r_sreq, MPI_STATUS_IGNORE);   // the base station has it already
            on_response(n);
        }
    }
}

// ---- version 3: neighbourhood collective --------------------------------
// Taabish: no request messages at all. Every cycle every node pushes its
// free count to its neighbours in one MPI_Neighbor_allgather on the
// Cartesian communicator. The cost moves from "only when congested" to
// "every node, every cycle", which is the trade off we measured in Task 3.
// The MPI_Allreduce first is how all nodes agree to stop on the SAME cycle:
// a collective that some ranks skip hangs the rest, so the stop must be
// agreed before anyone leaves the cycle loop.
static void collective_cycle(Node *n) {
    double t = now();
    int local = n->term_received, any = 0;
    MPI_Allreduce(&local, &any, 1, MPI_INT, MPI_MAX, n->grid);
    if (any) {
        n->stop_initiating = 1;
        n->stats[S_C(C_BLOCKED)] += now() - t;
        return;
    }
    int raw[MAX_NEIGH] = { -1, -1, -1, -1 };   // PROC_NULL slots stay untouched
    MPI_Neighbor_allgather(&n->free_now, 1, MPI_INT, raw, 1, MPI_INT, n->grid);
    double dt = now() - t;
    stats_add(n->stats, M_COLL, dt);
    n->stats[S_C(C_BLOCKED)] += dt;
    n->stats[S_C(C_MSGS_SENT)] += n->n_nb;
    n->stats[S_C(C_MSGS_RECV)] += n->n_nb;
    n->stats[S_C(C_BYTES_SENT)] += n->n_nb * (double)sizeof(int);
    n->stats[S_C(C_BYTES_RECV)] += n->n_nb * (double)sizeof(int);

    if (n->free_now <= n->cfg->threshold && !n->r_active && n->cooldown_left == 0) {
        n->stats[S_C(C_QUERIES)] += 1;
        int nfree[MAX_NEIGH], j = 0;
        for (int i = 0; i < MAX_NEIGH; i++)
            if (n->nb_raw[i] != MPI_PROC_NULL) nfree[j++] = raw[i];
        decide(n, nfree, dt, n->n_nb, n->n_nb);
    }
}

// ---- one cycle: count the ports and react --------------------------------
static void sample_cycle(Node *n) {
    PortTable *pt = n->pt;
    int free_ports = 0;
    for (int p = 0; p < n->cfg->k; p++) {
        int s;
        #pragma omp atomic read seq_cst
        s = pt->status[p];
        if (!s) free_ports++;
    }
    n->free_now = free_ports;
    n->cycle++;
    n->stats[S_C(C_CYCLES)] += 1;
    if (pt->hist_n < HIST_LEN) {
        pt->hist[pt->hist_n].wall = time(NULL);
        pt->hist[pt->hist_n].sim_sec = n->cycle * n->cfg->sim_sec_per_cycle;
        pt->hist[pt->hist_n].avail = free_ports;
        pt->hist_n++;
    }
    int congested = free_ports <= n->cfg->threshold;
    if (congested) n->stats[S_C(C_CONGESTED)] += 1;

    // Taabish: count the cooldown down BEFORE deciding, not after. In v1 the
    // answer lands inside this same call, in v2 it lands between cycles, so
    // decrementing at the end gave v1 one cycle less cooldown (and one cycle
    // less divert) and about twice the reports, so the versions were not
    // being compared fairly.
    if (n->cooldown_left > 0) n->cooldown_left--;
    // same reason for the divert counter: it must age by one cycle per
    // cycle in every version, whenever the answer that set it arrived
    int d;
    #pragma omp atomic read seq_cst
    d = pt->divert;
    if (d > 0) {
        #pragma omp atomic write seq_cst
        pt->divert = d - 1;
    }

    if (n->cfg->node_version == NODE_V_COLLECTIVE) {
        collective_cycle(n);
    } else if (congested && !n->stop_initiating && !n->q_active && !n->r_active
               && n->cooldown_left == 0) {
        if (n->cfg->node_version == NODE_V_BLOCKING) blocking_exchange(n);
        else start_nb_exchange(n);
    }

}

static int ports_done(Node *n, int tick) {
    for (int p = 0; p < n->cfg->k; p++) {
        int t;
        #pragma omp atomic read seq_cst
        t = n->pt->done_tick[p];
        if (t != tick) return 0;
    }
    return 1;
}

// ---- the comms thread ----------------------------------------------------
static void comm_loop(Node *n) {
    const Config *c = n->cfg;
    double period = c->cycle_ms / 1000.0;
    double next_tick = now() + period;
    int tick = 0, sampled = 0;

    while (!n->shutdown) {
        double t = now();

        // start a new cycle when it is due. Lateness is how far past its
        // scheduled time the cycle really started: in version 1 every
        // blocking wait shows up here as a late cycle.
        if (!n->stop_initiating && t >= next_tick) {
            double late = t - next_tick;
            n->stats[S_C(C_LATE_SUM)] += late;
            if (late > n->stats[S_C(C_LATE_MAX)]) n->stats[S_C(C_LATE_MAX)] = late;
            tick++;
            #pragma omp atomic write seq_cst
            n->pt->tick = tick;
            next_tick += period;
        }
        // all ports have updated for this cycle: count and react
        if (!n->stop_initiating && sampled < tick && ports_done(n, tick)) {
            sampled = tick;
            sample_cycle(n);
        }

        service_incoming(n);
        progress_nb(n);

        if (n->stop_initiating) {
            int stop;
            #pragma omp atomic read seq_cst
            stop = n->pt->stop;
            if (!stop) {
                #pragma omp atomic write seq_cst
                n->pt->stop = 1;            // let the port threads exit
            }
            // phase 1 of the shutdown: once nothing of ours is in flight,
            // tell the base station. We keep answering neighbours until
            // phase 2 (TAG_SHUTDOWN), because a neighbour may still be
            // waiting on a reply from us.
            if (!n->acked && !n->q_active && !n->r_active) {
                double ts = now();
                MPI_Send(&ts, 1, MPI_DOUBLE, n->bs, TAG_ACK, MPI_COMM_WORLD);
                count_send(n, (int)sizeof(double));
                n->acked = 1;
            }
        }
        sleep_us(c->poll_us);
    }
    // every Isend we made must be complete before MPI_Finalize
    MPI_Waitall(POOL, n->pool, MPI_STATUSES_IGNORE);
}

static void write_node_log_header(Node *n) {
    fprintf(n->nlog, "EV charging node %d at (%d,%d), %d ports, threshold %d free, version %d\n",
            n->me, n->x, n->y, n->cfg->k, n->cfg->threshold, n->cfg->node_version);
    fprintf(n->nlog, "neighbours:");
    for (int i = 0; i < n->n_nb; i++) fprintf(n->nlog, " %d(%d,%d)", n->nb[i], n->nb_x[i], n->nb_y[i]);
    fprintf(n->nlog, "\narrival %.2f, departure %.2f per port per cycle\n\n", n->pt->arrive, n->pt->depart);
}

// Table 1 of the spec, rebuilt from the shared array's history. Simulated
// clock: the real start time plus sim_sec_per_cycle seconds per cycle.
static void write_node_log_table(Node *n) {
    PortTable *pt = n->pt;
    if (!pt->hist_n) return;
    time_t start = pt->hist[0].wall;
    fprintf(n->nlog, "\nYear  Month Day Hour Minute Second  Availability\n");
    for (int i = 0; i < pt->hist_n; i++) {
        time_t sim = start + pt->hist[i].sim_sec;
        struct tm tmv;
        localtime_r(&sim, &tmv);
        fprintf(n->nlog, "%4d  %02d    %02d  %02d   %02d     %02d      %d\n",
                tmv.tm_year + 1900, tmv.tm_mon + 1, tmv.tm_mday, tmv.tm_hour,
                tmv.tm_min, tmv.tm_sec, pt->hist[i].avail);
    }
}

void run_charging_node(const Config *cfg, MPI_Comm grid_comm, int bs_rank,
                       MPI_Datatype t_neigh, MPI_Datatype t_report,
                       MPI_Datatype t_resp, double *stats) {
    Node *n = calloc(1, sizeof(Node));
    PortTable *pt = calloc(1, sizeof(PortTable));
    n->cfg = cfg; n->grid = grid_comm; n->bs = bs_rank;
    n->tn = t_neigh; n->tr = t_report; n->ts = t_resp;
    n->stats = stats; n->pt = pt;
    pt->cycle_ms = cfg->cycle_ms;
    MPI_Type_size(t_neigh, &n->sz_neigh);
    MPI_Type_size(t_report, &n->sz_report);
    for (int i = 0; i < POOL; i++) n->pool[i] = MPI_REQUEST_NULL;
    n->r_sreq = n->r_rreq = MPI_REQUEST_NULL;

    // where am I in the grid, and who is around me
    int grid_rank, coords[2];
    MPI_Comm_rank(grid_comm, &grid_rank);
    MPI_Cart_coords(grid_comm, grid_rank, 2, coords);
    n->x = coords[0]; n->y = coords[1];
    MPI_Comm_rank(MPI_COMM_WORLD, &n->me);

    // Taabish: MPI_Cart_shift does the edge handling for us: a missing
    // neighbour comes back as MPI_PROC_NULL. Order matches what
    // MPI_Neighbor_allgather uses: dim 0 (-1, +1), then dim 1 (-1, +1).
    MPI_Cart_shift(grid_comm, 0, 1, &n->nb_raw[0], &n->nb_raw[1]);   // up, down
    MPI_Cart_shift(grid_comm, 1, 1, &n->nb_raw[2], &n->nb_raw[3]);   // left, right

    // grid ranks -> world ranks. Point to point messages go over
    // MPI_COMM_WORLD so the same MPI_Probe sees neighbours AND the base
    // station. MPI_Group_translate_ranks keeps this right even if the grid
    // was ever created with reorder = 1.
    MPI_Group g_grid, g_world;
    MPI_Comm_group(grid_comm, &g_grid);
    MPI_Comm_group(MPI_COMM_WORLD, &g_world);
    for (int i = 0; i < MAX_NEIGH; i++) {
        if (n->nb_raw[i] == MPI_PROC_NULL) continue;
        int w, c2[2];
        MPI_Group_translate_ranks(g_grid, 1, &n->nb_raw[i], g_world, &w);
        MPI_Cart_coords(grid_comm, n->nb_raw[i], 2, c2);
        n->nb[n->n_nb] = w;
        n->nb_x[n->n_nb] = c2[0];
        n->nb_y[n->n_nb] = c2[1];
        n->n_nb++;
    }
    MPI_Group_free(&g_grid);
    MPI_Group_free(&g_world);

    set_load(n);
    if (cfg->node_log_dir[0]) {
        char path[512];
        snprintf(path, sizeof path, "%s/node_%03d.log", cfg->node_log_dir, n->me);
        n->nlog = fopen(path, "w");
        if (n->nlog) write_node_log_header(n);
    }

    // Taabish: k port threads + 1 comms thread. Dynamic teams are switched
    // off so OpenMP cannot quietly hand us fewer threads than ports.
    omp_set_dynamic(0);
    #pragma omp parallel num_threads(cfg->k + 1)
    {
        int tid = omp_get_thread_num();
        if (tid == 0) {
            if (omp_get_num_threads() != cfg->k + 1) {
                fprintf(stderr, "node %d: wanted %d threads, got %d\n", n->me, cfg->k + 1, omp_get_num_threads());
                MPI_Abort(MPI_COMM_WORLD, 2);
            }
            comm_loop(n);           // master thread: all MPI happens here
        } else {
            port_loop(n, tid - 1);  // threads 1..k: one charging port each
        }
    }   // implicit barrier: every port thread has exited before we go on

    if (n->nlog) {
        write_node_log_table(n);
        fclose(n->nlog);
    }
    free(pt);
    free(n);
}
