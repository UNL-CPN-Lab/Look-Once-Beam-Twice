import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.ticker import MaxNLocator

# === Settings ===
experiment_folder = "mavg_Results"
base_filename = "nh_jul12_gain9db_12db_16m"
linewidth_val = 3
markersize_val = 6

# === Thresholds and pastel colors ===
thresholds_info = {
    "t1": (11, (0.75, 0.6, 0.85)),  # pastel_purple
    "t2": (14, (0.6, 0.75, 0.95)),  # pastel_blue
    "t3": (17, (0.6, 0.8, 0.6))     # pastel_green
    # "t9": (20, (1.0, 0.75, 0.5)),   # pastel_orange
    # "t10": (23, (1.0, 0.5, 0.5))    # pastel_red
}

def darken_color(color, factor=0.8):
    return tuple(min(max(c * factor, 0.0), 1.0) for c in color)

# === Create Plot ===
plt.figure(figsize=(8, 6))

# === Loop through each threshold experiment ===
for label, (threshold_db, pastel_color) in thresholds_info.items():
    file_path = os.path.join(experiment_folder, f"{base_filename}_{label}", f"results_{base_filename}_{label}.csv")
    
    if not os.path.exists(file_path):
        print(f"[ERROR] Missing file: {file_path}")
        continue
    
    try:
        df = pd.read_csv(file_path)
        print(f"[INFO] Loaded file: {file_path} — {len(df)} rows")
    except Exception as e:
        print(f"[ERROR] Failed to read {file_path}: {e}")
        continue

    if "SNR (dB)" not in df.columns:
        print(f"[ERROR] 'SNR (dB)' column not found in: {file_path}")
        continue

    df = df.dropna(subset=["SNR (dB)"])
    df = df[df["SNR (dB)"] >= 0]

    if df.empty:
        print(f"[WARNING] No valid SNR data in: {file_path}")
        continue

    snr = df["SNR (dB)"].values
    x_vals = np.arange(len(snr))

    print(f"[INFO] Plotting {label}: {len(snr)} SNR values (≥ 0 dB)")

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

# === Labels and formatting ===
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
save_name = "snr_lineplot_mavg"
for ext in ['png', 'svg', 'eps']:
    save_path = os.path.join(experiment_folder, f"{save_name}.{ext}")
    try:
        plt.savefig(save_path, format=ext, dpi=600)
        print(f"[INFO] Saved plot to {save_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save {save_path}: {e}")

plt.show()
