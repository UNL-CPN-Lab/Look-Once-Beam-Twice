import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.lines import Line2D

# -----------------------------
# Data
# -----------------------------
data = [
    ("VIBE-MA", "Q80", 0.0, 0.13, 1.8),
    ("VIBE-MA", "Q80", 0.25, 0.22, 0.3),
    ("VIBE-MA", "Q80", 1.00, 0.22, 2.7),
    ("VIBE-MA", "Q80", 4.00, 0.22, 5.4),
    ("VIBE-MA", "Q90", 0.0, 0.13, 1.8),
    ("VIBE-MA", "Q90", 0.25, 0.22, 3.5),
    ("VIBE-MA", "Q90", 1.00, 0.23, 4.5),
    ("VIBE-MA", "Q90", 4.00, 0.26, 6.0),
    ("VIBE-MA", "Q95", 0.0, 0.54, 5.4), #update this
    ("VIBE-MA", "Q95", 0.25, 0.25, 1.8),
    ("VIBE-MA", "Q95", 1.00, 0.35, 3.6),
    ("VIBE-MA", "Q95", 4.00, 0.50, 11.1),

    ("5G NR", "Q80", 0.00, 7.90, 14.88),
    ("5G NR", "Q80", 0.25, 7.90, 54.54),
    ("5G NR", "Q80", 1.00, 7.90, 90.90),
    ("5G NR", "Q80", 4.00, 7.87, 100.0),
    ("5G NR", "Q90", 0.00, 7.90, 16.36),
    ("5G NR", "Q90", 0.25, 7.90, 54.54),
    ("5G NR", "Q90", 1.00, 7.90, 92.72),
    ("5G NR", "Q90", 4.00, 7.87, 100.0),
    ("5G NR", "Q95", 0.00, 7.90, 23.63),
    ("5G NR", "Q95", 0.25, 7.90, 61.81),
    ("5G NR", "Q95", 1.00, 7.90, 96.36),
    ("5G NR", "Q95", 4.00, 7.88, 100.0),
]

df = pd.DataFrame(data, columns=[
    "Algorithm", "Threshold", "RotorSpeed",
    "BeamAlignmentTime", "OutageProbability"
])

# -----------------------------
# Styling
# -----------------------------
thresholds = ["Q80", "Q90", "Q95"]

markers = {"Q80": "o", "Q90": "s", "Q95": "^"}

vibema_colors = {
    "Q80": "#249ea0",
    "Q90": "#008083",
    "Q95": "#005f60",
}

nr_colors = {
    "Q95": "#fd5901",
    "Q90": "#f78104",
    "Q80": "#faab36",
}

q_legend = {
    "Q80": r"$Q_{0.8}$",
    "Q90": r"$Q_{0.9}$",
    "Q95": r"$Q_{0.95}$",
}



# =============================
# Figure 1: Beam Alignment Time
# =============================
fig_tb, ax_tb = plt.subplots(figsize=(6.5, 4.5))

for th in thresholds:
    for algo, colors in [("VIBE-MA", vibema_colors), ("5G NR", nr_colors)]:
        sub = df[(df["Algorithm"] == algo) & (df["Threshold"] == th)]
        ax_tb.plot(
            sub["RotorSpeed"],
            sub["BeamAlignmentTime"],
            linestyle=":",
            marker=markers[th],
            linewidth=2.5,
            color=colors[th]
        )

ax_tb.set_ylim(-0.5, 9)
ax_tb.set_ylabel(r"$T_b$ (s)", fontsize=18)
ax_tb.set_xlabel("Rotation Speed (degrees/s)", fontsize=18)
ax_tb.set_xticks([0, 0.25, 1, 4])
ax_tb.set_xticklabels(["0", " ", "1", "4"])
ax_tb.tick_params(labelsize=16)
ax_tb.grid(True, linestyle="--", linewidth=0.5)

legend_handles_tb = []

legend_handles_tb.append(Line2D([], [], linestyle="None", label="VIBE-MA"))
for th in thresholds:
    legend_handles_tb.append(
        Line2D([0], [0], color=vibema_colors[th],
               linestyle=":", marker=markers[th],
               lw=2.5, label=f"{q_legend[th]}")
    )

legend_handles_tb.append(Line2D([], [], linestyle="None", label="5G NR"))
for th in thresholds:
    legend_handles_tb.append(
        Line2D([0], [0], color=nr_colors[th],
               linestyle=":", marker=markers[th],
               lw=2.5, label=f"{q_legend[th]}")
    )


ax_tb.legend(
    handles=legend_handles_tb,
    ncol=1,
    fontsize=16,
    frameon=False,
    loc="center right",
    handlelength=2.6,
    columnspacing=1.6,
    labelspacing=0.4
)

plt.tight_layout()
plt.savefig("beam_alignment_time.pdf", dpi=800, bbox_inches="tight")
plt.savefig("beam_alignment_time.png", dpi=800, bbox_inches="tight")

# =============================
# Figure 2: Outage Probability
# =============================
fig_out, ax_out = plt.subplots(figsize=(6.5, 4.5))

for th in thresholds:
    for algo, colors in [("VIBE-MA", vibema_colors), ("5G NR", nr_colors)]:
        sub = df[(df["Algorithm"] == algo) & (df["Threshold"] == th)]
        ax_out.plot(
            sub["RotorSpeed"],
            sub["OutageProbability"],
            linestyle="-",
            marker=markers[th],
            linewidth=2.5,
            color=colors[th],
            alpha=0.85
        )

ax_out.set_ylim(-1.5, 105)
ax_out.set_ylabel("Outage Probability (%)", fontsize=18)
ax_out.set_xlabel("Rotation Speed (degrees/s)", fontsize=18)
ax_out.set_xticks([0, 0.25, 1, 4])
ax_out.set_xticklabels(["0", " ", "1", "4"])
ax_out.tick_params(labelsize=16)
ax_out.grid(True, linestyle="--", linewidth=0.5)

legend_handles_out = []

legend_handles_out.append(Line2D([], [], linestyle="None", label="VIBE-MA"))
for th in thresholds:
    legend_handles_out.append(
        Line2D([0], [0], color=vibema_colors[th],
               linestyle="-", marker=markers[th],
               lw=2.5, label=f"{q_legend[th]}")
    )

legend_handles_out.append(Line2D([], [], linestyle="None", label="5G NR"))
for th in thresholds:
    legend_handles_out.append(
        Line2D([0], [0], color=nr_colors[th],
               linestyle="-", marker=markers[th],
               lw=2.5, label=f"{q_legend[th]}")
    )


ax_out.legend(
    handles=legend_handles_out,
    ncol=1,
    fontsize=16,
    frameon=False,
    loc="center right",
    handlelength=2.6,
    columnspacing=1.6,
    labelspacing=0.4
)

plt.tight_layout()
plt.savefig("beam_alignment_outage.pdf", dpi=800, bbox_inches="tight")
plt.savefig("beam_alignment_outage.png", dpi=800, bbox_inches="tight")

# plt.show()
