
# =================== SETUP ===================
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker
import numpy as np
from utils import snr_percent_db
from config import SNR_THRESHOLD_FACTOR, REFERENCE_MAX_SNR_DB

# Base path and experiment details (edit here)
exp_base_path = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH"
experiment_name = "nh_may7_gain13db_3m_t3"
experiment_path = os.path.join(exp_base_path, experiment_name)
ground_truth_name = "exhaustive_sweep_13db_apr16"
ground_truth_path = os.path.join(exp_base_path, ground_truth_name)

# Make sure experiment directory exists
os.makedirs(experiment_path, exist_ok=True)

# RX and TX beam angle lookup
RX_BEAM_ANGLES = [0, -45.0, -43.5, -42.1, -40.6, -39.2, -37.7, -36.3, -34.8, -33.4,
    -31.9, -30.5, -29.0, -27.6, -26.1, -24.7, -23.2, -21.8, -20.3, -18.9, -17.4,
    -16.0, -14.5, -13.1, -11.6, -10.2, -8.7, -7.3, -5.8, -4.4, -2.9, -1.5, 0,
    1.5, 2.9, 4.4, 5.8, 7.3, 8.7, 10.2, 11.6, 13.1, 14.5, 16.0, 17.4,
    18.9, 20.3, 21.8, 23.2, 24.7, 26.1, 27.6, 29.0, 30.5, 31.9, 33.4, 34.8,
    36.3, 37.7, 39.2, 40.6, 42.1, 43.5, 45.0]
TX_BEAM_ANGLES = [0,45.0, 43.5, 42.1, 40.6, 39.2, 37.7, 36.3, 34.8, 33.4, 31.9,
    30.5, 29.0, 27.6, 26.1, 24.7, 23.2, 21.8, 20.3, 18.9, 17.4, 16.0, 14.5,
    13.1, 11.6, 10.2, 8.7, 7.3, 5.8, 4.4, 2.9, 1.5, 0, -1.5, -2.9, -4.4,
    -5.8, -7.3, -8.7, -10.2, -11.6, -13.1, -14.5, -16.0, -17.4, -18.9, -20.3,
    -21.8, -23.2, -24.7, -26.1, -27.6, -29.0, -30.5, -31.9, -33.4, -34.8,
    -36.3, -37.7, -39.2, -40.6, -42.1,-43.5, -45.0]


# =================== USER MODE SELECTION ===================



print("Choose plotting mode:")
print("1 = Ground Truth Only")
print("2 = Basic Experiment")
print("3 = Corrective Experiment")
mode = input("Enter mode number (1, 2, or 3): ").strip()
assert mode in {"1", "2", "3"}, "Invalid mode selected. Use 1, 2, or 3."

save_path = ground_truth_path if mode == "1" else experiment_path
plot_base_prefix = ground_truth_name if mode == "1" else experiment_name

def save_plot(plot_id):
    plot_base_name = f"{plot_id}_{plot_base_prefix}"
    plt.savefig(os.path.join(save_path, f"{plot_base_name}.png"), format="png")
    plt.savefig(os.path.join(save_path, f"{plot_base_name}.svg"), format="svg")
    plt.savefig(os.path.join(save_path, f"{plot_base_name}.eps"), format="eps")



# =================== CALCULATE tx_fixed FOR STEP 1,2 ===================
# if mode != "1":
tx_mode_df = pd.read_csv(os.path.join(ground_truth_path, "forward_max_snr_per_angle.csv"))
tx_fixed = round(tx_mode_df["Tx Beam Angle"].mode().iloc[0], 1)
tx_fixed_index = TX_BEAM_ANGLES.index(tx_fixed)

# =================== STEP 1: generate_snr from ground truth ===================
if mode != "1":
    output_csv_path = os.path.join(experiment_path, "rx_beam_with_snr_generated.csv")
    if not os.path.exists(output_csv_path):
        print("Step 1: Generating SNR")
        results_file = os.path.join(experiment_path, "results.csv")
        snr_file = os.path.join(ground_truth_path, "forward_all_snr_data.csv")
        results_df = pd.read_csv(results_file)
        snr_df = pd.read_csv(snr_file)
        results_df.columns = results_df.columns.str.strip()
        snr_df.columns = snr_df.columns.str.strip()

        results_df = results_df.rename(columns={
            'Boresight Angle': 'boresight',
            'Rx Beam Index (Selected)': 'rx_beam_index',
            'SNR (dB)': 'snr_result'
        })
        snr_df = snr_df.rename(columns={
            'Boresight Angle': 'boresight',
            'Tx Beam Index': 'tx_beam_index',
            'Rx Beam Index': 'rx_beam_index',
            'SNR (dB)': 'snr_gt'
        })

        results_df = results_df[(results_df["boresight"] >= -45) & (results_df["boresight"] <= 45)]
        results_df["boresight"] = results_df["boresight"].astype(int)
        results_df["rx_beam_index"] = results_df["rx_beam_index"].astype(int)
        snr_df["boresight"] = snr_df["boresight"].astype(int)
        snr_df["rx_beam_index"] = snr_df["rx_beam_index"].astype(int)
        snr_df = snr_df[snr_df["tx_beam_index"] == tx_fixed_index]
        results_df["rx_beam_angle"] = results_df["rx_beam_index"].apply(
            lambda idx: RX_BEAM_ANGLES[idx] if 0 <= idx < len(RX_BEAM_ANGLES) else None
        )

        merged_df = pd.merge(
            results_df[["boresight", "rx_beam_index", "rx_beam_angle", "snr_result"]],
            snr_df[["boresight", "rx_beam_index", "snr_gt"]],
            on=["boresight", "rx_beam_index"],
            how="left"
        )
        merged_df.to_csv(output_csv_path, index=False)
    else:
        print("Step 1: SNR already generated. Skipping.")



# =================== STEP 2: plot_comparison_all ===================
print("Step 2: Plotting comparison SNR results")
adaptive_df = pd.read_csv(os.path.join(experiment_path, "results.csv"))
forward_df = pd.read_csv(os.path.join(ground_truth_path, "forward_max_snr_per_angle.csv"))

tx_fixed_rx32_csv = os.path.join(ground_truth_path, f"snr_tx{tx_fixed_index}_rx32_forward.csv")
tx_fixed_rx32_forward_df = pd.read_csv(tx_fixed_rx32_csv)



for df in [forward_df, tx_fixed_rx32_forward_df]:
    if "Boresight Angle" in df.columns:
        df["Boresight Angle"] = df["Boresight Angle"] - 90
    if "Rotor Angle" in df.columns:
        df["Boresight Angle"] = df["Rotor Angle"] - 90

plt.figure(figsize=(20, 8))
sns.set_context("notebook", font_scale=2.0)

sns.lineplot(data=forward_df, x="Boresight Angle", y="SNR (dB)",
             marker="v", markersize=8, linewidth=3,
             label="Best Tx Beam - Best Rx Beam (Exhaustive)", color="darkblue")

sns.lineplot(data=tx_fixed_rx32_forward_df, x="Boresight Angle", y="SNR (dB)",
             marker="D", markersize=8, linewidth=3,
             label=f"Fixed TX = {tx_fixed}°, RX = 0° (Exhaustive)", color="purple")


if mode != "1":
    sns.lineplot(data=adaptive_df, x="Boresight Angle", y="SNR (dB)",
                 marker="o", markersize=6, linewidth=3,
                 label="Adaptive Beamforming", color="green")
    
    


if mode != "1":
    snr_gt_df = pd.read_csv(os.path.join(experiment_path, "rx_beam_with_snr_generated.csv"))
    sns.lineplot(data=snr_gt_df, x="boresight", y="snr_gt",
                 marker="s", markersize=6, linewidth=3,
                 label="Adaptive Beamforming with SNR from Ground Truth", color="black")
    
if mode == "3":
    threshold_value = snr_percent_db(SNR_THRESHOLD_FACTOR * REFERENCE_MAX_SNR_DB)
    plt.axhline(y=threshold_value, color='gray', linestyle='--', linewidth=2,
            label=f"SNR Threshold: {threshold_value} dB)")


plt.title("SNR vs Boresight Angle", fontsize=24)
plt.xlabel("Boresight Angle (°)", fontsize=22)
plt.ylabel("SNR (dB)", fontsize=22)
plt.xticks(rotation=45, fontsize=16)
plt.yticks(fontsize=16)
plt.xlim(-90, 90)
plt.ylim(0, 30)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(5))
plt.grid(True)
plt.legend(fontsize=14)
plt.tight_layout()

save_plot("snr_vs_boresight")



# =================== STEP 3: beam_indices_plot ===================
print("Step 3: Plotting RX Beam Indices")


# ========== Assign angles to forward_df ==========
if "Rx Beam" in forward_df.columns:
    forward_df["Rx Beam Angle"] = forward_df["Rx Beam"].apply(
        lambda i: RX_BEAM_ANGLES[int(i)] if pd.notnull(i) and 0 <= int(i) < len(RX_BEAM_ANGLES) else np.nan
    )

if "Tx Beam" in forward_df.columns:
    forward_df["Tx Beam Angle"] = forward_df["Tx Beam"].apply(
        lambda i: TX_BEAM_ANGLES[int(i)] if pd.notnull(i) and 0 <= int(i) < len(TX_BEAM_ANGLES) else np.nan
    )

if "Rotor Angle" in forward_df.columns:
    forward_df["Boresight Angle"] = forward_df["Rotor Angle"] - 90

# ========== Assign angles to adaptive_df ==========
if "Rx Beam Index (YOLO Predicted)" in adaptive_df.columns:
    adaptive_df["Rx Beam Angle"] = adaptive_df["Rx Beam Index (Selected)"].apply(
        lambda i: RX_BEAM_ANGLES[int(i)] if pd.notnull(i) and 0 <= int(i) < len(RX_BEAM_ANGLES) else np.nan
    )


plt.figure(figsize=(20, 6))
sns.set_context("notebook", font_scale=2.0)
plt.scatter(forward_df["Boresight Angle"], forward_df["Rx Beam Angle"], label="Rx Beam (Exhaustive)", s=10, marker='v', color="darkblue")
if mode != "1":
    plt.scatter(adaptive_df["Boresight Angle"], adaptive_df["Rx Beam Angle"], label="Rx Beam (Adaptive)", s=10, marker='o', color="red")
x_vals = range(-45, 46)
plt.plot(x_vals, [-x for x in x_vals], linestyle='--', color='black', linewidth=2, label='Ideal: Rx = -Boresight')
plt.title("RX Beamforming Angle vs Boresight Angle", fontsize=24)
plt.xlabel("Boresight Angle (°)", fontsize=22)
plt.ylabel("RX Beamforming Angle (°)", fontsize=22)
plt.xticks(rotation=45, fontsize=16)
plt.yticks(fontsize=16)
plt.xlim(-90, 90)
plt.ylim(-50, 50)
plt.grid(True)
plt.legend(fontsize=14)
plt.tight_layout()

save_plot("rx_beam_index_vs_boresight")



if mode == "3":
    # =================== STEP 4: error_offset_degrees ===================
    print("Step 4: Plotting offset error in degrees")
    df = pd.read_csv(os.path.join(experiment_path, "results.csv"))
    df["predicted_angle"] = df["Rx Beam Index (YOLO Predicted)"].map(
        lambda idx: RX_BEAM_ANGLES[int(idx)] if pd.notna(idx) and 0 <= int(idx) < len(RX_BEAM_ANGLES) else None
    )
    df["selected_angle"] = df["Rx Beam Index (Selected)"].map(
        lambda idx: RX_BEAM_ANGLES[int(idx)] if pd.notna(idx) and 0 <= int(idx) < len(RX_BEAM_ANGLES) else None
    )
    df["offset_error_deg"] = abs(df["predicted_angle"] - df["selected_angle"])
    
    plt.figure(figsize=(12, 6))
    plt.bar(df["Boresight Angle"], df["offset_error_deg"])
    plt.title("Offset Error in Degrees: YOLO Predicted vs Selected RX Beam Angle", fontsize=16)
    plt.xlabel("Boresight Angle (°)", fontsize=14)
    plt.ylabel("Offset Error (°)", fontsize=14)
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    save_plot("offset_error_deg")
    
    
    # =================== STEP 5: number_of_beams ===================
    print("Step 5: Plotting number of beams checked")
    plt.figure(figsize=(18, 6))
    sns.set_context("notebook", font_scale=1.6)
    sns.barplot(data=df, x="Boresight Angle", y="Beams Checked in Search", palette="viridis")
    plt.title("Number of Beams Checked vs Boresight Angle")
    plt.xlabel("Boresight Angle (°)")
    plt.ylabel("Number of Beams Checked")
    plt.xticks(rotation=45, fontsize=12)
    plt.grid(True, axis='y')
    plt.tight_layout()
    
    save_plot("number_of_beams_checked")
    
    print("\nAll steps completed and saved.")