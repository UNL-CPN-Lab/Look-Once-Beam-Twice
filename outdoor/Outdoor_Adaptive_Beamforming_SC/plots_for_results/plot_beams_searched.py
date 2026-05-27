import pandas as pd
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

# === Example aggregated statistics (mocked from your code outputs) ===
without_guard_means = {"11": 1.02, "14": 1.00, "17": 1.63, "20": 1.31, "23": 3.97}
with_guard_means    = {"11": 1.03, "14": 1.00, "17": 1.05, "20": 1.92, "23": 1.48}

# === Remove thresholds 14 and 20 ===
remove_keys = {"14", "20"}
filtered_with    = {k: v for k, v in with_guard_means.items() if k not in remove_keys}
filtered_without = {k: v for k, v in without_guard_means.items() if k not in remove_keys}

thresholds = list(filtered_with.keys())
x = np.arange(len(thresholds))
width = 0.3

# === Prepare values ===
with_values = list(filtered_with.values())
without_values = list(filtered_without.values())

# === Plotting ===
fig, ax = plt.subplots(figsize=(9, 6))

bars1 = ax.bar(
    x - width/2, with_values, width,
    label='Restricted', color="#ca5b6f",
    edgecolor='white', hatch='/', linewidth=2
)
bars2 = ax.bar(
    x + width/2, without_values, width,
    label='Non-Restricted', color="#e3a69d",
    edgecolor='white', hatch='\\', linewidth=4
)

# === Formatting ===
ax.set_xlabel('SNR Threshold (dB)')
ax.set_ylabel('Avg # Beams Probed')
ax.set_xticks(x)
ax.set_xticklabels(thresholds)
ax.tick_params(axis='y')
ax.legend(frameon=False)
ax.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()

# === Save Plot ===
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(f"beams_Checked.{ext}", format=ext, dpi=600)

plt.show()
