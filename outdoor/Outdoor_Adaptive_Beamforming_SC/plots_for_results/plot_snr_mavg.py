import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.ticker import MaxNLocator

# === Settings ===
experiment_folder = "mavg_Results"
base_filename = "sc_jul13_gain9db_12db_16m"
linewidth_val = 3
markersize_val = 6

# === Thresholds and pastel colors ===
thresholds_info = {
    # "t11": (11, (0.75, 0.6, 0.85)),  # pastel_purple
    "t8": (14, (0.6, 0.75, 0.95)),  # pastel_blue
    "t9": (17, (0.6, 0.8, 0.6))    # pastel_green
    # "t14": (20, (1.0, 0.75, 0.5)),   # pastel_orange
    # "t15": (23, (1.0, 0.5, 0.5))    # pastel_red
}

def darken_color(color, factor=0.8):
    return tuple(min(max(c * factor, 0.0), 1.0) for c in color)

# === Loop through each threshold experiment ===
for label, (threshold_db, pastel_color) in thresholds_info.items():
    subfolder = f"{base_filename}_{label}"
    file_path = os.path.join(experiment_folder, subfolder, f"results_{base_filename}_{label}.csv")

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

    # === Create individual plot ===
    fig, ax = plt.subplots(figsize=(8, 6))

    dark_color = darken_color(pastel_color)
    ax.plot(
        x_vals,
        snr,
        label=f"YOLOR+ M.Avg(1 mph-Not Guard)",
        linewidth=linewidth_val,
        marker='o',
        markersize=markersize_val,
        color=dark_color
    )

    # === Add threshold line ===
    ax.axhline(y=threshold_db, color=dark_color, linestyle='--', linewidth=2, label=f"{threshold_db} dB Threshold")

    # === Labels and formatting ===
    ax.set_xlabel("Index", fontsize=16, fontweight='bold')
    ax.set_ylabel("SNR (dB)", fontsize=16, fontweight='bold')
    ax.tick_params(axis='both', labelsize=14)
    ax.set_ylim(0,40)
    ax.grid(True)
    ax.legend(fontsize=13, loc='upper right', prop={'weight': 'bold'})

    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    fig.tight_layout()

    # === Save in experiment folder ===
    save_name = f"snr_plot_{base_filename}_{label}"
    for ext in ['png', 'svg', 'eps']:
        save_path = os.path.join(experiment_folder, subfolder, f"{save_name}.{ext}")
        try:
            fig.savefig(save_path, format=ext, dpi=600)
            print(f"[INFO] Saved plot to {save_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save {save_path}: {e}")

    plt.close(fig)
