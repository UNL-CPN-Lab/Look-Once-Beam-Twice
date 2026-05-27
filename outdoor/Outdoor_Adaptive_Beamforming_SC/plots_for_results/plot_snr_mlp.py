# import pandas as pd
# import matplotlib.pyplot as plt
# import numpy as np
# import os
# from matplotlib.ticker import MaxNLocator

# # === Define file and folder names ===
# base_filename = "sc_jul24_gain9db_12db_16m_t1"

# experiment_folder = os.path.join("mlp_Results", base_filename)
# csv_filename = f"results_{base_filename}.csv"
# csv_path = os.path.join(experiment_folder, csv_filename)

# # === Load Data ===
# df = pd.read_csv(csv_path)
# snr = df["SNR (dB)"].copy()
# initial_snr = df.get("Initial SNR (dB)", pd.Series([np.nan] * len(df)))

# # Replace missing SNR with Initial SNR
# snr_filled = snr.fillna(initial_snr)

# x_vals = np.arange(len(snr_filled))

# # === Style Parameters ===
# linewidth_val = 4
# markersize_val = 8

# # === Define pastel and dark colors ===
# pastel_green = (0.6, 0.8, 0.6)
# pastel_blue = (0.6, 0.75, 0.95)
# pastel_purple = (0.75, 0.6, 0.85)
# pastel_orange = (1.0, 0.75, 0.5)
# pastel_red = (1.0, 0.5, 0.5)

# def darken_color(color, factor=0.8):
#     return tuple(min(max(c * factor, 0.0), 1.0) for c in color)

# dark_green = darken_color(pastel_green)
# dark_blue = darken_color(pastel_blue)
# dark_purple = darken_color(pastel_purple)
# dark_orange = darken_color(pastel_orange)
# dark_red = darken_color(pastel_red)

# # === Plot Settings ===
# plt.figure(figsize=(8, 6))

# # === Threshold Lines ===
# thresholds = [
#     (23, pastel_red, "23 dB SNR Th."),
#     (20, pastel_orange, "20 dB SNR Th."),
#     (17, pastel_green, "17 dB SNR Th."),
#     (14, pastel_blue, "14 dB SNR Th."),
#     (11, pastel_purple, "11 dB SNR Th."),
# ]

# for y_val, color, label in thresholds:
#     plt.axhline(y=y_val, color=color, linestyle='--', linewidth=linewidth_val, label=label)

# # === Plot Combined SNR ===
# plt.plot(
#     x_vals,
#     snr_filled,
#     label="YOLOR + MLP (1 mph)",
#     linewidth=linewidth_val,
#     marker='o',
#     markersize=markersize_val,
#     color="darkslategray"
# )

# # === Labels and Ticks ===
# plt.xlabel("Index", fontsize=16, fontweight='bold')
# plt.ylabel("SNR (dB)", fontsize=16, fontweight='bold')
# plt.xticks(fontsize=16, fontweight='bold')
# plt.yticks(fontsize=16, fontweight='bold')
# plt.ylim(0, 40)

# plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
# plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

# # === Legend and Grid ===
# plt.legend(fontsize=14, loc='upper right', prop={'weight': 'bold'})
# plt.grid(True)
# plt.tight_layout()

# # === Save Plot ===
# base_filename = "snr_vs_index"
# for ext in ['eps', 'svg', 'png']:
#     save_path = os.path.join(experiment_folder, f"{base_filename}.{ext}")
#     plt.savefig(save_path, format=ext, dpi=600)

# plt.show()

