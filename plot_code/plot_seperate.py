
# =================== SETUP ===================
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker
import numpy as np
from configurations.utils import snr_percent_db
from configurations.config import *
import sys
import json



# Add the root path so we can import the configurations module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)



linewidth = 5
marker_size = 12


# =================== USER MODE SELECTION ===================


"""  TO RUN FILE INDIVIDUALLY """

# print("Choose plotting mode:")
# print("1 = Ground Truth Only")
# print("2 = Basic Experiment")
# print("3 = Online Corrective Experiment")
# print("4 = Offline Corrective Experiment ")
# mode = "1"

# exp_base_path = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/OutdoorEvalApala/Adaptive_Beamforming_SC/offline_indoor_tests"
# ground_truth_name = "exhaustive_sweep_8db_jun12_sc"# GROUND_TRUTH_NAME
# ground_truth_path = GROUND_TRUTH_DIR


# if mode =="2" or mode == "3" or mode == "4":
    
#     experiment_name = "sc_may19_gain14db_3m_t7"
#     experiment_path = os.path.join(exp_base_path, experiment_name)
#     # Make sure experiment directory exists
#     os.makedirs(experiment_path, exist_ok=True)

#----------------------------------------------------------------------------------------------------------------------------------



""" ===================== TO RUN FILE THROUGH OTHER FILE ================= """


# Get experiment context from environment
experiment_name = os.getenv("EXPERIMENT_NAME")
experiment_path = os.getenv("EXPERIMENT_PATH")
ground_truth_path = os.getenv("GROUND_TRUTH_PATH")
ground_truth_name = os.getenv("GROUND_TRUTH_NAME")
mode = os.getenv("PLOT_MODE")


# Check if environment variables are set

if experiment_name is None or experiment_path is None:
    raise ValueError("Missing EXPERIMENT_NAME or EXPERIMENT_PATH environment variable.")

if ground_truth_path is None:
    ground_truth_path = os.path.join(os.path.dirname(experiment_path), GROUND_TRUTH_NAME)

#----------------------------------------------------------------------------------------------------------------------------------


save_path = ground_truth_path if mode == "1" else experiment_path
plot_base_prefix = ground_truth_name if mode == "1" else experiment_name

def save_plot(plot_id):
    plot_base_name = f"{plot_id}_{plot_base_prefix}"
    plt.savefig(os.path.join(save_path, f"{plot_base_name}.png"), format="png")
    plt.savefig(os.path.join(save_path, f"{plot_base_name}.svg"), format="svg")
    plt.savefig(os.path.join(save_path, f"{plot_base_name}.eps"), format="eps")
    
def tx_angle_index(angle):
    """Return the beam index for a given Tx angle, resolving 0.0 to index 32 only."""
    if angle == 0:
        return 32
    return TX_BEAM_ANGLES.index(angle)

def rx_angle_index(angle):
    """Return the beam index for a given Rx angle, resolving 0.0 to index 32 only."""
    if angle == 0:
        return 32
    return RX_BEAM_ANGLES.index(angle)


# === LOAD THRESHOLD FROM METADATA FILE ===
metadata_path = os.path.join(experiment_path, "metadata_fixed.json")
if not os.path.exists(metadata_path):
    raise FileNotFoundError(f"metadata_fixed.json not found at {metadata_path}")

with open(metadata_path, "r") as f:
    metadata = json.load(f)

threshold_db = float(metadata["Threshold"])
threshold_factor = float(metadata["Threshold Factor"])




# =================== CALCULATE tx_fixed FOR STEP 1,2 ===================

tx_mode_df = pd.read_csv(os.path.join(ground_truth_path, "forward_max_snr_per_angle.csv"))
tx_fixed = round(tx_mode_df["Tx Beam Angle"].mode().iloc[0], 1)
tx_fixed_index = tx_angle_index(tx_fixed)


# =================== MODE 1: PLOT GROUND TRUTH ONLY    ===================

forward_df = pd.read_csv(os.path.join(ground_truth_path, "forward_max_snr_per_angle.csv"))

tx_fixed_max_rx_csv = os.path.join(ground_truth_path, f"tx{tx_fixed_index}_max_snr.csv")
tx_fixed_max_rx_df = pd.read_csv(tx_fixed_max_rx_csv)

tx_fixed_rx32_csv = os.path.join(ground_truth_path, f"snr_tx{tx_fixed_index}_rx32_forward.csv")
tx_fixed_rx32_forward_df = pd.read_csv(tx_fixed_rx32_csv)


for df in [forward_df, tx_fixed_rx32_forward_df]:
    if "Boresight Angle" in df.columns:
        df["Boresight Angle"] = df["Boresight Angle"] - 90
    if "Rotor Angle" in df.columns:
        df["Boresight Angle"] = df["Rotor Angle"] - 90

plt.figure(figsize=(20, 8))
sns.set_context("notebook", font_scale=2.0)

if mode == "1":
    print("Mode 1: Plotting Ground Truth SNR results")

    sns.lineplot(data=forward_df, x="Boresight Angle", y="SNR (dB)",
                marker="v", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                label="Best Beam Pair", color="darkblue")

    sns.lineplot(data=tx_fixed_rx32_forward_df, x="Boresight Angle", y="SNR (dB)",
                marker="D", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                label=f"TX-RX 0° LoS", color="orange")
    
    # sns.lineplot(data=tx_fixed_max_rx_df, x="Boresight Angle", y="SNR (dB)",
    #             marker="D", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
    #             label=f"Fixed TX = {tx_fixed}°, Best Rx Beam", color="crimson")

   


# =================== STEP 1: generate_snr from ground truth ===================
if mode != "1":
    output_csv_path = os.path.join(experiment_path, "rx_beam_with_snr_generated.csv")
    if not os.path.exists(output_csv_path):
        print("Step 1: Generating SNR")
        results_file = os.path.join(experiment_path, f"results_{experiment_name}.csv")
        snr_file = os.path.join(ground_truth_path, "forward_all_snr_data.csv")
        results_df = pd.read_csv(results_file)
        snr_df = pd.read_csv(snr_file)
        results_df.columns = results_df.columns.str.strip()
        snr_df.columns = snr_df.columns.str.strip()

       # Dynamically rename based on mode
        if mode == "2":
            results_df = results_df.rename(columns={
                'Boresight Angle': 'boresight',
                'Rx Beam Index': 'rx_beam_index',
                'SNR (dB)': 'snr_result'
            })
        elif mode == "3" or mode == "4":
            results_df = results_df.rename(columns={
                'Boresight Angle': 'boresight',
                'Rx Beam Index (Selected)': 'rx_beam_index',
                'SNR (dB)': 'snr_result'
            })
            
        # Filter out NO_RADIO rows
        if "Jetson Detection" in results_df.columns:
            results_df = results_df[results_df["Jetson Detection"] != "NO_RADIO"].copy()
            
        snr_df = snr_df.rename(columns={
            'Boresight Angle': 'boresight',
            'Tx Beam Index': 'tx_beam_index',
            'Rx Beam Index': 'rx_beam_index',
            'SNR (dB)': 'snr_gt'
        })
        
        

        results_df = results_df[(results_df["boresight"] >= -45) & (results_df["boresight"] <= 45)]
        results_df["rx_beam_index"] = pd.to_numeric(results_df["rx_beam_index"], errors='coerce').fillna(-1).astype(int)

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
        offline_df = merged_df.copy()

    else:
        print("Step 1: SNR already generated. Skipping.")
        offline_df = pd.read_csv(output_csv_path)



# =================== STEP 2: PLOT SNR VS BORESIGHT ===================

if mode in ["2", "3", "4"]:
    adaptive_df = pd.read_csv(os.path.join(experiment_path, f"results_{experiment_name}.csv"))
    # adaptive_df = adaptive_df[adaptive_df["Jetson Detection"] != "NO_RADIO"].copy()
    adaptive_df = adaptive_df[(adaptive_df["Boresight Angle"] >= -35) & (adaptive_df["Boresight Angle"] <= 35)]




if mode == "2":

    print("Step 2: Plotting comparison SNR results for mode 2")
   
    sns.lineplot(data=forward_df, x="Boresight Angle", y="SNR (dB)",
                marker="v", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                label="Best Beam Pair", color="darkblue")

    sns.lineplot(data=tx_fixed_rx32_forward_df, x="Boresight Angle", y="SNR (dB)",
                marker="D", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                label=f"TX-RX 0° LoS", color="orange")

    sns.lineplot(data=adaptive_df, x="Boresight Angle", y="SNR (dB)",
                 marker="o", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                 label="Adaptive Beamforming", color="green")
    
    # sns.lineplot(data=offline_df, x="boresight", y="snr_gt",
    #          marker="s", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
    #          label="Adaptive Beamforming(offline)", color="purple")

    
  
    
    plt.axhline(y=threshold_db, color='gray', linestyle='--', linewidth=linewidth,
            label=f"Threshold: {threshold_factor:.2f}")



if mode == "3" :

    print("Step 2: Plotting comparison SNR results for mode 3")
  
    sns.lineplot(data=forward_df, x="Boresight Angle", y="SNR (dB)",
                marker="v", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                label="Best Beam Pair", color="darkblue")

    sns.lineplot(data=tx_fixed_rx32_forward_df, x="Boresight Angle", y="SNR (dB)",
                marker="D", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                label=f"TX-RX 0° LoS", color="orange")
   
    # sns.lineplot(data=adaptive_df, x="Boresight Angle", y="Initial SNR (dB)",
    #              marker="s", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
    #              label="Adaptive Beamforming ", color="purple")
    
    sns.lineplot(data=adaptive_df, x="Boresight Angle", y="SNR (dB)",
                 marker="o", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                 label="AB with Correction", color="green")
    

    plt.axhline(y=threshold_db, color='gray', linestyle='--', linewidth=linewidth,
            label=f"Threshold: {threshold_factor:.2f}")






if mode == "4":

    print("Step 2: Plotting comparison SNR results for mode 4")
  
    sns.lineplot(data=forward_df, x="Boresight Angle", y="SNR (dB)",
                marker="v", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                label="Best Beam Pair", color="darkblue")

    sns.lineplot(data=tx_fixed_rx32_forward_df, x="Boresight Angle", y="SNR (dB)",
                marker="D", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                label=f"TX-RX 0° LoS", color="orange")

    # sns.lineplot(data=adaptive_df, x="Boresight Angle", y="Initial SNR (dB)",
    #              marker="s", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
    #              label="Initial Adaptive Beamforming SNR ", color="purple")
    
    
    sns.lineplot(data=adaptive_df, x="Boresight Angle", y="SNR (dB)",
                 marker="o", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                 label="AB with Correction", color="green")
    

    plt.axhline(y=threshold_db, color='gray', linestyle='--', linewidth=linewidth,
            label=f"Threshold: {threshold_factor:.2f}")




plt.xlabel("Boresight Angle (°)", fontsize=28, fontweight='bold')
plt.ylabel("SNR (dB)", fontsize=28, fontweight='bold')
plt.xticks(rotation=45, fontsize=28, fontweight='bold')
plt.yticks(fontsize=28, fontweight='bold')
plt.xlim(-90, 90)
plt.ylim(5, 35)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(15))
plt.grid(True)
plt.legend(loc='upper right', prop={'weight': 'bold', 'size': 20}, frameon=True)  # Add fontweight if needed
plt.tight_layout()

save_plot("snr_vs_boresight")




# =================== STEP 3: beam_indices_plot ===================
print("Step 3: Plotting RX Beam Indices vs Boresight Angle")


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

if mode != "1":
    if "Rx Beam Index (YOLO Predicted)" in adaptive_df.columns:
        adaptive_df["Rx Beam Angle"] = adaptive_df["Rx Beam Index (Selected)"].apply(
            lambda i: RX_BEAM_ANGLES[int(i)] if pd.notnull(i) and 0 <= int(i) < len(RX_BEAM_ANGLES) else np.nan
        )


plt.figure(figsize=(20, 6))
sns.set_context("notebook", font_scale=2.0)
plt.scatter(forward_df["Boresight Angle"], forward_df["Rx Beam Angle"], label="RX Beam Angle ", s=12, marker='v', color="darkblue")
if mode != "1":
    plt.scatter(adaptive_df["Boresight Angle"], adaptive_df["Rx Beam Angle"], label="RX Beam Angle", s=12, marker='o', color="red")
x_vals = range(-45, 46)
plt.plot(x_vals, [-x for x in x_vals], linestyle='--', color='black', linewidth=2, label='Ideal: RX = -Boresight')
# plt.title("RX Beamforming Angle vs Boresight Angle", fontsize=24)
plt.xlabel("Boresight Angle (°)", fontsize=28,fontweight='bold')
plt.ylabel("RX Beamforming Angle (°)", fontsize=28,fontweight='bold')
plt.xticks(rotation=45, fontsize=28,fontweight='bold')
plt.yticks(fontsize=28,fontweight='bold')
plt.xlim(-90, 90)
plt.ylim(-50, 50)
plt.grid(True)
plt.legend(prop={'weight': 'bold', 'size': 28}, frameon=True)  # Add fontweight if needed
plt.tight_layout()

save_plot("rx_beam_index_vs_boresight")


# =================== STEP 4: error_offset_degrees ===================
if mode == "3"  or mode == "4":

    print("Step 4: Plotting offset error in degrees")
    df = pd.read_csv(os.path.join(experiment_path, f"results_{experiment_name}.csv"))
    
    df = df[(df["Boresight Angle"] >= -45) & (df["Boresight Angle"] <= 45)]

    

    df["predicted_angle"] = df["Rx Beam Index (YOLO Predicted)"].map(
        lambda idx: RX_BEAM_ANGLES[int(idx)] if pd.notna(idx) and 0 <= int(idx) < len(RX_BEAM_ANGLES) else None
    )
    df["selected_angle"] = df["Rx Beam Index (Selected)"].map(
        lambda idx: RX_BEAM_ANGLES[int(idx)] if pd.notna(idx) and 0 <= int(idx) < len(RX_BEAM_ANGLES) else None
    )
    df["offset_error_deg"] = abs(df["predicted_angle"] - df["selected_angle"])
    
    plt.figure(figsize=(12, 6))
    plt.bar(df["Boresight Angle"], df["offset_error_deg"])
    # plt.title("Offset Error in Degrees: YOLO Predicted vs Selected RX Beam Angle", fontsize=16)
    plt.xlabel("Boresight Angle (°)", fontsize=28,fontweight='bold')
    plt.xlim(-45,45)
    plt.ylim(0, 10)
    plt.ylabel("Offset Error (°)", fontsize=28,fontweight='bold')
    plt.grid(True)
    plt.xticks(rotation=45, fontsize=28,fontweight='bold')
    plt.yticks(fontsize=28,fontweight='bold')
    # plt.legend(fontsize=18)
    plt.tight_layout()
    
    save_plot("offset_error_deg")
    
    
    # =================== STEP 5: number_of_beams ===================
    print("Step 5: Plotting number of beams checked")
    plt.figure(figsize=(18, 6))
    sns.set_context("notebook", font_scale=1.6)
    sns.barplot(data=df, x="Boresight Angle", y="Beams Checked in Search", color="steelblue")
    # plt.title("Number of Beams Checked vs Boresight Angle")
    plt.xlabel("Boresight Angle (°)", fontsize=28,fontweight='bold')
    plt.ylim(0, 20)
  
    plt.ylabel("Number of Beams Checked", fontsize=24,fontweight='bold')
    plt.xticks(rotation=45, fontsize=28,fontweight='bold')
    plt.grid(True, axis='y')
    plt.yticks(fontsize=20,fontweight='bold')
    # plt.legend(fontsize=18)
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(15))
    plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(2))
    plt.tight_layout()
    
    save_plot("number_of_beams_checked")
    
    print("\nAll steps completed and saved.")


