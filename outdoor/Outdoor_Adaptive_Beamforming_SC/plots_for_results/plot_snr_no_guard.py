import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.ticker import MaxNLocator

# === Settings ===
experiment_folder = "mavg_Results"
base_filename = "sc_outdoor_jul11_gain9db_12db_16m"
linewidth_val = 3
markersize_val = 6

# === Thresholds and pastel colors for t1–t5 ===
thresholds_info = {
    "t1": (11, (0.75, 0.6, 0.85)),  # pastel_purple
    "t2": (14, (0.6, 0.75, 0.95)),  # pastel_blue
    "t3": (17, (0.6, 0.8, 0.6)),    # pastel_green
    "t4": (20, (1.0, 0.75, 0.5)),   # pastel_orange
    "t5": (23, (1.0, 0.5, 0.5))     # pastel_red
}

def darken_color(color, factor=0.8):
    return tuple(min(max(c * factor, 0.0), 1.0) for c in color)

# === Create Plot ===
plt.figure(figsize=(8, 6))

# === Plot each threshold result ===
for label, (threshold_db, pastel_color) in thresholds_info.items():
    file_path = os.path.join(experiment_folder, f"{base_filename}_{label}", f"results_{base_filename}_{label}.csv")
    
    if not os.path.exists(file_path):
        print(f"Missing: {file_path}")
        continue
    
    df = pd.read_csv(file_path)
    df = df.dropna(subset=["SNR (dB)"])
    df = df[df["SNR (dB)"] >= 0]
    
    snr = df["SNR (dB)"].values
    x_vals = np.arange(len(snr))
    
    dark_color = darken_color(pastel_color)
    label_str = f"{threshold_db} dB Th."
    
    plt.plot(
        x_vals,
        snr,
        label=label_str,
        linewidth=linewidth_val,
        marker='o',
        markersize=markersize_val,
        color=dark_color
    )

# === Labels and Ticks ===
plt.xlabel("Index", fontsize=16, fontweight='bold')
plt.ylabel("SNR (dB)", fontsize=16, fontweight='bold')
plt.xticks(fontsize=14, fontweight='bold')
plt.yticks(fontsize=14, fontweight='bold')
plt.ylim(6, 35)
plt.grid(True)
plt.legend(fontsize=13, loc='upper right', prop={'weight': 'bold'})

# === Force integer ticks ===
plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

# === Save Plot ===
plt.tight_layout()
base_filename = "snr_lineplot_mavg"
for ext in ['png', 'svg', 'eps']:
    plt.savefig(os.path.join(experiment_folder, f"{base_filename}.{ext}"), format=ext, dpi=600)

plt.show()
