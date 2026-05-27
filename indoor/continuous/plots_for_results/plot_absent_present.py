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

# === Prepare data for plotting ===
labels = []
absent_values, present_values = [], []

for q in quantiles:
    for s_idx, s in enumerate(speeds):
        labels.append(f"{s}\n{q}")
        absent_values.append(outage_data["Absent"][q][s_idx])
        present_values.append(outage_data["Present"][q][s_idx])

# === Plotting ===
fig, ax = plt.subplots(figsize=(10, 8))
bar_width = 0.3
indices = np.arange(len(labels))

bars1 = ax.bar(indices - bar_width/2, absent_values, bar_width, label="Offset Absent", hatch="///", edgecolor="white")
bars2 = ax.bar(indices + bar_width/2, present_values, bar_width, label="Offset Present", hatch="\\\\\\", edgecolor="white")

# === Formatting ===
ax.set_ylabel("Outage Probability (%)")
ax.set_xticks(indices)
ax.set_xticklabels(labels, rotation=45, ha="right")
ax.legend()


plt.tight_layout()
plt.savefig("abs_pres.png", bbox_inches='tight')
plt.savefig("abs_pres.svg", bbox_inches='tight')
plt.savefig("abs_pres..eps", bbox_inches='tight')
plt.savefig("abs_pres..pdf", bbox_inches='tight')  # Tight PDF
