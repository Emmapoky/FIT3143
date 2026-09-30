"""Charts for FIT3143 Applied 2, Task 2 (Ethics of scaling HPC for AI).

Every number below is copied from the cited source. Run: python3 make_charts.py
Output: charts/C1_*.png ... charts/C4_*.png (16:9, white background).
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "charts")
os.makedirs(OUT, exist_ok=True)

# Okabe-Ito colourblind-safe palette
BLUE, ORANGE, GREEN, VERMIL, SKY, PURPLE, YELLOW, GREY = (
    "#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7", "#F0E442", "#666666")

plt.rcParams.update({
    "font.family": "Helvetica",
    "font.size": 16,
    "axes.titlesize": 22,
    "axes.titleweight": "bold",
    "axes.labelsize": 17,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "legend.fontsize": 14,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})
SIZE = (16, 9)


def source(fig, text):
    fig.text(0.01, 0.015, text, fontsize=12, color=GREY, ha="left", va="bottom", wrap=True)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150)
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- C1
# TOP500 and Green500, June 2026 (ISC 2026). Rmax in PFlop/s, power in MW,
# efficiency in GFLOPS/W exactly as listed on top500.org.
def c1():
    systems = [
        # name, Rmax PF, power MW, GFLOPS/W, TOP500 rank, Green500 rank
        ("LineShine\n(China)", 2198.40, 42.220, 52.070, 1, 50),
        ("El Capitan\n(USA)", 1809.00, 29.685, 60.941, 2, 28),
        ("Frontier\n(USA)", 1353.00, 24.607, 54.984, 3, 40),
        ("JUPITER Booster\n(Germany)", 1000.00, 15.794, 63.316, 5, 17),
        ("LUMI\n(Finland)", 379.70, 7.107, 53.428, 11, 45),
        ("KAIROS\n(France)", 3.05, 0.046, 73.282, 445, 1),
    ]
    names = [s[0] for s in systems]
    eff = [s[3] for s in systems]
    power = [s[2] for s in systems]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=SIZE, gridspec_kw={"width_ratios": [1.15, 1]})
    fig.subplots_adjust(left=0.13, right=0.97, top=0.82, bottom=0.17, wspace=0.55)
    cols = [GREY, GREY, VERMIL, GREY, GREEN, BLUE]
    y = range(len(systems))[::-1]
    a1.barh(list(y), eff, color=cols)
    for yi, v in zip(y, eff):
        a1.text(v + 0.8, yi, f"{v:.1f}", va="center", fontsize=15)
    a1.set_yticks(list(y)); a1.set_yticklabels(names)
    a1.set_xlim(0, 85); a1.set_xlabel("Energy efficiency (GFLOPS per watt, HPL)")
    a1.set_title("Efficiency: Frontier and LUMI\nare almost the same", loc="left", fontsize=19)
    a2.barh(list(y), power, color=cols)
    for yi, v in zip(y, power):
        a2.text(v + 0.6, yi, f"{v:.1f} MW" if v >= 1 else f"{v*1000:.0f} kW", va="center", fontsize=15)
    a2.set_yticks(list(y)); a2.set_yticklabels([])
    a2.set_xlim(0, 52); a2.set_xlabel("Power during HPL run (MW)")
    a2.set_title("Power: what the grid\nactually has to supply", loc="left", fontsize=19)
    fig.suptitle("Same MI250X silicon, different planet cost: the grid and heat reuse decide the footprint",
                 x=0.01, ha="left", fontsize=21, fontweight="bold")
    fig.text(0.01, 0.075,
             "Frontier (Tennessee, US grid) and LUMI (Kajaani, Finland, hydropower, waste heat to district heating) share the "
             "HPE Cray EX235a / AMD MI250X / Slingshot-11 design.",
             fontsize=13, color="#222222")
    source(fig, "Source: TOP500 and Green500 lists, June 2026, top500.org [5], [6]. LUMI hydropower and heat reuse: LUMI consortium [8].")
    save(fig, "C1_top500_green500_efficiency.png")


# ---------------------------------------------------------------- C2
# IEA, Energy and AI (April 2025). Global data-centre electricity use, TWh.
# 2024 = 415 (about 1.5% of world electricity); 2030 Base = 945;
# 2025 = 485 (IEA Key Questions on Energy and AI, April 2026).
# 2035: Base about 1200, Lift-Off above 1700, High Efficiency about 970, Headwinds about 700.
def c2():
    fig, ax = plt.subplots(figsize=SIZE)
    fig.subplots_adjust(left=0.08, right=0.80, top=0.90, bottom=0.14)
    ax.plot([2024, 2030, 2035], [415, 945, 1200], "-o", color=BLUE, lw=4, ms=11, label="Base Case")
    ax.plot([2025], [485], "D", color=PURPLE, ms=13, zorder=5, label="2025 actual estimate (IEA, April 2026)")
    ax.annotate("485 TWh in 2025\n(+17% in one year)", (2025, 485), xytext=(2025.6, 330), fontsize=15, color=PURPLE,
                arrowprops=dict(arrowstyle="-", color=PURPLE))
    cases = [("Lift-Off", 1700, VERMIL), ("High Efficiency", 970, GREEN), ("Headwinds", 700, ORANGE)]
    for name, v, c in cases:
        ax.plot([2030, 2035], [945, v], "--o", color=c, lw=3, ms=9, label=f"{name} (2035)")
    ax.annotate("415 TWh\nabout 1.5% of world electricity", (2024, 415), xytext=(2024.1, 150),
                fontsize=15, arrowprops=dict(arrowstyle="-", color=GREY))
    ax.annotate("945 TWh\nmore than double", (2030, 945), xytext=(2027.3, 1180), fontsize=15,
                arrowprops=dict(arrowstyle="-", color=GREY))
    for label, v, c in [("about 1,200 (Base)", 1200, BLUE), ("above 1,700 (Lift-Off)", 1700, VERMIL),
                        ("about 970 (High Efficiency)", 970, GREEN), ("about 700 (Headwinds)", 700, ORANGE)]:
        ax.text(2035.25, v, label, va="center", fontsize=14, color=c, fontweight="bold")
    ax.set_xlim(2023.5, 2035.2); ax.set_ylim(0, 1900)
    ax.set_xticks([2024, 2026, 2028, 2030, 2032, 2035])
    ax.set_ylabel("Data-centre electricity use (TWh per year)")
    ax.legend(loc="upper left", frameon=False)
    ax.set_title("Data-centre electricity could roughly triple by 2035; efficiency is the swing factor",
                 loc="left", x=-0.06)
    fig.text(0.08, 0.075, "Accelerated (GPU) servers: +30% per year in the Base Case, vs +9% for conventional servers.",
             fontsize=14, color="#222222")
    source(fig, "Source: IEA, Energy and AI, April 2025 [1]; 2025 point: IEA, Key Questions on Energy and AI, April 2026 [4]. Only the years published by the IEA are plotted; lines join published points.")
    save(fig, "C2_iea_datacentre_electricity.png")


# ---------------------------------------------------------------- C4
# Our proposed checklist: SCALE responsibly. Diagram only, no data.
def c4():
    fig = plt.figure(figsize=SIZE)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 16); ax.set_ylim(0, 9); ax.axis("off")
    ax.text(0.5, 8.35, "SCALE: a five-step checklist for responsible HPC", fontsize=28, fontweight="bold")
    ax.text(0.5, 7.75, "Each step maps to a mechanism a cluster already has, and a number you can report.",
            fontsize=17, color=GREY)
    evidence = [
        "Evidence: Llama 3 405B ran at\n38 to 43% MFU on up to 16K\nH100s. A 150 W cap gave 87.7%\nof the energy for 108.5% of\nthe time.",
        "Evidence: jobs with weekly\nslack cut CO2 by up to about\n19%. Google fleet: 1 to 2% less\npower in peak-carbon hours.",
        "Evidence: Frontier PUE about\n1.03 vs 1.54 industry average.\nEU sites of 500 kW or more\nmust now report.",
        "Evidence: Malaysia PDPA 2024\ncross-border rules. EU AI Act\nasks for training compute\nand energy.",
        "Evidence: Gadi demand was\nnearly 3x its national\nallocation. 85% of surveyed\nacademics had no cloud budget.",
    ]
    steps = [
        ("S", "Size right", BLUE,
         "Stop adding nodes once\nparallel efficiency drops\n(Amdahl, strong scaling).\nMixed precision and\npower caps.",
         "Metric: speedup and\nefficiency per job"),
        ("C", "Carbon-aware\nscheduling", GREEN,
         "Shift deferrable jobs to\nlow-carbon hours or sites.\nDeadline-aware queues.",
         "Metric: gCO2e per\nkWh at run time"),
        ("A", "Account every\njoule", ORANGE,
         "Per-job energy in the\nscheduler (e.g. Slurm\nConsumedEnergy).\nPublish PUE, WUE, CUE.",
         "Metric: kWh, litres\nand kgCO2e per job"),
        ("L", "Lawful, local\ndata", PURPLE,
         "Data residency by site.\nFederated training when\ndata cannot move.\nModel and data cards.",
         "Metric: audit trail\nper dataset"),
        ("E", "Equitable\naccess", VERMIL,
         "Fair-share queues and\nnational allocations\n(NCI, EuroHPC, NAIRR).\nOpen models and data.",
         "Metric: share of hours\nto small groups"),
    ]
    w, gap, x0 = 2.8, 0.25, 0.5
    for i, (letter, title, c, body, metric) in enumerate(steps):
        x = x0 + i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 0.9), w, 6.4, boxstyle="round,pad=0.02,rounding_size=0.18",
                                    fc="white", ec=c, lw=3))
        ax.add_patch(FancyBboxPatch((x, 5.55), w, 1.75, boxstyle="round,pad=0.02,rounding_size=0.18",
                                    fc=c, ec=c, lw=3))
        ax.text(x + 0.25, 6.42, letter, fontsize=46, fontweight="bold", color="white", va="center")
        ax.text(x + 1.0, 6.42, title, fontsize=17, fontweight="bold", color="white", va="center")
        ax.text(x + 0.2, 5.25, body, fontsize=14.5, va="top", linespacing=1.35)
        ax.text(x + 0.2, 3.35, evidence[i], fontsize=12.5, va="top", color="#333333", linespacing=1.3, style="italic")
        ax.text(x + 0.2, 1.2, metric, fontsize=14, va="bottom", color=c, fontweight="bold")
    source(fig, "Our synthesis. Evidence: S [22], [66]; C [64], [65]; A [7], [70], [54]; L [26], [53]; E [43], [40]. "
                "Tools: Slurm [60], [61], [71]. Principles: Green AI [57]; UNESCO [47]; OECD [48]; Malaysia AIGE [50].")
    save(fig, "C4_SCALE_framework.png")


# ---------------------------------------------------------------- C3
# Epoch AI, "Data on AI Models" (CSV downloaded 30 Sep 2026, archived in charts/).
# Notable models with a training-compute estimate, split by organisation type.
def c3():
    import csv
    from datetime import date
    path = os.path.join(OUT, "epoch_all_ai_models_2026-09-30.csv")
    rows = [r for r in csv.DictReader(open(path, encoding="utf-8"))
            if r["Notability criteria"].strip() and r["Training compute (FLOP)"].strip()
            and r["Publication date"][:4].isdigit() and int(r["Publication date"][:4]) >= 2012]

    def sector(r):
        s = {t.strip() for t in r["Organization categorization"].split(",")}
        return "Industry" if s == {"Industry"} else "Academia" if s == {"Academia"} else "Mixed"

    def yr(r):
        d = date.fromisoformat(r["Publication date"][:10])
        return d.year + (d.timetuple().tm_yday-1) / 365.25

    fig, ax = plt.subplots(figsize=SIZE)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.90, bottom=0.14)
    style = {"Industry": (BLUE, "Industry only"), "Academia": (ORANGE, "Academia only"),
             "Mixed": ("#BBBBBB", "Collaborations and other")}
    for key in ["Mixed", "Industry", "Academia"]:
        pts = [(yr(r), float(r["Training compute (FLOP)"])) for r in rows if sector(r) == key]
        c, lab = style[key]
        ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=46 if key != "Mixed" else 26, color=c,
                   alpha=0.85 if key != "Mixed" else 0.6, edgecolor="white", lw=0.5,
                   label=f"{lab} ({len(pts)})", zorder=3 if key != "Mixed" else 2)
    ax.set_yscale("log")
    ax.set_ylim(1e15, 1e28); ax.set_xlim(2012, 2027)
    ax.set_ylabel("Training compute (FLOP, log scale)")
    # Reference line: the EU threshold and 100 days of Frontier land in the same place.
    frontier_100d = 1.353e18 * 86400 * 100  # = 1.17e25 FLOP
    ax.axhline(1e25, color=VERMIL, ls="--", lw=2.2, zorder=1)
    ax.text(2012.2, 2.2e25, "10^25 FLOP: EU AI Act systemic-risk presumption", color=VERMIL, fontsize=14.5)
    ax.text(2012.2, 1.6e24, "about the same as Frontier at full HPL speed (1.353 EFLOP/s, FP64) for 100 days",
            color=VERMIL, fontsize=13.5)
    # label: text position given in (year, FLOP)
    labels = {"AlexNet": ("AlexNet", 2012.6, 2e18),
              "Transformer": ("Transformer", 2016.6, 4e19),
              "BERT-Large": ("BERT-Large", 2017.3, 3e21),
              "GPT-3 175B (davinci)": ("GPT-3", 2019.0, 4e23),
              "GPT-4 (Mar 2023)": ("GPT-4 (est.)", 2020.9, 1.2e26),
              "Llama 3.1-405B": ("Llama 3.1 405B", 2022.0, 3e26),
              "Grok 3": ("Grok 3 (est.)", 2022.9, 1.5e27),
              "GPT-6 Astra": ("Largest estimate,\n2026: about 10^27", 2024.2, 6e27),
              "GLM-130B": ("GLM-130B, top\nacademic model (2022)", 2022.9, 2e21)}
    for r in rows:
        if r["Model"] in labels:
            text, tx, ty = labels[r["Model"]]
            ax.annotate(text, (yr(r), float(r["Training compute (FLOP)"])), xytext=(tx, ty), fontsize=13.5,
                        arrowprops=dict(arrowstyle="-", color="#333333", lw=1), zorder=5,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    ax.legend(loc="lower right", frameon=False, markerscale=1.6)
    ax.set_title("Frontier training compute grows about 5x a year; the top academic model is about 3,000x smaller",
                 loc="left", x=-0.07, fontsize=21, pad=18)
    source(fig, "Source: Epoch AI, Data on AI Models (notable models with a compute estimate, downloaded 30 Sep 2026) [38]; "
                "growth rate: Epoch AI Trends [39]. Reference line: EU AI Act Art. 51 [53]; Frontier Rmax, TOP500 June 2026 [5].")
    save(fig, "C3_epoch_training_compute.png")


if __name__ == "__main__":
    c1(); c2(); c3(); c4()
