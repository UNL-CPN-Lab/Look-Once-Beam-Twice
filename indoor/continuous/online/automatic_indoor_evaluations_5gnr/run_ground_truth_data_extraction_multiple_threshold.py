
# =================== SETUP ===================
import os
import pandas as pd
import re
import sys
import importlib.util
import numpy as np

# Add the root path so we can import the configurations module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.append(project_root)


from configurations.utils import *
from configurations.config import PROJECT_ROOT



# Read command-line arguments
if len(sys.argv) != 3:
    print("Usage: python3 run_full_data_extraction.py  <exp_dir>")
    sys.exit(1)

base_name = sys.argv[1]
snr_quantiles = [float(q) for q in sys.argv[2].split(",")]




# Source: where optimized_beam_sweep.py wrote the raw per-angle CSVs.
# Replace <DATA_ROOT> with the absolute path of your storage volume.
base_dir = f"<DATA_ROOT>/mmWaveSSD/Schorr_Center/Full_Sweep_Experiment/gain13db/{base_name}"
# Destination: project-tree copy. Kept in sync with GROUND_TRUTH_PATH set in
# automatic_5gnr_main.py.
exp_dir = os.path.join(
    PROJECT_ROOT,
    "indoor", "continuous", "online", "automatic_indoor_evaluations_5gnr",
    "Adaptive_Beamforming_SC",
    base_name,
)
os.makedirs(exp_dir, exist_ok=True)


# Angle mappings
RX_BEAM_ANGLES = [0, -45.0, -43.5, -42.1, -40.6, -39.2, -37.7, -36.3, -34.8, -33.4,
    -31.9, -30.5, -29.0, -27.6, -26.1, -24.7, -23.2, -21.8, -20.3, -18.9, -17.4,
    -16.0, -14.5, -13.1, -11.6, -10.2, -8.7, -7.3, -5.8, -4.4, -2.9, -1.5, 0,
    1.5, 2.9, 4.4, 5.8, 7.3, 8.7, 10.2, 11.6, 13.1, 14.5, 16.0, 17.4,
    18.9, 20.3, 21.8, 23.2, 24.7, 26.1, 27.6, 29.0, 30.5, 31.9, 33.4, 34.8,
    36.3, 37.7, 39.2, 40.6, 42.1, 43.5, 45.0]
TX_BEAM_ANGLES = [0, 45.0, 43.5, 42.1, 40.6, 39.2, 37.7, 36.3, 34.8, 33.4, 31.9,
    30.5, 29.0, 27.6, 26.1, 24.7, 23.2, 21.8, 20.3, 18.9, 17.4, 16.0, 14.5,
    13.1, 11.6, 10.2, 8.7, 7.3, 5.8, 4.4, 2.9, 1.5, 0, -1.5, -2.9, -4.4,
    -5.8, -7.3, -8.7, -10.2, -11.6, -13.1, -14.5, -16.0, -17.4, -18.9, -20.3,
    -21.8, -23.2, -24.7, -26.1, -27.6, -29.0, -30.5, -31.9, -33.4, -34.8,
    -36.3, -37.7, -39.2, -40.6, -42.1, -43.5, -45.0]



def update_fixed_tx_beam_in_config(tx_index):
    CONFIG_PATH = "../../../../configurations/config.py" 
    with open(CONFIG_PATH, "r") as f:
        lines = f.readlines()
    with open(CONFIG_PATH, "w") as f:
        for line in lines:
            if line.strip().startswith("fixed_tx_beam"):
                f.write(f"fixed_tx_beam = {tx_index}  # Updated from GT extraction\n")
            else:
                f.write(line)




# =================== STEP 1: Extract all SNR values ===================
print("Step 1: Extracting all SNR values...")
all_snr_data = []
for folder in sorted(os.listdir(base_dir)):
    folder_path = os.path.join(base_dir, folder)
    if not os.path.isdir(folder_path):
        continue
    # match = re.search(r'\d+', folder)
    match = re.search(r'-?\d+', folder)

    if not match:
        continue
    boresight = int(match.group()) 
    snr_file_path = os.path.join(folder_path, "snr_data.csv")
    if not os.path.exists(snr_file_path):
        continue
    try:
        df = pd.read_csv(snr_file_path)
        # df.columns = ["Tx Beam Index", "Tx Beam Angle", "Rx Beam Index", "Rx Beam Angle", "SNR (dB)"]
        df["Boresight"] = boresight
        all_snr_data.append(df)
    except Exception as e:
        print(f"[ERROR] Failed {folder}: {e}")
if all_snr_data:
    df_all = pd.concat(all_snr_data, ignore_index=True)
    df_all.to_csv(os.path.join(base_dir, "forward_all_snr_data.csv"), index=False)
    df_all.to_csv(os.path.join(exp_dir, "forward_all_snr_data.csv"), index=False)
else:
    print("[ERROR] No valid SNR data found to extract.")
    exit(1)


# =================== STEP 1.1: Compute SNR threshold from quantile ===================
print("Step 1.1: Computing quantile-based SNR threshold...")



# Use all SNR values from df_all to compute quantile
snr_column_name = [c for c in df_all.columns if 'snr' in c.lower()][0]
snr_values = pd.to_numeric(df_all[snr_column_name], errors='coerce').dropna().values

if len(snr_values) == 0:
    print("[ERROR] No valid SNR values found in forward_all_snr_data.csv for quantile calculation.")
    exit(1)



# Update config.py with this threshold
def update_snr_threshold(snr_threshold_db):
    CONFIG_PATH = "../../../../configurations/config.py"
    with open(CONFIG_PATH, "r") as f:
        lines = f.readlines()
    with open(CONFIG_PATH, "w") as f:
        for line in lines:
            if line.strip().startswith("SNR_THRESHOLD"):
                f.write(f'SNR_THRESHOLD = {snr_threshold_db:.2f} \n')
            else:
                f.write(line)


threshold_records = []

for q in snr_quantiles:
    snr_threshold_db = np.quantile(snr_values, q)
    threshold_records.append({
        "quantile": q,
        "snr_threshold_db": snr_threshold_db
    })
    print(f"[INFO] Quantile {q:.2f} → SNR threshold = {snr_threshold_db:.2f} dB")

# Save all thresholds (do NOT overwrite config repeatedly)
df_thresh = pd.DataFrame(threshold_records)
df_thresh.to_csv(os.path.join(exp_dir, "snr_thresholds_by_quantile.csv"), index=False)
df_thresh.to_csv(os.path.join(base_dir, "snr_thresholds_by_quantile.csv"), index=False)

# OPTIONAL: only update config with the *primary* quantile
update_snr_threshold(threshold_records[0]["snr_threshold_db"])
