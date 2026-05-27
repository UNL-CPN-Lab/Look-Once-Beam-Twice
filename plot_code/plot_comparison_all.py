import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker
import os

SNR_THRESHOLD_FACTOR = 1.0  # SNR threshold factor
REFERENCE_MAX_SNR_DB = 17.4  # Reference SNR in dB for 0.8 × max threshold

# ---------- 1. Define base path and experiment name ----------
exp_base_path = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH"
experiment_name = "nh_apr22_gain13db_3m_t1"
experiment_path = os.path.join(exp_base_path, experiment_name)

ground_truth_name = "exhaustive_sweep_13db_apr16"
ground_truth_path = os.path.join(exp_base_path, ground_truth_name)

# ---------- 2. Load experimental data ----------
adaptive_df = pd.read_csv(os.path.join(experiment_path, "results.csv"))

# ---------- 3.  Load ground truth data ----------
forward_df = pd.read_csv(os.path.join(ground_truth_path, "forward_max_snr_per_angle.csv"))
tx30_max_forward_df = pd.read_csv(os.path.join(ground_truth_path, "tx30_max_snr.csv"))
tx32_rx32_forward_df = pd.read_csv(os.path.join(ground_truth_path, "snr_tx32_rx32_forward.csv"))
tx27_rx32_forward_df = pd.read_csv(os.path.join(ground_truth_path, "snr_tx30_rx32_forward.csv"))
snr_gt_df = pd.read_csv(os.path.join(experiment_path, "rx_beam_with_snr_generated.csv"))


RX_BEAM_ANGLES = [0,-45.0, -43.5, -42.1, -40.6, -39.2, -37.7, -36.3, -34.8, -33.4, -31.9, -30.5, -29.0, -27.6, -26.1, -24.7, -23.2, -21.8, -20.3, -18.9, -17.4, -16.0, -14.5, -13.1, -11.6, -10.2, -8.7, -7.3, -5.8, -4.4, -2.9, -1.5, 0, 1.5, 2.9, 4.4, 5.8, 7.3, 8.7, 10.2, 11.6, 13.1, 14.5, 16.0, 17.4, 18.9, 20.3, 21.8, 23.2, 24.7, 26.1, 27.6, 29.0, 30.5, 31.9, 33.4, 34.8, 36.3, 37.7, 39.2, 40.6, 42.1, 43.5, 45.0]
    
TX_BEAM_ANGLES = [0,45.0, 43.5, 42.1, 40.6, 39.2, 37.7, 36.3, 34.8, 33.4, 31.9, 30.5, 29.0, 27.6, 26.1, 24.7, 23.2, 21.8, 20.3, 18.9, 17.4, 16.0, 14.5, 13.1, 11.6, 10.2, 8.7, 7.3, 5.8, 4.4, 2.9, 1.5, 0, -1.5, -2.9, -4.4, -5.8, -7.3, -8.7, -10.2, -11.6, -13.1, -14.5, -16.0, -17.4, -18.9, -20.3, -21.8, -23.2, -24.7, -26.1, -27.6, -29.0, -30.5, -31.9, -33.4, -34.8, -36.3, -37.7, -39.2, -40.6, -42.1,-43.5, -45.0]

# Replace index with actual angle in CSV-based DataFrames
for df in [forward_df,tx32_rx32_forward_df,tx27_rx32_forward_df]:
    if "Boresight Angle" in df.columns:
        df["Boresight Angle"] = df["Boresight Angle"] - 90

    if "Rotor Angle" in df.columns:
        df["Boresight Angle"] = df["Rotor Angle"] - 90



# Plot setup
plt.figure(figsize=(20, 8))
sns.set_context("notebook", font_scale=2.0)

# Line plot for adaptive beamforming and baselines

sns.lineplot(data=forward_df, x="Boresight Angle", y="SNR (dB)",
             marker="v", markersize=8, linewidth=3,
             label="Best Tx Beam - Best Rx Beam in Exhaustive Sweep", color="darkblue")

# sns.lineplot(data=tx30_max_forward_df, x="Boresight Angle", y="SNR (dB)",
#              marker="P", markersize=8, linewidth=3,
#              label="Tx 2.9 degree - Best Rx Beam in Exhaustive Sweep", color="crimson") #crimson

sns.lineplot(data=tx27_rx32_forward_df, x="Boresight Angle", y="SNR (dB)",
             marker="D", markersize=8, linewidth=3,
             label="Tx 2.9 degree - Rx 0 degree Exhaustive Sweep", color="purple")



# sns.lineplot(data=tx32_rx32_forward_df, x="Boresight Angle", y="SNR (dB)",
#              marker="D", markersize=8, linewidth=3,
#              label="0 degree - 0 degree Exhaustive Sweep", color="orange")

sns.lineplot(data=adaptive_df, x="Boresight Angle", y="SNR (dB)",
             marker="o", markersize=6, linewidth=3,
             label="Adaptive Beamforming ", color="green")


# threshold_value = SNR_THRESHOLD_FACTOR * REFERENCE_MAX_SNR_DB

# plt.axhline(y=threshold_value, color='gray', linestyle='--', linewidth=2,
#             label=f"SNR Threshold ({SNR_THRESHOLD_FACTOR} × {REFERENCE_MAX_SNR_DB} = {threshold_value:.2f} dB)")



# # New: Ground Truth SNR from merged CSV
# sns.lineplot(data=snr_gt_df, x="boresight", y="snr_gt",
#              marker="s", markersize=6, linewidth=3,
#              label="GT SNR (Tx 2.9° - Rx Beam Index : SNR from Ground Truth)", color="black")




# Format axes
plt.title("SNR vs Boresight Angle", fontsize=24)
plt.xlabel("Boresight Angle (°)", fontsize=22)
plt.ylabel("SNR (dB)", fontsize=22)
plt.xticks(rotation=45,fontsize=16)
plt.yticks(fontsize=16)
plt.xlim(-90, 90)
plt.ylim(0,30)

# Grid every 5 degrees
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(5))
plt.grid(True)

# Add legend
plt.legend(fontsize=14)
plt.tight_layout()

# Save and show
plt.tight_layout()

plot_base_name = f"snr_vs_boresight_{experiment_name}"

# Save in multiple formats
# plt.savefig(os.path.join(experiment_path,f"{plot_base_name}.png"), format='png')
# plt.savefig(os.path.join(experiment_path,f"{plot_base_name}.svg"), format='svg')
# plt.savefig(os.path.join(experiment_path,f"{plot_base_name}.eps"), format='eps')
plt.savefig('simplesweep.png', format='png')
# plt.show()
