import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker
import numpy as np



# ----------- Define experiment path and name -----------
experiment_path = "/media/cse-vuran-32/mmWaveSSD/Nebraska_Hall/FixedBeamSweep/nh_apr15_gain13db_3m_t1_los"
experiment_name = "nh_apr15_gain13db_3m_t1_los"
snr_data = []

# ----------- Extract and Average SNR per rx_angle + boresight -----------
for folder in os.listdir(experiment_path):
    if folder.startswith("rx_"):
        try:
            rx_index = int(folder.split("_")[1])
        except ValueError:
            print(f"[WARNING] Skipping folder '{folder}', cannot extract rx_index")
            continue

        rx_path = os.path.join(experiment_path, folder)

        for angle_folder in os.listdir(rx_path):
            if angle_folder.startswith("angle_"):
                try:
                    angle_index = int(angle_folder.split("_")[1])
                    boresight_angle = angle_index - 90
                    snr_file = os.path.join(rx_path, angle_folder, "snr_data.csv")

                    if not os.path.exists(snr_file):
                        print(f"[SKIPPED] Missing file: {snr_file}")
                        continue

                    df = pd.read_csv(snr_file, header=None, sep=None, engine='python')
                    if df.shape[1] < 7:
                        print(f"[SKIPPED] {snr_file} has only {df.shape[1]} columns")
                        continue

                    df.columns = ["sample_size", "tx_idx", "tx_angle", "rx_index", "rx_angle", "boresight", "snr"]

                    avg_snr = df["snr"].mean()
                    rx_angle = df["rx_angle"].iloc[0]

                    snr_data.append({
                        "rx_angle": rx_angle,
                        "boresight": boresight_angle,
                        "avg_snr": avg_snr
                    })

                except Exception as e:
                    print(f"[ERROR] angle folder '{angle_folder}' in '{folder}': {e}")
                    continue

# ----------- Create DataFrame -----------
if not snr_data:
    raise RuntimeError("No SNR data collected.")
# Clean up RX angle precision


full_df = pd.DataFrame(snr_data)

full_df["rx_angle"] = full_df["rx_angle"].round(1)# Clean up RX angle precision




# ----------- 1. Line Plot: SNR vs Boresight for each RX ANGLE -----------
# plt.figure(figsize=(14, 10))  # Keep a large canvas

# max_snr_boresight_0deg = None
# global_max_boresight = None
# global_max_snr = -float("inf")

# for rx_angle in sorted(full_df["rx_angle"].unique()):
#     beam_df = full_df[full_df["rx_angle"] == rx_angle].sort_values("boresight")
#     plt.plot(beam_df["boresight"], beam_df["avg_snr"], label=f"{rx_angle:.1f}°")

#     # 1. Max SNR for RX angle = 0°
#     if abs(rx_angle - 0) == 0:
#         max_idx = beam_df["avg_snr"].idxmax()
#         max_snr_boresight_0deg = beam_df.loc[max_idx, "boresight"]

#     # 2. Track global max SNR across all RX angles
#     local_max = beam_df["avg_snr"].max()
#     if local_max > global_max_snr:
#         global_max_snr = local_max
#         global_max_boresight = beam_df.loc[beam_df["avg_snr"].idxmax(), "boresight"]

# # Plot vertical line for max SNR at RX = 0°
# if max_snr_boresight_0deg is not None:
#     plt.axvline(x=max_snr_boresight_0deg, color='red', linestyle='--', alpha=0.9, linewidth=2,
#                 label=f"Boresight at RX 0° beam: {max_snr_boresight_0deg}°")

# # Plot vertical line for global max SNR
# if global_max_boresight is not None:
#     plt.axvline(x=global_max_boresight, color='black', linestyle='--', alpha=0.9, linewidth=2,
#                 label=f"Boresight at Max SNR: {global_max_boresight}°")


# plt.title("SNR vs Boresight Angle", fontsize=24)
# plt.xlabel("Boresight Angle (°)", fontsize=22)
# plt.ylabel("SNR (dB)", fontsize=22)
# plt.xticks(rotation= 45, fontsize=14)
# plt.yticks( fontsize=14)
# plt.xlim(-90, 90)
# plt.ylim(0, 20)
# plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(5))
# plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(5))
# plt.grid(True)

# # Lower the legend a bit more
# plt.legend(
#     title=" ", fontsize=12, title_fontsize=14,
#     loc='upper center', bbox_to_anchor=(0.5, -0.22),
#     ncol=10, frameon=False
# )

# plt.tight_layout(rect=[0, 0.28, 1, 1])  # Push the plot further up to give room

# # Save the figure
# plot_base_name = f"snr_vs_boresight_rxangle_{experiment_name}"
# plt.savefig(os.path.join(experiment_path, f"{plot_base_name}.png"), format='png', bbox_inches='tight')
# plt.savefig(os.path.join(experiment_path, f"{plot_base_name}.svg"), format='svg', bbox_inches='tight')
# plt.savefig(os.path.join(experiment_path, f"{plot_base_name}.eps"), format='eps', bbox_inches='tight')
# plt.show()

# 



# Pivot for heatmap
heatmap_data = full_df.pivot(index="rx_angle", columns="boresight", values="avg_snr")
heatmap_data = heatmap_data.iloc[::-1]


plt.figure(figsize=(16, 8))
ax = sns.heatmap(
    heatmap_data,
    cmap="viridis",
    annot=False,
    cbar_kws={"label": "Average SNR (dB)"}
)

plt.title("SNR Heatmap: RX Beam Angle vs. Boresight Angle", fontsize=24)
plt.xlabel("Boresight Angle (°)", fontsize=22, labelpad=15)
plt.ylabel("RX Beam Angle (°)", fontsize=22, labelpad=15)

plt.xticks(rotation=45, fontsize=10)
plt.yticks(rotation=45, fontsize=10)


plt.tight_layout(pad=1.5)

# Save
heatmap_base_name = f"snr_heatmap_rxangle_{experiment_name}"
for ext in ['png', 'svg', 'eps']:
    plt.savefig(os.path.join(experiment_path, f"{heatmap_base_name}.{ext}"), format=ext)

plt.show()

# # ----------- 3. Max SNR Boresight per RX ANGLE Plot (Corrected Axes) -----------
# max_snr_angles = full_df.groupby("rx_angle").apply(
#     lambda df: df.loc[df["avg_snr"].idxmax(), "boresight"]
# ).reset_index()
# max_snr_angles.columns = ["rx_angle", "boresight_of_max_snr"]

# plt.figure(figsize=(12, 6))

# # Plot with boresight on x-axis, RX angle on y-axis
# plt.plot(
#     max_snr_angles["boresight_of_max_snr"], 
#     max_snr_angles["rx_angle"], 
#     marker='o', 
#     label="Max SNR Boresight"
# )

# # Add y = -x reference line in (x, y) = (boresight, rx_angle) space
# x_vals = np.linspace(-45, 45, 100)
# y_vals = -x_vals
# plt.plot(x_vals, y_vals, linestyle='--', color='gray', linewidth=1.5, label='RX = - Boresight')

# plt.title("RX Beam Angle vs. Boresight Angle of Max SNR", fontsize=24)
# plt.xlabel("Boresight Angle (°)", fontsize=22)
# plt.ylabel("RX Beam Angle (°)", fontsize=22)
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(rotation=45, fontsize=10)
# plt.grid(True)

# plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(5))
# plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(5))
# plt.xlim(-90, 90)
# plt.ylim(-50, 50)
# plt.legend(fontsize=14)
# plt.tight_layout()

# # Save plot
# plot_base_name = f"rx_angle_vs_max_snr_boresight_{experiment_name}"
# plt.savefig(os.path.join(experiment_path, f"{plot_base_name}.png"), format='png')
# plt.savefig(os.path.join(experiment_path, f"{plot_base_name}.svg"), format='svg')
# plt.savefig(os.path.join(experiment_path, f"{plot_base_name}.eps"), format='eps')
# plt.show()
