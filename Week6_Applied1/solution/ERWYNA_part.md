# Applied #1 - Erwyna's part (Tasks 1 + Task 2 structure, slides 1-7, first 3:30 of the talk)

====================================================================
SECTION A - WHAT YOU WRITE INTO THE SUBMISSION DOCUMENT
====================================================================

--------------------------------------------------------------------
TASK 1 - NETWORK TOPOLOGY (your section)
--------------------------------------------------------------------

Write this comparison table (one slide + one page in the doc):

| Topology        | Diameter (n nodes) | Links      | Fault tolerance                          | Scalability                     | Suitable for the WSN simulator? |
|-----------------|--------------------|------------|------------------------------------------|---------------------------------|---------------------------------|
| Line            | n - 1              | n - 1      | None: any single link cut splits it      | Poor, delay grows linearly      | No                              |
| Ring            | floor(n/2)         | n          | Survives one cut (degrades to a line)    | Weak, delay still grows with n  | No                              |
| Star            | 2                  | n - 1      | Hub is a single point of failure         | Hub link becomes the bottleneck | Partly: matches node-to-base-station traffic only |
| Binary tree     | about 2 log2(n)    | n - 1      | None: any cut disconnects a subtree      | Good depth growth, no redundancy| No                              |
| Fully connected | 1                  | n(n-1)/2   | Excellent                                | Link count explodes quadratically| No: unrealistic for wireless radios |
| 2-D mesh (grid) | about 2(sqrt(n)-1) | about 2n   | Multiple redundant paths between nodes   | Grows incrementally, degree capped at 4 | Yes: matches the spec exactly |
| Hypercube       | log2(n)            | (n/2)log2(n)| Good                                    | Needs n = 2^k nodes             | No: wrong shape for a city grid |

Then write the decision paragraph (adapt wording to your voice):

"We choose a hybrid topology: a 2-D mesh (grid) between the charging nodes, with a
star overlay connecting every node to the base station. The specification places the
EV charging nodes in a Cartesian grid where each node communicates only with its
immediate adjacent neighbours, which is exactly the connectivity a 2-D mesh provides,
and it is realistic for a wireless sensor network because radio range limits each
node to nearby nodes. The mesh gives redundant paths, so the simulated network
survives a single node or link failure, unlike a line or tree. The base station is a
logging and coordination server that every node must reach directly, which is star
connectivity. A fully connected topology would minimise diameter but needs n(n-1)/2
links, which no real WSN radio deployment could provide, and a ring or line cannot
scale because worst-case path length grows linearly with the number of nodes."

--------------------------------------------------------------------
TASK 2 - ARCHITECTURE DESIGN, PART 1: STRUCTURE (your section)
--------------------------------------------------------------------

Write this text:

"The simulator runs as one MPI program on a cluster of multi-core machines. With m
charging nodes arranged as a sqrt(m) x sqrt(m) grid, the program launches m + 1 MPI
processes: ranks 0 to m-1 are charging nodes, and the last rank is the base station.

Base station (1 MPI process): holds a table of every node's coordinates and port
availability, receives alert messages, logs them, computes the closest available
node by Manhattan distance on the grid coordinates, and replies with a redirect
message telling the origin node where to send future vehicles.

Charging nodes (m MPI processes): the node ranks form a 2-D non-periodic Cartesian
communicator created with MPI_Cart_create, so every node obtains its up, down, left
and right neighbour ranks with MPI_Cart_shift. Each node simulates its own port
occupancy, checks it against the threshold each cycle, queries neighbours when the
threshold is exceeded, and alerts the base station when the whole neighbourhood is
saturated.

Charging ports (threads inside each node process): each node process spawns one
POSIX thread (or OpenMP thread) per charging port. The threads update a shared
port-state array protected by a mutex. This deliberately combines both parallelism
models: shared-memory parallelism (threads) exploits the cores inside each machine,
and message-passing parallelism (MPI) connects processes across machines, which is
how software is deployed on a cluster of multi-core machines.

Machines, cores and bandwidth: for a 3 x 3 grid the program needs 10 processes.
Two 8-core machines are sufficient (5 processes per machine, leaving cores free for
the port threads). Traffic is small: an alert is a packed struct under 512 bytes, so
even if all 9 nodes alerted every second the base station link carries about
9 x 512 x 8 = 37 kbit/s, far below a 1 Gbps link. 1 Gbps commodity Ethernet is
therefore ample, and the fabric, not the message sizes, would only become a concern
at thousands of nodes (analysed in Task 3)."

DIAGRAM 1 (you draw this one - draw.io or PowerPoint shapes, NOT hand drawn).
UML class diagram, three boxes:

  BaseStation
    - rank: int (= m)
    - nodeTable: array of NodeStatus {coords, freePorts, lastSeen}
    + receiveAlert()
    + findClosestAvailable(origin): coords   (Manhattan distance search)
    + sendRedirect(target)

  ChargingNode
    - rank: int, coords: (row, col)
    - neighbours: {up, down, left, right}    (from MPI_Cart_shift)
    - ports: ChargingPort[K]
    - threshold: float (e.g. 0.8)
    + checkThreshold()
    + queryNeighbours()      (non-blocking MPI_Isend / MPI_Irecv)
    + alertBaseStation()     (struct via MPI_Type_create_struct)

  ChargingPort
    - inUse: bool
    + simulate()             (runs on its own POSIX/OpenMP thread, mutex on state)

  Relations: BaseStation 1 --- m ChargingNode (MPI messages, star overlay)
             ChargingNode 1 --- K ChargingPort (composition, shared memory)
             ChargingNode --- ChargingNode (adjacent only, MPI messages, mesh)

====================================================================================================================
SECTION B - SPEAKING NOTES (bullets, rewritten 2026-09-02)
====================================================================

Deck is 15 slides. Slide 15 is blank, see the checklist.
Erwyna slides 1-6. Taabish slides 7-13. Slide 14 is Questions.

Target 6:50, hard ceiling 7:00. These are BULLETS, not a script: say each
point in your own words and stop. Written short on purpose because we both
speak slowly. Do not read the slide bullets aloud as well, that is what
makes teams overrun.

The same bullets are in the Canva speaker notes, so present from there.

--------------------------------------------------------------------
ERWYNA - slides 1 to 6  (0:00 - 2:55)
--------------------------------------------------------------------

[1] Title  0:00-0:12
  - Names, unit, topic
  - MPI simulator for a wireless sensor network of EV charging nodes
  - I take Tasks 1 and 2, Taabish takes Task 3

[2] Context  0:12-0:35
  - Grid of charging nodes, each with ports
  - Over threshold, node queries its 4 neighbours
  - All neighbours saturated, node alerts the base station
  - Base station finds the closest free node and redirects

[3] Topology table  0:35-1:20
  - Compared 7 Week 5 topologies: diameter, links, fault tolerance, scalability
  - Line and binary tree: one cut splits the network
  - Ring: survives one cut, but path length grows linearly
  - Fully connected: best diameter, but n(n-1)/2 links, no radio can build that
  - Star: diameter 2, but the hub is a single point of failure and a bottleneck

[4] Our choice  1:20-1:50
  - Hybrid: 2-D mesh between nodes, star overlay to the base station
  - Spec puts nodes in a Cartesian grid, adjacent only. That is a mesh
  - Same shape as real radio range
  - Redundant paths, degree capped at 4, so it scales incrementally

[5] MPI architecture + class diagram  1:50-2:30
  - 1 charging node = 1 MPI process. Base station is its own rank
  - MPI_Cart_create builds the grid, MPI_Cart_shift gives the 4 neighbours
  - Edge nodes get MPI_PROC_NULL, so no special case at the borders
  - Base station holds the global table, Manhattan distance search
  - Each port is a POSIX thread, mutex on shared state
  - Threads inside a machine, MPI between machines

[6] Deployment  2:30-2:55
  - 3x3 grid plus base station = 10 processes
  - 2 x 8-core machines, cores spare for the port threads
  - Alert struct under 512 B, about 37 kbit/s worst case
  - 1 Gbps Ethernet is far more than we need
  - Hand over to Taabish

--------------------------------------------------------------------
TAABISH - slides 7 to 13  (2:55 - 6:50)
--------------------------------------------------------------------

[7] Message passing + communication diagram  2:55-3:30
  - 4 message types plus an optional heartbeat
  - Neighbour query and reply use MPI_Isend, non-blocking
  - Why: two adjacent nodes can query each other in the same cycle.
    Blocking would deadlock
  - Alert is a packed struct, MPI_Type_create_struct
  - Redirect uses MPI_Send. Blocking is safe: many-to-one is not a cycle

[8] Delay model  3:30-4:00
  - Td = T overhead + message bits / bandwidth
  - T overhead about 20 us: propagation, switch and NIC, MPI stack
  - All 4 message types are 32 to 64 B, so the size term is under 1 us
  - Every single hop is about 20 us
  - Point: overhead dominates, not payload

[9] Delay vs charging nodes  4:00-4:40
  - Neighbour traffic is O(1), flat. Degree capped at 4, more nodes adds
    no neighbours
  - Alerts all converge on one base station, serialised by MPI_ANY_SOURCE
  - Queue delay is O(N), about +5 us per extra simultaneous alert
  - At 100 nodes, over 500 us
  - The mesh scales, the star hub does not

[10] Delay vs base stations  4:40-5:20
  - Per-message time does not improve: no B term in the formula, still 20 us
  - Queueing does improve: N/B alerts per station instead of all N
  - Sharp early gain, then diminishing returns
  - Cost: split tables must synchronise to answer closest free node
  - That sync is a serial fraction, so it bounds the speed-up

[11] Extension: other growing factors  5:20-5:55
  - More ports per node: delay is flat. 4 to 64 ports adds 60 B, about 0.5 us
  - More EVs / higher charging frequency: linear, 20 us up to over 500 us
  - The three port curves sit on top of each other, which confirms it
  - Queueing, not payload, is the constraint

[12] Conclusion and limitations  5:55-6:25
  - Mesh keeps neighbour traffic O(1) at any network size
  - Hybrid MPI plus threads: cheap port updates in shared memory, real
    messages on the network
  - One bottleneck: the single base station, O(N)
  - Limits: single point of failure; fixed 80 percent threshold; regular
    grid assumed; latency constants are assumptions, not measurements

[13] Future work  6:25-6:50
  - Replicate and partition the base station, measure the sync overhead
    we predicted
  - Fault injection to prove the mesh survives failures
  - Real EV demand traces instead of synthetic occupancy
  - Acks and timeouts to port onto lossy wireless
  - Thank you, we will take questions

--------------------------------------------------------------------
DELIVERY
--------------------------------------------------------------------
- Slides 5, 7, 9, 10 and 11 carry a diagram or a graph. Point at it while
  you talk. The timings already allow for that.
- The rubric rewards parallel computing terminology over general computing
  terms. Keep the specific words: rank, communicator, non-blocking,
  serialise, serial fraction, O(1), O(N), shared memory versus message
  passing.

====================
SECTION C - YOUR Q&A PREP (asked individually, no AI allowed)
====================================================================

Q: Why a mesh and not just a star, since everything goes to the base station anyway?
A: "Neighbour queries stay local. If every query went through the base station its
link would serialise all traffic and become the bottleneck and single point of
failure. The mesh keeps neighbour traffic on disjoint links in parallel."

Q: Why MPI_Cart_create instead of computing neighbour ranks yourself?
A: "It gives us the neighbour ranks for any grid size for free through
MPI_Cart_shift, returns MPI_PROC_NULL at the edges so border nodes need no special
casing, and MPI can reorder ranks to match the physical machine layout."

Q: Why are ports threads and not MPI processes?
A: "Port state is only ever read and written inside one node, so shared memory with
a mutex is cheaper than message passing. One process per port would multiply process
count and message overhead for data that never leaves the node."

Q: What is your threshold and why?
A: "We used 80 percent in-use as the default; it's a tunable parameter of the
simulation, and the right value in reality depends on how fast ports turn over."

Q: Is this realistic for a real WSN? Could it be ported off the cluster?
A: "Largely yes: one process per physical node and neighbour-only links mirror a
real deployment. The gap is that MPI assumes reliable delivery, while real wireless
drops packets, so a real port would need acknowledgements and timeouts. That's in
our limitations."

====================================================================
CHECKLIST BEFORE CLASS
====================================================================
Deck is 15 slides as of 2026-09-02. Slides 1-6 Erwyna, 7-13 Taabish,
14 Questions, 15 blank.

Done:
- [x] Title slide typo, floor(n/2) render fix, capybara off the 3b graph
- [x] Slide 11 Task 3 extension (graph now placed) and slide 13 Future work
- [x] Slide 7 attribution is Taabish (he fixed it himself)
- [x] All speaker notes rewritten as short bullets, timed, in Canva
- [x] Both UML diagrams (class on 5, communication on 7), all three graphs
- [x] Submission folder built at ../submission/

Still on you:
- [ ] SLIDE 15 IS BLANK. Ask Taabish whether it is deliberate. If not,
      delete it before exporting, a blank trailing slide looks careless.
- [ ] Class diagram on slide 5 is small. Check it reads from the back.
- [ ] Rehearse twice with a timer. Target 6:50, hard ceiling 7:00.
- [ ] AI declaration: Taabish adds Section 3, plus the slide-edit line
      quoted at the bottom of submission/README_SUBMISSION.txt
- [ ] Export the deck to PDF into ../submission/, then zip that folder
