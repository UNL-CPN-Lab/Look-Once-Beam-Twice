import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.legend_handler import HandlerTuple

# -----------------------------
# Data
# -----------------------------
data = [
    ("VIBE-MA", "Q80", 0.25, 0.22, 0.3),
    ("VIBE-MA", "Q80", 1.00, 0.22, 2.7),
    ("VIBE-MA", "Q80", 4.00, 0.22, 5.4),
    ("VIBE-MA", "Q90", 0.25, 0.22, 3.5),
    ("VIBE-MA", "Q90", 1.00, 0.23, 4.5),
    ("VIBE-MA", "Q90", 4.00, 0.26, 6.0),
    ("VIBE-MA", "Q95", 0.25, 0.25, 1.8),
    ("VIBE-MA", "Q95", 1.00, 0.35, 3.6),
    ("VIBE-MA", "Q95", 4.00, 0.50, 11.1),

    ("5G NR", "Q80", 0.25, 7.90, 54.54),
    ("5G NR", "Q80", 1.00, 7.90, 90.90),
    ("5G NR", "Q80", 4.00, 7.87, 100.0),
    ("5G NR", "Q90", 0.25, 7.90, 54.54),
    ("5G NR", "Q90", 1.00, 7.90, 92.72),
    ("5G NR", "Q90", 4.00, 7.87, 100.0),
    ("5G NR", "Q95", 0.25, 7.90, 61.81),
    ("5G NR", "Q95", 1.00, 7.90, 96.36),
    ("5G NR", "Q95", 4.00, 7.88, 100.0),
]

df = pd.DataFrame(
    data,
    columns=[
        "Algorithm",
        "Threshold",
        "RotorSpeed",
        "BeamAlignmentTime",
        "OutageProbability",
    ],
)

# -----------------------------
# X-axis setup (Quantiles)
# -----------------------------
quantiles = ["Q80", "Q90", "Q95"]
x_pos = np.arange(len(quantiles))

speed_offsets = {0.25: -0.18, 1.00: 0.0, 4.00: 0.18}
speed_markers = {0.25: "o", 1.00: "s", 4.00: "^"}
speed_labels = {0.25: "0.25 deg/s", 1.00: "1 deg/s", 4.00: "4 deg/s"}

# Colors (algorithm-specific)
vibema_color = "#008083"
nr_color = "#f78104"

q_legend = {
    "Q80": r"$Q_{0.8}$",
    "Q90": r"$Q_{0.9}$",
    "Q95": r"$Q_{0.95}$",
}

# -----------------------------
# Figure & axes
# -----------------------------
fig, (ax_top, ax_bot) = plt.subplots(
    2, 1,
    figsize=(6, 5.6),
    sharex=True,
    gridspec_kw={"hspace": 0.08, "height_ratios": [1, 1.2]}
)

ax_top_r = ax_top.twinx()
ax_bot_r = ax_bot.twinx()

# -----------------------------
# Plotting
# -----------------------------
for speed in speed_offsets:

    # ---- Bottom: VIBE-MA ----
    sub = df[(df["Algorithm"] == "VIBE-MA") & (df["RotorSpeed"] == speed)]
    sub = sub.set_index("Threshold").loc[quantiles]

    ax_bot.plot(
        x_pos + speed_offsets[speed],
        sub["BeamAlignmentTime"],
        linestyle=":", marker=speed_markers[speed],
        linewidth=2.5, color=vibema_color
    )

    ax_bot_r.plot(
        x_pos + speed_offsets[speed],
        sub["OutageProbability"],
        linestyle="-", marker=speed_markers[speed],
        linewidth=2.5, color=vibema_color, alpha=0.85
    )

    # ---- Top: 5G NR ----
    sub = df[(df["Algorithm"] == "5G NR") & (df["RotorSpeed"] == speed)]
    sub = sub.set_index("Threshold").loc[quantiles]

    ax_top.plot(
        x_pos + speed_offsets[speed],
        sub["BeamAlignmentTime"],
        linestyle=":", marker=speed_markers[speed],
        linewidth=2.5, color=nr_color
    )

    ax_top_r.plot(
        x_pos + speed_offsets[speed],
        sub["OutageProbability"],
        linestyle="-", marker=speed_markers[speed],
        linewidth=2.5, color=nr_color, alpha=0.85
    )

# -----------------------------
# Axes formatting
# -----------------------------
ax_top.set_ylim(4, 9)
ax_top_r.set_ylim(50, 105)
ax_bot.set_ylim(0, 3)
ax_bot_r.set_ylim(0, 14)

ax_top.set_yticks(np.arange(4, 10, 1))
ax_top_r.set_yticks(np.arange(50, 106, 15))
ax_bot.set_yticks(np.arange(0, 3, 1))
ax_bot_r.set_yticks(np.arange(0, 15, 5))

for ax in [ax_top, ax_top_r, ax_bot, ax_bot_r]:
    ax.tick_params(labelsize=17)

# -----------------------------
# X-axis labels
# -----------------------------
ax_bot.set_xticks(x_pos)
ax_bot.set_xticklabels([q_legend[q] for q in quantiles], fontsize=18)
ax_bot.set_xlabel("Quantile Threshold", fontsize=18)

# -----------------------------
# Grid
# -----------------------------
for ax in [ax_top, ax_bot]:
    ax.grid(True, linestyle="--", linewidth=0.5)

# -----------------------------
# Shared Y labels
# -----------------------------
fig.text(0.03, 0.5, r"$T_b$ (s)", va="center", rotation="vertical", fontsize=18)
fig.text(0.97, 0.5, "Outage Probability (%)", va="center", rotation="vertical", fontsize=18)

# -----------------------------
# Speed legend
# -----------------------------
speed_handles = [
    Line2D([0], [0], marker=speed_markers[s], linestyle="None",
           color="black", label=speed_labels[s])
    for s in speed_markers
]

ax_bot.legend(
    handles=speed_handles,
    loc="upper left",
    fontsize=13,
    frameon=False,
    title="Rotation Speed"
)

# -----------------------------
# Save
# -----------------------------
plt.tight_layout(rect=[0.06, 0.04, 0.94, 0.96])
plt.savefig("beam_alignment_vs_quantile.pdf", dpi=800, bbox_inches="tight")
plt.savefig("beam_alignment_vs_quantile.png", dpi=800, bbox_inches="tight")
# plt.show()
