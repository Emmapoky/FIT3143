"""
FIT3143 Applied #1, Task 3 (extension).

Student Name: Taabish Farooq Bhat 
Student ID: 35473932
Student Email: ttaa0006@student.monash.edu

Model (identical to the deck):
    Td_single_hop = T_overhead + (message_size_bits / bandwidth_bps)
    T_overhead    = 20 us      (propagation + switch/NIC + MPI stack)
    bandwidth     = 1 Gbps     (given in the spec)

Two growing factors are layered on top of that:

1. Ports per node, K.
   The BS_ALERT struct carries a fixed header (coords, rank, timestamp,
   free-port count = 32 B) plus a one-byte occupancy entry per port, so
   L(K) = 32 + K bytes. Bigger K therefore lengthens the alert message.

2. EV arrival / charging frequency, expressed as the alert rate f per node
   per second. All alerts converge on the single base station, which drains
   them serially via MPI_ANY_SOURCE. Following the deck's convention of
   "+5 us per extra simultaneous alert", the expected number of alerts
   queued behind a given one at N nodes is M = N * f * W, with W = 1 ms the
   observation window, giving

       Td_alert(K, f) = T_overhead + L(K)*8 / B + M * 5 us

Run:  python3 make_extra_factor_graph.py
Out:  delay_vs_ports_and_frequency.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

T_OVERHEAD_US = 20.0        # microseconds, as stated on slide 8
BANDWIDTH_BPS = 1e9         # 1 Gbps, from the spec
QUEUE_COST_US = 5.0         # microseconds per extra simultaneous alert
N_NODES = 100               # same 100-node deployment used on slide 9
WINDOW_S = 1e-3             # 1 ms observation window

ports = np.arange(4, 65, 2)                      # 4 to 64 ports per node
alert_rates = np.arange(0, 1001, 25)             # 0 to 1000 alerts per node per second


def alert_delay_us(k, f):
    """Total alert-path delay in microseconds for K ports and alert rate f."""
    payload_bits = (32 + k) * 8                  # L(K) = 32 + K bytes
    tx_us = payload_bits / BANDWIDTH_BPS * 1e6   # seconds -> microseconds
    queued = N_NODES * f * WINDOW_S              # expected simultaneous alerts
    return T_OVERHEAD_US + tx_us + queued * QUEUE_COST_US


fig, (axL, axR) = plt.subplots(1, 2, figsize=(12, 4.8), dpi=160)

# Panel A: grow the ports per node, hold demand fixed.
for f, label in [(50, "Low demand (50 alerts/node/s)"),
                 (200, "Typical demand (200 alerts/node/s)"),
                 (800, "Peak demand (800 alerts/node/s)")]:
    axL.plot(ports, [alert_delay_us(k, f) for k in ports],
             marker="o", markersize=3, linewidth=1.8, label=label)

axL.set_xlabel("Charging ports per node (K)")
axL.set_ylabel("Alert-path delay (µs)")
axL.set_title("(a) More ports per node\ndelay is flat: message size is not the constraint",
              fontsize=10)
axL.grid(True, alpha=0.3)
axL.legend(frameon=True, fontsize=8)
axL.set_ylim(0, 460)

# Panel B: grow EV demand (charging frequency), hold ports fixed
for k, style in [(4, "-"), (16, "--"), (64, ":")]:
    axR.plot(alert_rates, [alert_delay_us(k, f) for f in alert_rates],
             style, linewidth=2, label=f"K = {k} ports per node")

axR.set_xlabel("Alert rate per node (alerts/s), driven by EV arrivals")
axR.set_ylabel("Alert-path delay (µs)")
axR.set_title("(b) More EVs / higher charging frequency\ndelay grows linearly: queueing is the constraint",
              fontsize=10)
axR.grid(True, alpha=0.3)
axR.legend(frameon=True, fontsize=8)

fig.suptitle("Task 3 (extension): alert delay vs other growing factors  "
             "(N = 100 nodes, 1 base station, 1 Gbps links)",
             fontsize=11.5, y=1.02)
fig.tight_layout()
fig.savefig("delay_vs_ports_and_frequency.png", bbox_inches="tight")
print("wrote delay_vs_ports_and_frequency.png")

# Printed so the numbers can be quoted directly in Q&A
print("\nSanity values (microseconds):")
for f in (50, 200, 800):
    print(f"  f={f:>3} alerts/node/s:  K=4 -> {alert_delay_us(4, f):8.1f}   "
          f"K=64 -> {alert_delay_us(64, f):8.1f}   "
          f"(K adds only {alert_delay_us(64, f) - alert_delay_us(4, f):.1f} us)")
