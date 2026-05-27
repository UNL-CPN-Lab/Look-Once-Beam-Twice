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
        # --- 5G NR, rotation speed = 0 (wait-for-best-beam case) ---
    # ("5G NR", "Q80", 0.00, 7.90, 14.88),
    # ("5G NR", "Q90", 0.00, 7.90, 16.36),
    # ("5G NR", "Q95", 0.00, 7.90, 23.63),

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

# -----------------------------
# Figure & axes
# -----------------------------
fig, (ax_top, ax_bot) = plt.subplots(
    2, 1, figsize=(6,9.5), sharex=True,
    gridspec_kw={"hspace": 0.08}
)

ax_top_r = ax_top.twinx()
ax_bot_r = ax_bot.twinx()

# -----------------------------
# Plotting
# -----------------------------
for th in thresholds:

    # ---- Bottom: VIBE-MA ----
    sub = df[(df["Algorithm"] == "VIBE-MA") & (df["Threshold"] == th)]

    ax_bot.plot(
        sub["RotorSpeed"], sub["BeamAlignmentTime"],
        linestyle=":", marker=markers[th], linewidth=2.5,
        color=vibema_colors[th]
    )

    ax_bot_r.plot(
        sub["RotorSpeed"], sub["OutageProbability"],
        linestyle="-", marker=markers[th], linewidth=2.5,
        color=vibema_colors[th], alpha=0.85
    )

    # ---- Top: 5G NR ----
    sub = df[(df["Algorithm"] == "5G NR") & (df["Threshold"] == th)]

    ax_top.plot(
        sub["RotorSpeed"], sub["BeamAlignmentTime"],
        linestyle=":", marker=markers[th], linewidth=2.5,
        color=nr_colors[th]
    )

    ax_top_r.plot(
        sub["RotorSpeed"], sub["OutageProbability"],
        linestyle="-", marker=markers[th], linewidth=2.5,
        color=nr_colors[th], alpha=0.85
    )

# -----------------------------
# Axis limits & ticks
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
    ax.tick_params(labelsize=18)

# -----------------------------
# X-axis
# -----------------------------
rotor_speeds = [0.25, 1, 4]
ax_bot.set_xticks(rotor_speeds)
ax_bot.set_xticklabels(["0.25", "1", "4"])
ax_bot.set_xlabel("Rotation Speed (degrees/s)", fontsize=18)

# -----------------------------
# Grid
# -----------------------------
for ax in [ax_top, ax_bot]:
    ax.set_xscale("linear")
    ax.minorticks_off()
    ax.grid(True, which="major", linestyle="--", linewidth=0.5)

# -----------------------------
# Shared Y-axis labels
# -----------------------------
fig.text(0.04, 0.5, r"$T_b$ (s)",
         va="center", rotation="vertical", fontsize=18)

fig.text(0.96, 0.5, "Outage Probability (%)",
         va="center", rotation="vertical", fontsize=18)

# -----------------------------
# Legends: grouped solid + dotted per quantile
# -----------------------------
def quantile_handles(color, marker):
    return (
        Line2D([0], [0], linestyle=":", color=color,
               marker=marker, linewidth=2.5),
        Line2D([0], [0], linestyle="-", color=color,
               marker=marker, linewidth=2.5),
    )




top_handles = [quantile_handles(nr_colors[th], markers[th]) for th in thresholds]
bot_handles = [quantile_handles(vibema_colors[th], markers[th]) for th in thresholds]

LEGEND_HANDLE_LENGTH = 4   # try 3.0–4.0

leg_top = ax_top.legend(
    top_handles,
    [q_legend[th] for th in thresholds],
    handler_map={tuple: HandlerTuple(ndivide=2, pad=0.4)},
    fontsize=15,
    loc="lower right",
    handlelength=4.0,
    title="5G NR\n$T_b\\quad\\mathrm{Outage}$",
    title_fontsize=15,
    frameon=True
)

leg_top.get_title().set_ha("left")

# White background, no border
leg_top.get_frame().set_facecolor("white")
leg_top.get_frame().set_alpha(1.0)
leg_top.get_frame().set_edgecolor("none")



leg_bot = ax_bot.legend(
    bot_handles,
    [q_legend[th] for th in thresholds],
    handler_map={tuple: HandlerTuple(ndivide=2, pad=0.4)},
    fontsize=15,
    loc="upper left",
    handlelength=4.0,
    title="VIBE-MA\n$T_b\\quad\\mathrm{Outage}$",
    title_fontsize=15,
    frameon=True
)

leg_bot.get_title().set_ha("left")

# White background, no border
leg_bot.get_frame().set_facecolor("white")
leg_bot.get_frame().set_alpha(1.0)
leg_bot.get_frame().set_edgecolor("none")




# -----------------------------
# Save
# -----------------------------
plt.tight_layout(rect=[0.06, 0.03, 0.94, 0.98])
plt.savefig("beam_alignment_outage_vs_speed_split.pdf", dpi=800, bbox_inches="tight")
plt.savefig("beam_alignment_outage_vs_speed_split.png", dpi=800, bbox_inches="tight")
# plt.show()
