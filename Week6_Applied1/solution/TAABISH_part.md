# Applied #1 - Taabish's part (Task 2 messages, Task 3, conclusion; slides 7-12, last 3:30)

====================================================================
SECTION A - WHAT YOU WRITE INTO THE SUBMISSION DOCUMENT
====================================================================

--------------------------------------------------------------------
TASK 2 - ARCHITECTURE DESIGN, PART 2: MESSAGE PASSING (your section)
--------------------------------------------------------------------

Write this message table:

| # | Message              | From -> To                  | MPI mechanism                                  | Payload                                   |
|---|----------------------|-----------------------------|------------------------------------------------|-------------------------------------------|
| 1 | NEIGHBOUR_QUERY      | node -> up/down/left/right  | MPI_Isend (non-blocking), tag 102              | requesting node's rank + coords (~64 B)   |
| 2 | NEIGHBOUR_REPLY      | neighbour -> requesting node| MPI_Isend, tag 103                             | free ports, in-use ports (~256 B)         |
| 3 | BS_ALERT             | node -> base station        | MPI_Send of a struct built with MPI_Type_create_struct (or MPI_Pack), tag 100 | coords, ports in use, neighbour data, timestamp (~512 B) |
| 4 | BS_REDIRECT          | base station -> node        | MPI_Send, tag 101                              | coords of the closest available node (~128 B) |
| 5 | HEARTBEAT (optional) | node -> base station, periodic | MPI_Isend, tag 104                          | alive flag + free ports (~64 B)           |

Then write the interaction paragraph:

"The interaction cycle is: each node's port threads update the shared port array;
once per cycle the node checks utilisation against the threshold. If exceeded, it
sends NEIGHBOUR_QUERY to its adjacent nodes using non-blocking MPI_Isend and posts
matching MPI_Irecv calls. Non-blocking calls matter here because two adjacent nodes
can exceed the threshold simultaneously and query each other; with blocking sends
both could wait on the other and deadlock. Each node services incoming queries while
waiting for its own replies. If every neighbour's reply is also over the threshold,
the node packs an alert struct with MPI_Type_create_struct and sends BS_ALERT to the
base station. The base station logs the alert, searches its table for the closest
node with free ports by Manhattan distance, and answers with BS_REDIRECT. The node
then directs future simulated vehicles to that target."

DIAGRAM 2 (you draw this one). UML communication/sequence diagram with four
lifelines: Node(1,1) . Neighbours(4x) . BaseStation . Node(2,1, the redirect target).
Arrows in order:
  1. Node(1,1) -> Neighbours: NEIGHBOUR_QUERY (MPI_Isend, tag 102)
  2. Neighbours -> Node(1,1): NEIGHBOUR_REPLY (tag 103)
  3. Node(1,1) -> BaseStation: BS_ALERT (packed struct, tag 100)   [only if all over threshold]
  4. BaseStation -> BaseStation: log + findClosestAvailable()
  5. BaseStation -> Node(1,1): BS_REDIRECT (tag 101, target = (2,1))
Label the guard on arrow 3: "[all neighbour replies over threshold]".

--------------------------------------------------------------------
TASK 3 - COMMUNICATION ANALYSIS (your section)
--------------------------------------------------------------------

State the model first:

"Per link, delay t = L / B + t_other, where L is the message size in bits, B is the
1 Gbps link bandwidth given in the spec, and t_other covers queuing, processing and
propagation. We use the course convention 1 MB = 1,000,000 bytes and
1 Gbps = 10^9 bits per second."

(a) Scaling with the number of charging nodes n:

"Neighbour query and reply: each node communicates with at most four fixed
neighbours regardless of grid size, so the delay per message is O(1) in n. Total
network traffic grows O(n), but it travels on disjoint mesh links in parallel, so
no individual link's delay grows.

Base station alert and redirect: all n nodes share the base station's single link,
which is the star hub. In the worst case (many nodes alerting in the same window)
the messages serialise on that link, so worst-case delay grows O(n). This is the
message type that limits scalability, and the graph shows it climbing linearly
while the neighbour curve stays flat."

(b) Would more base stations reduce transmission delay?

"Yes, for the alert path. Partitioning n nodes across b base stations cuts each
station's worst-case queue to about n/b messages, so delay scales O(n/b): going from
one to two stations roughly halves the worst case. But the gain diminishes: the
stations must synchronise a shared availability table to still find the true
closest free node, and that inter-station synchronisation traffic grows with b. It
does not help the neighbour messages at all, which are already O(1). So extra base
stations relieve the hub bottleneck at the cost of a new synchronisation overhead,
which behaves like the serial fraction of the design."

Graphs (already generated, regenerate after changing sizes):
  python3 transmission_delay_model.py
  -> graphs/delay_vs_nodes.png          (one curve per message type, delay vs n)
  -> graphs/delay_vs_base_stations.png  (alert path delay vs b, 100 nodes)
Put both in the slides and the doc, axes labelled in seconds and counts.
If you want HD-level extra graphs, add sweeps for ports per node and alert
frequency (edit SIZES / add a loop in the script, or do it by hand in Excel).

--------------------------------------------------------------------
CONCLUSION / LIMITATIONS / FUTURE WORK (your section, required by the rubric)
--------------------------------------------------------------------

"Limitations: MPI guarantees reliable in-order delivery, but real wireless links
drop packets, so a real deployment would need acknowledgements and timeouts. Our
base station is centralised; it remains a single point of failure unless
replicated, and replication adds synchronisation cost as shown in Task 3. Port
simulation uses a fixed threshold rather than learned demand.

Future work: fault injection (killing a node and observing rerouting), replicated
base stations with a consistency protocol, and calibrating arrival rates with real
EV charging data."

====================================================================
SECTION B - YOUR SPOKEN SCRIPT (3:30 to 7:00, rehearse to under 3:30)
====================================================================

[Slide 7, message table + communication diagram, 3:30-4:40]
"Thanks Erwyna. Our design uses four message types, plus an optional heartbeat.
When a node passes its threshold it sends neighbour queries with non-blocking
MPI_Isend. That's deliberate: two adjacent nodes can cross their thresholds at the
same time and query each other, and with blocking sends both could wait forever.
Non-blocking calls let each node service incoming queries while waiting for its own
replies. If every neighbour is also saturated, the node packs an alert struct with
MPI_Type_create_struct and sends it to the base station, which logs it, runs a
Manhattan-distance search for the closest free node, and replies with a redirect.
You can see the full cycle in this communication diagram."

[Slide 8, delay model, 4:40-5:10]
"For Task 3 we model each link as L over B plus other delays, on the 1 gigabit
links from the spec. The question is how each message type scales."

[Slide 9, delay vs nodes graph, 5:10-5:50]
"Neighbour messages are constant time in the number of nodes, because a mesh caps
every node at four neighbours; that's the flat line. Alerts all converge on the
base station's single link, so their worst-case delay grows linearly with node
count; that's the climbing line. The star hub is the scalability limit of this
design."

[Slide 10, delay vs base stations graph, 5:50-6:20]
"Adding base stations divides that load: with b stations each handles about n over
b nodes, so the worst case drops like this curve. But returns diminish, because the
stations now have to synchronise a shared availability table to still find the true
closest free node, and that synchronisation grows with the number of stations. It
behaves like the serial fraction of the design."

[Slide 11, conclusion, 6:20-6:50]
"To conclude: a 2-D mesh with a star overlay matches the physical WSN, our MPI
architecture combines message passing between machines with threads inside each
node, and the analysis shows the base station link is the bottleneck, relieved but
not removed by adding stations. Limitations: MPI's reliable delivery is optimistic
for real wireless, and the base station is a single point of failure. Future work:
fault injection and replicated base stations. Thank you, happy to take questions."

[Slide 12: "Questions?"; appendix slides after this, clearly labelled APPENDIX]

====================================================================
SECTION C - YOUR Q&A PREP (asked individually, no AI allowed)
====================================================================

Q: Why non-blocking communication for the neighbour queries?
A: "Two adjacent nodes can cross their thresholds simultaneously and query each
other. With blocking sends both can block waiting for the other's receive, which is
a deadlock. MPI_Isend and MPI_Irecv let each node keep servicing incoming queries
while its own are in flight."

Q: Why MPI_Type_create_struct for the alert instead of separate sends?
A: "The alert carries mixed types: coordinates, counts, a timestamp. One derived
datatype sends it in a single message, so we pay one latency cost instead of
several, and the struct arrives atomically."

Q: Why does the alert delay grow linearly but neighbour delay stays flat?
A: "Neighbour degree is capped at four whatever the grid size, so per-message delay
is constant. Alerts share the base station's one link, so in the worst case n
messages serialise there, which is order n."

Q: Would ten base stations make it ten times faster?
A: "On the alert path the worst case drops to about n over ten, but the stations
must synchronise the availability table to answer 'closest free node' correctly, so
the real speedup is less. It's the same shape as Amdahl's law: the synchronisation
is the serial fraction."

Q: Did you consider POSIX threads or OpenMP as well as MPI? (spec asks this verbatim)
A: "Yes: charging ports are threads inside each node process. Port state never
leaves the node, so shared memory with a mutex is cheaper than messages, and the
threads use the spare cores on each machine while MPI links the machines."

====================================================================
CHECKLIST BEFORE CLASS
====================================================================
- [ ] Your sections written into the shared doc + slides 7-12 built
- [ ] Communication diagram drawn, guard condition labelled
- [ ] Both graphs regenerated with the final parameters and pasted in
- [ ] Rehearsed your 3:30 twice, with a timer; full team run under 7:00
- [ ] Names, IDs, Monash emails on every file
