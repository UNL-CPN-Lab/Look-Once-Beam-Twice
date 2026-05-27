
# =================== SETUP ===================
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker
import numpy as np
import sys



linewidth = 5
marker_size = 12

# Add the root path so we can import the configurations module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.append(project_root)


from configurations.config import *


# =================== USER MODE SELECTION ===================


# """  TO RUN FILE INDIVIDUALLY """


# exp_base_path = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/experiments/Adaptive_Beamforming_SC"
# ground_truth_name = "optimized_exhaustive_sweep_13db_jun18_sc"# GROUND_TRUTH_NAME
# ground_truth_path = GROUND_TRUTH_DIR




#----------------------------------------------------------------------------------------------------------------------------------



""" ===================== TO RUN FILE THROUGH OTHER FILE ================= """


# Get experiment context from environment
ground_truth_path = os.getenv("GROUND_TRUTH_PATH")
ground_truth_name = os.getenv("GROUND_TRUTH_NAME")



#----------------------------------------------------------------------------------------------------------------------------------


save_path = ground_truth_path 
plot_base_prefix = ground_truth_name 

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




# =================== CALCULATE tx_fixed FOR STEP 1,2 ===================

# tx_mode_df = pd.read_csv(os.path.join(ground_truth_path, "forward_max_snr_per_angle.csv"))
# tx_modes = tx_mode_df["Tx Beam Angle"].mode()
# tx_fixed = round(tx_modes.min(), 1)  # Pick smallest mode
# tx_fixed_index = tx_angle_index(tx_fixed)


# =================== MODE 1: PLOT GROUND TRUTH ONLY    ===================

forward_df = pd.read_csv(os.path.join(ground_truth_path, "forward_max_snr_per_angle.csv"))

tx_fixed_max_rx_csv = os.path.join(ground_truth_path, f"tx{fixed_tx_beam}_max_snr.csv")
tx_fixed_rx32_csv = os.path.join(ground_truth_path, f"snr_tx{fixed_tx_beam}_rx32_forward.csv")

# Initialize dataframes as None
tx_fixed_max_rx_df = None
tx_fixed_rx32_forward_df = None

plt.figure(figsize=(20, 8))
sns.set_context("notebook", font_scale=2.0)

print("Plotting Ground Truth SNR results")

sns.lineplot(data=forward_df, x="Boresight", y="SNR (dB)",
            marker="v", markersize=marker_size, linewidth=linewidth,markeredgecolor='none',
            label="Best Beam Pair", color="darkblue")

# Optional: Plot TX-RX 0° LoS
if os.path.exists(tx_fixed_rx32_csv):
    tx_fixed_rx32_forward_df = pd.read_csv(tx_fixed_rx32_csv)
    sns.lineplot(data=tx_fixed_rx32_forward_df, x="Boresight", y="SNR (dB)",
                marker="D", markersize=marker_size, linewidth=linewidth, markeredgecolor='none',
                label=f"TX-RX 0° LoS", color="orange")
else:
    print(f"[WARN] File not found: {tx_fixed_rx32_csv} — skipping RX32 plot.")

# Optional: Plot Fixed TX + Best RX
if os.path.exists(tx_fixed_max_rx_csv):
    tx_fixed_max_rx_df = pd.read_csv(tx_fixed_max_rx_csv)
    sns.lineplot(data=tx_fixed_max_rx_df, x="Boresight", y="SNR (dB)",
                marker="D", markersize=marker_size, linewidth=linewidth, markeredgecolor='none',
                label=f"Fixed TX = {fixed_tx_beam}°, Best Rx Beam", color="crimson")
else:
    print(f"[WARN] File not found: {tx_fixed_max_rx_csv} — skipping Fixed TX+Best RX plot.")



   


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
print("Step 2: Plotting RX Beam Indices vs Boresight Angle")


# ========== Assign angles to forward_df ==========
if "Rx Beam" in forward_df.columns:
    forward_df["Rx Beam Angle"] = forward_df["Rx Beam"].apply(
        lambda i: RX_BEAM_ANGLES[int(i)] if pd.notnull(i) and 0 <= int(i) < len(RX_BEAM_ANGLES) else np.nan
    )

if "Tx Beam" in forward_df.columns:
    forward_df["Tx Beam Angle"] = forward_df["Tx Beam"].apply(
        lambda i: TX_BEAM_ANGLES[int(i)] if pd.notnull(i) and 0 <= int(i) < len(TX_BEAM_ANGLES) else np.nan
    )



plt.figure(figsize=(20, 6))
sns.set_context("notebook", font_scale=2.0)
plt.scatter(forward_df["Boresight"], forward_df["Rx Beam Angle"], label="RX Beam Angle ", s=12, marker='v', color="darkblue")

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



