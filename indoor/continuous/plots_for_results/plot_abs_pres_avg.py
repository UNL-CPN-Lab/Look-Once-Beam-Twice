import matplotlib.pyplot as plt
import numpy as np

# === Matplotlib Config ===
plt.rcParams.update({
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'text.usetex': False,
    'font.size': 26,
    'mathtext.fontset': 'dejavusans',
    'font.family': 'DejaVu Sans'
})

# === Given Data ===
quantiles = ["Q80", "Q90", "Q95"]
speeds = ["0.25", "1", "4"]

# Outage data (in %)
outage_data = {
    "Absent": {
        "Q80": [2.4, 2.7, 5.6],
        "Q90": [1.8, 3.0, 6.8],
        "Q95": [4.0, 3.0, 11.5]
    },
    "Present": {
        "Q80": [0.3, 2.7, 5.4],
        "Q90": [3.5, 4.5, 6.0],
        "Q95": [1.8, 3.6, 11.1]
    }
}

# === Compute average outage per speed (across quantiles) ===
avg_absent_speed = [np.mean([outage_data["Absent"][q][i] for q in quantiles]) for i in range(len(speeds))]
avg_present_speed = [np.mean([outage_data["Present"][q][i] for q in quantiles]) for i in range(len(speeds))]

# === Prepare labels and positions ===
labels_speed = speeds
indices = np.arange(len(labels_speed))
bar_width = 0.3

# === Plotting ===
fig, ax = plt.subplots(figsize=(9, 6))

bars1 = ax.bar(indices - bar_width/2, avg_absent_speed, bar_width,
               label="w/o Offset Tracking", color="#90a955", hatch="/", edgecolor="white")

bars2 = ax.bar(indices + bar_width/2, avg_present_speed, bar_width,
               label="w/ Offset Tracking", color="#4f772d", hatch="\\", edgecolor="white")

# === Formatting ===
ax.set_ylabel("Avg. Outage (%)")
ax.set_xlabel("Rotation Speed (°/s)")   # <-- Added x-axis label
ax.set_xticks(indices)
ax.set_xticklabels([f"{s}°/s" for s in labels_speed])
ax.legend( frameon=False)
ax.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()

# === Save Figures ===
plt.savefig("avg_outage_per_speed.png", bbox_inches='tight')
plt.savefig("avg_outage_per_speed.svg", bbox_inches='tight')
plt.savefig("avg_outage_per_speed.eps", bbox_inches='tight')
plt.savefig("avg_outage_per_speed.pdf", bbox_inches='tight')

plt.show()
