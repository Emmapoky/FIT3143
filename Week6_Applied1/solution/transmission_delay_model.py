# Applied #1 Task 3 prep: transmission delay graphs.
# Adjust parameters to match
# your own architecture before using any output in the submission
#
# Model: t = L / B + t_other per link (course convention: 1 MB = 1e6 bytes, 1 Gbps = 1e9 bps)
# Message types follow the guide: neighbour query/reply (O(1) in n),
# base-station alert (O(n) serialised at the star hub), redirect reply.

import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

B = 1e9            # link bandwidth, bits per second (1 Gbps)
T_OTHER = 0.004    # queuing + processing + propagation per link, seconds

SIZES = {          # message payload sizes in bytes; tune to your design
    "neighbour_query": 64,
    "neighbour_reply": 256,
    "bs_alert_struct": 512,
    "bs_redirect": 128,
}

def link_delay(size_bytes, bandwidth=B, t_other=T_OTHER):
    return (size_bytes * 8) / bandwidth + t_other

def delay_vs_nodes(msg, size, nodes_range):
    """Worst-case delay per message type as the grid grows to n charging nodes."""
    ys = []
    for n in nodes_range:
        if msg.startswith("neighbour"):
            # degree capped at 4 whatever the grid size -> O(1)
            ys.append(link_delay(size))
        else:
            # all n nodes share one base-station link -> worst case n serialised sends
            ys.append(n * link_delay(size))
    return ys

def delay_vs_base_stations(msg, size, n_nodes, bs_range):
    """Alert-path delay when n_nodes are partitioned across b base stations."""
    return [math.ceil(n_nodes / b) * link_delay(size) for b in bs_range]

def main():
    nodes = list(range(4, 401, 4))
    bstations = list(range(1, 21))

    # Graph set 1: delay vs number of charging nodes, one line per message type
    plt.figure(figsize=(8, 5))
    for msg, size in SIZES.items():
        plt.plot(nodes, delay_vs_nodes(msg, size, nodes), label=msg)
    plt.xlabel("Number of charging nodes")
    plt.ylabel("Worst-case delay (s)")
    plt.title("Transmission delay vs number of charging nodes (1 Gbps)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig("graphs/delay_vs_nodes.png", dpi=150, bbox_inches="tight")

    # Graph set 2: alert-path delay vs number of base stations (fixed 100 nodes)
    plt.figure(figsize=(8, 5))
    for msg in ("bs_alert_struct", "bs_redirect"):
        plt.plot(bstations, delay_vs_base_stations(msg, SIZES[msg], 100, bstations), label=msg)
    plt.xlabel("Number of base stations (100 charging nodes)")
    plt.ylabel("Worst-case delay (s)")
    plt.title("Transmission delay vs number of base stations")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig("graphs/delay_vs_base_stations.png", dpi=150, bbox_inches="tight")

    print("Wrote graphs/delay_vs_nodes.png and graphs/delay_vs_base_stations.png")

if __name__ == "__main__":
    import os
    os.makedirs("graphs", exist_ok=True)
    main()
