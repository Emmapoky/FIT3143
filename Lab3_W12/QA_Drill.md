# FIT3143 Lab 3 Q&A drill (private, not for submission)

Q&A is 40% of the mark. Each answer: **verdict, then mechanism, then our
number or our line of code**. Parallel computing terms, no analogies. Never
contradict the deck. Say each answer out loud in under 25 seconds.

Numbers marked [N] come from `results/summary_*.csv`; check them against
the deck before class.

---

## Task 1 (Taabish first, Erwyna must know it too)

**1. Why one MPI process per node but threads for the ports?**
Port state never leaves the node, so it belongs in shared memory: a thread
writes one int, no message. Nodes only share data by message passing, which
is what MPI models, and they could sit on different machines (CAAS).

**2. Show me where you use the virtual topology.**
`main.c`: `MPI_Comm_split` takes the base station out, `MPI_Cart_create`
makes a rows x cols grid, periods 0,0 (no wrap: an edge station has no
neighbour past the edge), reorder 0. `node.c`: `MPI_Cart_shift` on dim 0 and
dim 1 gives up/down/left/right; edges come back `MPI_PROC_NULL`. Version 3
also runs `MPI_Neighbor_allgather` on that Cartesian communicator.

**3. Why does the base station call MPI_Comm_split if it is not in the grid?**
Because it is a collective on `MPI_COMM_WORLD`: every rank must call it or
the others block forever. It passes `MPI_UNDEFINED` and gets `MPI_COMM_NULL`.

**4. Two threads share the array. Where is your lock?**
There is none on purpose. One writer per field: port p only writes
`status[p]` and `done_tick[p]`; only thread 0 writes `tick`, `stop`,
`divert`. Writes and reads are `#pragma omp atomic ... seq_cst`, and the
port writes status before done_tick, so once thread 0 sees done_tick == tick
it sees that cycle's status. No race, no lock contention.

**5. Why MPI_THREAD_FUNNELED?**
Only thread 0 (the OpenMP master) calls MPI. FUNNELED is the minimum level
that allows that; MULTIPLE would add internal locking to every MPI call.

**6. Blocking vs nonblocking: which did you pick and why?**
Version 2, nonblocking. Version 1 blocks the comms thread inside MPI_Probe,
so the node runs no cycles while it waits ([N] ms blocked per node per run,
v2 is 0). Version 1's round trip is actually a little shorter because a
blocked probe wakes instantly while v2 polls every 200 us: that is a poll
interval cost, and graph 7 shows we can buy it back with CPU.

**7. Could version 1 deadlock?**
The wait loop answers neighbour requests while it waits, so two full
neighbours querying each other do not deadlock. The remaining risk is
`MPI_Send` itself: the standard allows it to block until received. Our
40 B messages go eagerly in Open MPI, but that is an implementation
detail, which is one reason v2 uses MPI_Isend.

**8. What does version 3 trade?**
No request at congestion time: every node already has its neighbours'
counts from `MPI_Neighbor_allgather`. But it sends 4 messages per node per
cycle whether anyone is full or not ([N]x the messages of v2), and the
collective forces every node into lockstep. The stop needs an
`MPI_Allreduce` first so all nodes leave the cycle loop on the same cycle.

**9. What is in your report and why one message?**
Detection time (date to ms), reporter rank and (x,y), its free ports, k,
threshold, every neighbour's rank, coordinates and free ports, messages and
bytes exchanged with the neighbours, the exchange round trip, report count,
version, send stamp. One `MPI_Type_create_struct` datatype (176 B), so one
call and no pack/unpack copy.

**10. How do you know your simulation is correct?**
Low availability test cases: `hotspot` (busy middle) exercises both the
local redirect and the report; `saturated` produced all three base station
answers (8 candidates / 43 none nearby / 12 none anywhere); 1x1, 1x8, 8x1;
ASan and UBSan clean; leaks only from MPI_Init_thread.

## Task 2 (Erwyna first)

**11. Walk me through the base station decision.**
Node 0 reports, neighbours 1 and 3. If both 1 and 3 reported inside the
window W, their reports already covered 2, 4, 6 as full: answer "no nodes
nearby". Otherwise take the 2 hop ring {2, 4, 6}, drop any node known full
inside W, and send ALL that remain (tied distance). If none, widen to 3
hops, 4 hops. Ring walk is O(d), not a grid scan.

**12. Why three versions, and which won?**
v1 probe + blocking send + line buffered log: a serial queue, report delay
grows linearly with nodes ([N] ms at 64). v2 one Irecv(ANY_SOURCE): fast to
36 nodes, then bursts back up in MPI's unexpected message queue, worst case
[N] ms at 64. v3 persistent receive per node + MPI_Testsome + persistent
answers + 1 MB log buffer: flat, [N] ms at 64, and [N] us per report.

**13. What does MPI_Testsome give you over MPI_Test?**
One call returns every completed receive out of the n posted ones, so a
burst of reports is drained in one progress pass, and each node has its own
pre-posted buffer, so nothing lands in the unexpected queue.

**14. Why a persistent request?**
The receive's arguments never change (same buffer, source, tag), so
`MPI_Recv_init` sets the matching up once and `MPI_Start` re-arms it,
saving the set up cost on every report.

**15. How is the shutdown graceful?**
Two phases: TERMINATE stops new work; each node ACKs only when it has no
query or report in flight and keeps answering neighbours; after all n ACKs
nothing can be moving, so SHUTDOWN. Then the stats MPI_Gather, persistent
requests cancelled, waited and freed, datatypes and communicators freed,
log flushed and closed, MPI_Finalize.

**16. What does the log contain?**
Header with the configuration; per report: arrival time, detection time,
reporter state, every neighbour's state, neighbour messages and bytes,
one way delay, window check result, every candidate, processing time; at
the end a per node table and a summary: simulation time, alerts, answers by
type, total messages and bytes, delay per message type, blocking, shutdown.

## Task 3 (Erwyna 3a, Taabish 3b)

**17. How did you measure communication delay?**
Every message carries its send stamp. One way delay = receive time minus
that stamp; round trips are measured on one process's clock. Means over 3
seeds, 32 grid sizes and 32 line sizes.

**18. Why not MPI_Wtime?**
On our Open MPI, MPI_WTIME_IS_GLOBAL = 0: each process's MPI_Wtime has its
own zero, so we first got negative one way delays. The system real time
clock is shared by every process on one machine. Across CAAS nodes it is
only NTP synced, so there the round trips are the trustworthy numbers.

**19. How does delay scale with grid size? (3a)**
Neighbour messages stay roughly flat: a node has at most 4 neighbours
whatever the grid size, so per node work is O(1). Base station messages
grow, because all reports converge on one rank: O(N) arrivals into one
serial receiver. Past 13 nodes the laptop also has more processes than
cores, so part of the growth is oversubscription, which CAAS removes.

**20. Line topology? (3b)**
Degree drops from 4 to 2, so a neighbour exchange is 2 messages not 4 and
its round trip is a bit shorter. But with only 2 neighbours a full node
finds both neighbours full more often, so lines send more reports per node
to the base station. Diameter is N - 1 instead of about 2 sqrt(N), so the
base station's 2 hop candidates are less likely to exist, and far ones
are further away.

**21. Biggest limitation?**
The single base station is a serial bottleneck and a single point of
failure; on one laptop, large grids are oversubscribed; MPI assumes
reliable delivery while real radios drop packets.

**22. Future work?**
Partition the base station (one per region) and measure the sync cost;
run the full sweep on CAAS across nodes; acks and timeouts for lossy links;
adaptive polling (spin briefly, then sleep).
