# Applied #1 - Erwyna's part (Tasks 1 + Task 2 structure, slides 1-7, first 3:30 of the talk)

NOTE: This content is AI-assisted prep (Claude, 2026-08-28). The spec allows this ONLY
with an AI declaration and full prompt records uploaded as PDF. Rewrite in your own
words where you can, and make sure you can defend every line verbally - Q&A is 40%
and AI tools are banned in the room.

Submission is via MOODLE BEFORE THE START OF CLASS: slides (pptx + PDF), this content
as the design documentation, the two graphs, AI declaration + prompt records.
Put both names, student IDs and Monash emails on the title slide and every file.

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

====================================================================
SECTION B - YOUR SPOKEN SCRIPT (0:00 to 3:30, rehearse to under 3:30)
====================================================================

[Slide 1, title, 0:00-0:15]
"Hi, we're Erwyna and Taabish, and this is our design for the EV charging wireless
sensor network simulator. I'll cover the topology choice and the structure of our
MPI architecture, and Taabish will cover the message passing and the communication
analysis."

[Slide 2, problem recap, 0:15-0:40]
"The system we're simulating is a grid of EV charging nodes. Each node has charging
ports; when a node passes its utilisation threshold it asks its neighbours, and if
the whole neighbourhood is saturated it alerts a base station, which finds the
closest free node and redirects incoming vehicles."

[Slide 3, topology table, 0:40-1:40]
"For Task 1 we compared seven topologies from Week 5 on diameter, link count, fault
tolerance and scalability. Line and tree fail immediately on fault tolerance: cut
any link and the network splits. A ring survives one cut but its path length grows
linearly, so it doesn't scale. Fully connected has perfect fault tolerance but needs
n squared links, which no wireless deployment can provide. A star matches the
base-station traffic but makes the hub a single point of failure for everything."

[Slide 4, chosen topology, 1:40-2:10]
"So we chose a hybrid: a 2-D mesh between charging nodes, because the spec places
nodes in a Cartesian grid talking only to adjacent neighbours, which is also what
real radio range gives you, plus a star overlay to the base station for logging and
redirection. The mesh gives redundant paths if a node dies, and its degree is capped
at four, so it scales incrementally."

[Slide 5, architecture overview + class diagram, 2:10-3:00]
"For Task 2, each charging node is one MPI process. The node ranks form a Cartesian
communicator built with MPI_Cart_create, so every process finds its four neighbours
with MPI_Cart_shift instead of us hard-coding a mapping. The base station is a
dedicated rank holding the global availability table and doing a Manhattan-distance
search for the closest free node. Inside each node process, every charging port is a
POSIX thread updating shared port state under a mutex, so we combine shared-memory
parallelism inside each multi-core machine with message passing between machines."

[Slide 6, deployment numbers, 3:00-3:30]
"A 3 by 3 grid needs ten processes; two 8-core machines cover that with cores to
spare for the port threads. An alert struct is under 512 bytes, so worst-case
base-station traffic is tens of kilobits per second, and 1 Gbps Ethernet is ample.
Taabish will now take you through the messages themselves and how the delays scale."

====================================================================
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
- [ ] Your sections written into the shared doc + slides 1-6 built
- [ ] Class diagram drawn (legible from the back of the room)
- [ ] Rehearsed your 3:30 twice, with a timer
- [ ] Names, IDs, Monash emails on the title slide and every file
- [ ] AI declaration + prompt-record PDFs exported and in the Moodle zip
