import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker
import numpy as np
import os

# ---------- 1. Define base path and experiment name ----------
exp_base_path = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH"
<<<<<<< HEAD
experiment_name = "nh_apr22_gain13db_3m_t8"
=======
experiment_name = "nh_apr21_gain13db_3m_t6"
>>>>>>> e262bb6 (minor change)
experiment_path = os.path.join(exp_base_path, experiment_name)

ground_truth_name = "exhaustive_sweep_13db_apr16"
ground_truth_path = os.path.join(exp_base_path, ground_truth_name)

# ---------- 2. Load experimental data ----------
adaptive_df = pd.read_csv(os.path.join(experiment_path, "results.csv"))

# ---------- 3.  Load ground truth data ----------
forward_df = pd.read_csv(os.path.join(ground_truth_path, "forward_max_snr_per_angle.csv"))
# tx32_max_forward_df = pd.read_csv(os.path.join(ground_truth_path, "snr_tx32_max_rx_forwards.csv"))
# tx32_rx32_forward_df = pd.read_csv(os.path.join(ground_truth_path, "snr_tx32_rx32_forward.csv"))
# tx27_rx32_forward_df = pd.read_csv(os.path.join(ground_truth_path, "snr_tx27_rx32_forward.csv"))

RX_BEAM_ANGLES = [0,-45.0, -43.5, -42.1, -40.6, -39.2, -37.7, -36.3, -34.8, -33.4, -31.9, -30.5, -29.0, -27.6, -26.1, -24.7, -23.2, -21.8, -20.3, -18.9, -17.4, -16.0, -14.5, -13.1, -11.6, -10.2, -8.7, -7.3, -5.8, -4.4, -2.9, -1.5, 0, 1.5, 2.9, 4.4, 5.8, 7.3, 8.7, 10.2, 11.6, 13.1, 14.5, 16.0, 17.4, 18.9, 20.3, 21.8, 23.2, 24.7, 26.1, 27.6, 29.0, 30.5, 31.9, 33.4, 34.8, 36.3, 37.7, 39.2, 40.6, 42.1, 43.5, 45.0]
    
TX_BEAM_ANGLES = [0,45.0, 43.5, 42.1, 40.6, 39.2, 37.7, 36.3, 34.8, 33.4, 31.9, 30.5, 29.0, 27.6, 26.1, 24.7, 23.2, 21.8, 20.3, 18.9, 17.4, 16.0, 14.5, 13.1, 11.6, 10.2, 8.7, 7.3, 5.8, 4.4, 2.9, 1.5, 0, -1.5, -2.9, -4.4, -5.8, -7.3, -8.7, -10.2, -11.6, -13.1, -14.5, -16.0, -17.4, -18.9, -20.3, -21.8, -23.2, -24.7, -26.1, -27.6, -29.0, -30.5, -31.9, -33.4, -34.8, -36.3, -37.7, -39.2, -40.6, -42.1,-43.5, -45.0]

# Assign angles
for df in [forward_df]:
    if "Rx Beam" in df.columns:
        df["Rx Beam Angle"] = df["Rx Beam"].apply(
            lambda i: RX_BEAM_ANGLES[int(i)] if pd.notnull(i) and int(i) in range(len(RX_BEAM_ANGLES)) else np.nan
        )
    if "Tx Beam" in df.columns:
        df["Tx Beam Angle"] = df["Tx Beam"].apply(
            lambda i: TX_BEAM_ANGLES[int(i)] if pd.notnull(i) and 0 <= int(i) < len(TX_BEAM_ANGLES) else np.nan
        )

# Replace index with actual angle in CSV-based DataFrames
for df in [adaptive_df]:
    if "Boresight Angle" in df.columns:
        df["Boresight Angle"] = df["Boresight Angle"] - 90

    if "Rotor Angle" in df.columns:
        df["Boresight Angle"] = df["Rotor Angle"] - 90



# Replace index with actual angle in CSV-based DataFrames
for df in [adaptive_df]:

    if "Rx Beam Index (YOLO Predicted)" in df.columns:
        df["Rx Beam Angle"] = df["Rx Beam Index (Selected)"].apply(
            lambda i: RX_BEAM_ANGLES[int(i)] if pd.notnull(i) and int(i) in range(len(RX_BEAM_ANGLES)) else np.nan
        )



# Fixed angle assignments
adaptive_df["Tx Beam Angle"] = TX_BEAM_ANGLES[30]
# tx27_rx32_forward_df["Tx Beam Angle"] =  TX_BEAM_ANGLES[27]
# tx27_rx32_forward_df["Rx Beam Angle"] =  RX_BEAM_ANGLES[32]
# tx32_max_forward_df["Tx Beam Angle"] =  TX_BEAM_ANGLES[32]


# # TX Scatter Plot
# plt.figure(figsize=(20, 6))
# sns.set_context("notebook", font_scale=2.0)
# plt.scatter(forward_df["Boresight Angle"], forward_df["Tx Beam Angle"], label="Tx Best Beam in Exhaustive Sweep", s=20, marker='o', color="darkblue", zorder=2)
# # plt.scatter(adaptive_df["Boresight Angle"], adaptive_df["Tx Beam Angle"], label="Adaptive Beamforming", s=20, marker='^', color="forestgreen", zorder=3)
# plt.title("TX Beamforming Angle vs Boresight Angle", fontsize=24)
# plt.xlabel("Boresight Angle (°)", fontsize=22)
# plt.ylabel("TX Beamforming Angle (°)", fontsize=22)
# plt.xticks(rotation=45, fontsize=16)
# plt.yticks(fontsize=16)
# plt.xlim(-90, 90)
# plt.ylim(-50, 50)
# plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(5))
# plt.grid(True, zorder=0)
# plt.legend(fontsize=14)
# plt.tight_layout()
# plot_base_name = f"tx_beam_vs_boresight_{ground_truth_name}"

# # Save in multiple formats
# plt.savefig(os.path.join(ground_truth_path,f"{plot_base_name}.png"), format='png')
# plt.savefig(os.path.join(ground_truth_path,f"{plot_base_name}.svg"), format='svg')
# plt.savefig(os.path.join(ground_truth_path,f"{plot_base_name}.eps"), format='eps')
# plt.show()

# RX Scatter Plot
plt.figure(figsize=(20, 6))
sns.set_context("notebook", font_scale=2.0)
plt.scatter(forward_df["Boresight Angle"], forward_df["Rx Beam Angle"], label="Rx Best Beam in Exhaustive Sweep", s=10, marker='v', color="darkblue", zorder=2)
plt.scatter(adaptive_df["Boresight Angle"], adaptive_df["Rx Beam Angle"], label="Adaptive Beamforming(Added 3 beams offset)", s=10, marker='o', color="red", zorder=2)
# plt.scatter(adaptive__previous_beam_df["Boresight Angle"], adaptive__previous_beam_df["Rx Beam Angle"], label="Adaptive Beamforming(Default Previous Beam)", s=10, marker='s', color="blue", zorder=3)
# plt.scatter(adaptive_3beams_df["Boresight Angle"], adaptive_3beams_df["Rx Beam Angle"], label="Adaptive Beamforming(3-Beam Max SNR)", s=10, marker='^', color="green", zorder=4)
x_vals = range(-45, 46)
plt.plot(x_vals, [-x for x in x_vals], linestyle='--', color='black', linewidth=2, label='Rx Beamforming Angle = -Boresight Angle')

plt.title("RX Beamforming Angle vs Boresight Angle", fontsize=24)
plt.xlabel("Boresight Angle (°)", fontsize=22)
plt.ylabel("RX Beamforming Angle (°)", fontsize=22)
plt.xticks(rotation=45, fontsize=16)
plt.yticks(fontsize=16)
plt.xlim(-90, 90)
plt.ylim(-50, 50)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(5))
plt.grid(True, zorder=0)
plt.legend(fontsize=14)
plt.tight_layout()
plot_base_name = f"rx_beam_vs_boresight_{experiment_name}"

# Save in multiple formats
plt.savefig(os.path.join(experiment_path,f"{plot_base_name}.png"), format='png')
plt.savefig(os.path.join(experiment_path,f"{plot_base_name}.svg"), format='svg')
plt.savefig(os.path.join(experiment_path,f"{plot_base_name}.eps"), format='eps')
plt.show()

