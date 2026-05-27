
# =================== SETUP ===================
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker
import numpy as np
import sys

# Add the root path so we can import the configurations module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)


from configurations.utils import snr_percent_db
from configurations.config import *




# experiment_name = "sc_jun22_gain8db_3m_AB15"
# project_dir = os.path.join(PROJECT_ROOT, "indoor", "continuous", "automatic_indoor_evaluations_basic","Adaptive_Beamforming_SC")
# experiment_path = os.path.join(project_dir,  experiment_name)
# mode = "2"

os.environ["GROUND_TRUTH_PATH"] = GROUND_TRUTH_DIR
os.environ["GROUND_TRUTH_NAME"] = GROUND_TRUTH_NAME

linewidth = 5
marker_size = 12



""" ===================== TO RUN FILE THROUGH OTHER FILE ================= """

# Get experiment context from environment
experiment_name = os.getenv("EXPERIMENT_NAME")
experiment_path = os.getenv("EXPERIMENT_PATH")
ground_truth_path = GROUND_TRUTH_DIR
ground_truth_name = GROUND_TRUTH_NAME
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



# =================== CALCULATE tx_fixed FOR STEP 1,2 ===================

tx_mode_df = pd.read_csv(os.path.join(ground_truth_path, "forward_max_snr_per_angle.csv"))
tx_fixed_index = int(tx_mode_df["Tx Beam Index"].mode().iloc[0])




# =================== MODE 1: PLOT GROUND TRUTH ONLY    ===================

forward_df = pd.read_csv(os.path.join(ground_truth_path, "forward_max_snr_per_angle.csv"))

# tx_fixed_max_rx_csv = os.path.join(ground_truth_path, f"tx{tx_fixed_index}_max_snr.csv")
# tx_fixed_max_rx_df = pd.read_csv(tx_fixed_max_rx_csv)

# tx_fixed_rx32_csv = os.path.join(ground_truth_path, f"snr_tx{tx_fixed_index}_rx32_forward.csv")
# tx_fixed_rx32_forward_df = pd.read_csv(tx_fixed_rx32_csv)


tx_fixed_max_rx_csv = os.path.join(ground_truth_path, f"tx{fixed_tx_beam}_max_snr.csv")
tx_fixed_rx32_csv = os.path.join(ground_truth_path, f"snr_tx{fixed_tx_beam}_rx32_forward.csv")

# Initialize dataframes as None
tx_fixed_max_rx_df = None
tx_fixed_rx32_forward_df = None


plt.figure(figsize=(20, 8))
sns.set_context("notebook", font_scale=2.0)

if mode == "1":
    print("Mode 1: Plotting Ground Truth SNR results")

    sns.lineplot(data=forward_df, x="Boresight", y="SNR (dB)",
                marker="v", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                label="Best Beam Pair", color="darkblue")

    sns.lineplot(data=tx_fixed_rx32_forward_df, x="Boresight", y="SNR (dB)",
                marker="D", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                label=f"TX-RX 0° LoS", color="orange")
    
    # sns.lineplot(data=tx_fixed_max_rx_df, x="Boresight ", y="SNR (dB)",
    #             marker="D", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
    #             label=f"Fixed TX = {tx_fixed}°, Best Rx Beam", color="crimson")

   


# =================== STEP 1: generate_snr from ground truth ===================
# if mode != "1":
#     output_csv_path = os.path.join(experiment_path, "rx_beam_with_snr_generated.csv")
#     if not os.path.exists(output_csv_path):
#         print("Step 1: Generating SNR")
#         results_file = os.path.join(experiment_path, f"results_{experiment_name}.csv")
#         snr_file = os.path.join(ground_truth_path, "forward_all_snr_data.csv")
#         results_df = pd.read_csv(results_file)
#         snr_df = pd.read_csv(snr_file)
#         results_df.columns = results_df.columns.str.strip()
#         snr_df.columns = snr_df.columns.str.strip()

#        # Dynamically rename based on mode
    
#         if mode == "3" or mode == "4":
#             results_df = results_df.rename(columns={
#                 'Rx Beam Index (Selected)': 'Rx Beam Index'
#             })
            
#         # Filter out NO_RADIO rows
#         if "Jetson Detection" in results_df.columns:
#             results_df = results_df[results_df["Jetson Detection"] != "NO_RADIO"].copy()
            
#         snr_df = snr_df.rename(columns={
#             'SNR (dB)': 'snr_gt'
#         })
        
        

#         results_df = results_df[(results_df["Boresight"] >= -45) & (results_df["Boresight"] <= 45)]
#         results_df["Rx Beam Index"] = pd.to_numeric(results_df["Rx Beam Index"], errors='coerce').fillna(-1).astype(int)

#         results_df["Rx Beam Index"] = results_df["Rx Beam Index"].astype(int)
#         snr_df["Boresight"] = snr_df["Boresight"].astype(int)
#         snr_df["Rx Beam Index"] = snr_df["Rx Beam Index"].astype(int)
#         snr_df = snr_df[snr_df["Tx Beam Index"] == tx_fixed_index]


#         merged_df = pd.merge(
#             results_df[["Boresight", "Rx Beam Index", "Rx Beam Angle", "SNR (dB)"]],
#             snr_df[["Boresight", "Rx Beam Index", "snr_gt"]],
#             on=["Boresight", "Rx Beam Index"],
#             how="left"
#         )
#         merged_df.to_csv(output_csv_path, index=False)
#         offline_df = merged_df.copy()

#     else:
#         print("Step 1: SNR already generated. Skipping.")
#         offline_df = pd.read_csv(output_csv_path)



# =================== STEP 2: PLOT SNR VS BORESIGHT ===================

if mode in ["2", "3", "4"]:
    adaptive_df = pd.read_csv(os.path.join(experiment_path, f"results_{experiment_name}.csv"))
    adaptive_df = adaptive_df[adaptive_df["Jetson Detection"] != "NO_RADIO"].copy()
    adaptive_df = adaptive_df[(adaptive_df["Boresight"] >= -65) & (adaptive_df["Boresight"] <= 65)]




if mode == "2":

    print("Step 2: Plotting comparison SNR results for mode 2")
   
    sns.lineplot(data=forward_df, x="Boresight", y="SNR (dB)",
                marker="v", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                label="Best Beam Pair", color="darkblue")

    # sns.lineplot(data=tx_fixed_rx32_forward_df, x="Boresight", y="SNR (dB)",
    #             marker="D", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
    #             label=f"TX-RX 0° LoS", color="orange")

    sns.lineplot(data=adaptive_df, x="Boresight", y="SNR (dB)",
                 marker="o", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                 label="Adaptive Beamforming", color="green")
    
    # sns.lineplot(data=offline_df, x="Boresight", y="snr_gt",
    #          marker="s", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
    #          label="AB(offline)", color="purple")

    threshold_value = SNR_THRESHOLD
    plt.axhline(y=threshold_value, color='gray', linestyle='--', linewidth=linewidth,markeredgecolor='none',
            label=f"SNR Th: {SNR_THRESHOLD} dB")
    
#     threshold_value = snr_percent_db(SNR_THRESHOLD_FACTOR , REFERENCE_MAX_SNR_DB)
#     plt.axhline(y=threshold_value, color='gray', linestyle='--', linewidth=linewidth,
#             label=f"SNR Th: {SNR_THRESHOLD_FACTOR * 100:.0f}%"
# )


if mode == "3" :

    print("Step 2: Plotting comparison SNR results for mode 3")
  
    sns.lineplot(data=forward_df, x="Boresight", y="SNR (dB)",
                marker="v", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                label="Best Beam Pair", color="darkblue")

    # sns.lineplot(data=tx_fixed_rx32_forward_df, x="Boresight", y="SNR (dB)",
    #             marker="D", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
    #             label=f"TX-RX 0° LoS", color="orange")
   
    # sns.lineplot(data=adaptive_df, x="Boresight", y="Initial SNR (dB)",
    #              marker="s", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
    #              label="Adaptive Beamforming ", color="purple")
    
    sns.lineplot(data=adaptive_df, x="Boresight", y="SNR (dB)",
                 marker="o", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                 label="AB with Correction", color="green")
    
    
    threshold_value = SNR_THRESHOLD
    plt.axhline(y=threshold_value, color='gray', linestyle='--', linewidth=linewidth,markeredgecolor='none',
            label=f"SNR Th: {SNR_THRESHOLD} dB")
    

    # threshold_value = snr_percent_db(SNR_THRESHOLD_FACTOR , REFERENCE_MAX_SNR_DB)
    # plt.axhline(y=threshold_value, color='gray', linestyle='--', linewidth=linewidth,markeredgecolor='none',
    #         label=f"SNR Th: {SNR_THRESHOLD_FACTOR * 100:.0f}%"
# )





if mode == "4":

    print("Step 2: Plotting comparison SNR results for mode 4")
  
    sns.lineplot(data=forward_df, x="Boresight", y="SNR (dB)",
                marker="v", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                label="Best Beam Pair", color="darkblue")

    sns.lineplot(data=tx_fixed_rx32_forward_df, x="Boresight", y="SNR (dB)",
                marker="D", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                label=f"TX-RX 0° LoS", color="orange")

    # sns.lineplot(data=adaptive_df, x="Boresight", y="Initial SNR (dB)",
    #              marker="s", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
    #              label="Initial Adaptive Beamforming SNR ", color="purple")
    
    
    sns.lineplot(data=adaptive_df, x="Boresight", y="SNR (dB)",
                 marker="o", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
                 label="AB with Correction", color="green")
    

    # threshold_value = snr_percent_db(SNR_THRESHOLD_FACTOR , REFERENCE_MAX_SNR_DB)
    threshold_value = SNR_THRESHOLD
    plt.axhline(y=threshold_value, color='gray', linestyle='--', linewidth=linewidth,markeredgecolor='none',
            label=f"SNR Th: {SNR_THRESHOLD} dB")



plt.xlabel("Boresight Angle (°)", fontsize=28, fontweight='bold')
plt.ylabel("SNR (dB)", fontsize=28, fontweight='bold')
plt.xticks(rotation=45, fontsize=28, fontweight='bold')
plt.yticks(fontsize=28, fontweight='bold')
plt.xlim(-90, 90)
plt.ylim(5, 45)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(15))
plt.grid(True)
plt.legend(loc='upper right', prop={'weight': 'bold', 'size': 20}, frameon=True)  # Add fontweight if needed
plt.tight_layout()

save_plot("snr_vs_boresight")




# =================== STEP 3: beam_indices_plot ===================
print("Step 3: Plotting RX Beam Indices vs Boresight Angle")


if mode != "1":
    if "Rx Beam Index (YOLO Predicted)" in adaptive_df.columns:
        adaptive_df["Rx Beam Angle"] = adaptive_df["Rx Beam Index (Selected)"].apply(
            lambda i: RX_BEAM_ANGLES[int(i)] if pd.notnull(i) and 0 <= int(i) < len(RX_BEAM_ANGLES) else np.nan
        )


plt.figure(figsize=(20, 6))
sns.set_context("notebook", font_scale=2.0)
plt.scatter(forward_df["Boresight"], forward_df["Rx Beam Angle"], label="RX Beam Angle ", s=12, marker='v', color="darkblue")
if mode != "1":
    plt.scatter(adaptive_df["Boresight"], adaptive_df["Rx Beam Angle"], label="RX Beam Angle", s=12, marker='o', color="red")
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
    
    df = df[(df["Boresight"] >= -32) & (df["Boresight"] <= 25)]

    

    df["predicted_angle"] = df["Rx Beam Index (YOLO Predicted)"].map(
        lambda idx: RX_BEAM_ANGLES[int(idx)] if pd.notna(idx) and 0 <= int(idx) < len(RX_BEAM_ANGLES) else None
    )
    df["selected_angle"] = df["Rx Beam Index (Selected)"].map(
        lambda idx: RX_BEAM_ANGLES[int(idx)] if pd.notna(idx) and 0 <= int(idx) < len(RX_BEAM_ANGLES) else None
    )
    df["offset_error_deg"] = abs(df["predicted_angle"] - df["selected_angle"])
    
    plt.figure(figsize=(12, 6))
    plt.bar(df["Boresight"], df["offset_error_deg"])

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
    sns.barplot(data=df, x="Boresight", y="Beams Checked in Search", color="steelblue")
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


