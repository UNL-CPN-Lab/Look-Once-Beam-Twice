
# =================== SETUP ===================
import os
import pandas as pd
import re
import sys

# Add the root path so we can import the configurations module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)


from configurations.utils import *


# # Update these paths as needed
# base_dir = "<DATA_ROOT>/mmWaveSSD/Schorr_Center/Full_Sweep_Experiment/gain13db/Optimized_exhaustive_sweep_sc_jun18_gain13db_3m_t2"
# exp_dir = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/experiments/Adaptive_Beamforming_SC/optimized_exhaustive_sweep_13db_jun18_sc"
# os.makedirs(exp_dir, exist_ok=True)


# Read command-line arguments
if len(sys.argv) != 2:
    print("Usage: python run_full_data_extraction.py  <exp_dir>")
    sys.exit(1)

base_name = sys.argv[1]


base_dir = f"<DATA_ROOT>/mmWaveSSD/Schorr_Center/Full_Sweep_Experiment/gain13db/{base_name}"
exp_dir = f"<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/experiments/Adaptive_Beamforming_SC/{base_name}"
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



# =================== STEP 2: Extract max SNR for each boresight ===================
print("Step 2: Extracting max SNR per boresight...")
max_snr_data = []
for folder in sorted(os.listdir(base_dir)):
    folder_path = os.path.join(base_dir, folder)
    match = re.search(r'-?\d+', folder)

    if not match:
        continue
    boresight = int(match.group())
    snr_file_path = os.path.join(folder_path, "snr_data.csv")
    if os.path.exists(snr_file_path):
        # df = pd.read_csv(snr_file_path)
        # max_row = df.loc[df["SNR (dB)"].idxmax()]
        df = pd.read_csv(snr_file_path)
        df["SNR (dB)"] = pd.to_numeric(df["SNR (dB)"], errors='coerce')  # Add this line
        max_row = df.loc[df["SNR (dB)"].idxmax()]

        max_snr_data.append([
            boresight,
            max_row["Tx Beam Index"],
            max_row["Tx Beam Angle"],
            max_row["Rx Beam Index"],
            max_row["Rx Beam Angle"],
            max_row["SNR (dB)"]
        ])

if max_snr_data:
    df_max = pd.DataFrame(max_snr_data, columns=["Boresight", "Tx Beam Index", "Tx Beam Angle", "Rx Beam Index", "Rx Beam Angle", "SNR (dB)"])
df_max.to_csv(os.path.join(base_dir, "forward_max_snr_per_angle.csv"), index=False)
df_max.to_csv(os.path.join(exp_dir, "forward_max_snr_per_angle.csv"), index=False)




# =================== STEP 3: Find most frequent Tx Beam ===================
print("Step 3: Finding most common Tx Beam in max SNR data...")
# tx_fixed_beam_index = int(df_max["Tx Beam Index"].mode().iloc[0])
tx_fixed_beam_index = int(df_max["Tx Beam Index"].mode().min())
update_fixed_tx_beam_in_config(tx_fixed_beam_index)


print(f"[INFO] Most common Tx Beam Index : {tx_fixed_beam_index}")



# =================== STEP 4: Extract best Rx beam per angle for fixed Tx ===================
print("Step 4: Extracting best Rx beam for Tx =", tx_fixed_beam_index)


filtered_data = []
for folder in sorted(os.listdir(base_dir)):
    folder_path = os.path.join(base_dir, folder)
    match = re.search(r'-?\d+', folder)

    if not match:
        continue
    boresight = int(match.group())

    
    snr_file_path = os.path.join(folder_path, "snr_data.csv")
    if os.path.exists(snr_file_path):
        # df = pd.read_csv(snr_file_path)
        # df = pd.read_csv(snr_file_path)
        # df["SNR (dB)"] = pd.to_numeric(df["SNR (dB)"], errors='coerce')  # Add this line
        # max_row = df.loc[df["SNR (dB)"].idxmax()]

        # df = df[df["Tx Beam Index"] == tx_fixed_beam_index]
        
        df = pd.read_csv(snr_file_path)
        df["SNR (dB)"] = pd.to_numeric(df["SNR (dB)"], errors='coerce')
        df = df[df["Tx Beam Index"] == tx_fixed_beam_index]  # <- First filter
        if df.empty:
            continue
        max_row = df.loc[df["SNR (dB)"].idxmax()]  # <- Then compute max row 
        filtered_data.append({
            "Boresight": boresight,
            "Tx Beam Index": int(max_row["Tx Beam Index"]),
            "Rx Beam Index": int(max_row["Rx Beam Index"]),
            "SNR (dB)": max_row["SNR (dB)"]
        })


# if filtered_data:
df_filtered = pd.DataFrame(filtered_data)
df_filtered.to_csv(os.path.join(base_dir, f"tx{tx_fixed_beam_index}_max_snr.csv"), index=False)
df_filtered.to_csv(os.path.join(exp_dir, f"tx{tx_fixed_beam_index}_max_snr.csv"), index=False)
    




# =================== STEP 5: Extract Tx=fixed, Rx=0 and Tx=0, Rx=0 pairs ===================

def extract_fixed_pair(tx_index, rx_index, output_filename):
    results = []
    for folder in sorted(os.listdir(base_dir)):
        folder_path = os.path.join(base_dir, folder)
        match = re.search(r'-?\d+', folder)

        if not match:
            continue
        boresight = int(match.group())

        snr_file_path = os.path.join(folder_path, "snr_data.csv")
        if os.path.exists(snr_file_path):
            df = pd.read_csv(snr_file_path)
            df_filtered = df[(df["Tx Beam Index"] == tx_index) & (df["Rx Beam Index"] == rx_index)]
            if not df_filtered.empty:
                results.append([boresight, df_filtered.iloc[0]["SNR (dB)"]])
    if results:
        df_out = pd.DataFrame(results, columns=["Boresight", "SNR (dB)"])
        df_out.to_csv(os.path.join(base_dir, output_filename), index=False)
        df_out.to_csv(os.path.join(exp_dir, output_filename), index=False)

print(f"Step 5: Extracting Tx={tx_fixed_beam_index}°, Rx=32 and Tx=32")

extract_fixed_pair(tx_fixed_beam_index, 32, f"snr_tx{tx_fixed_beam_index}_rx32_forward.csv")
extract_fixed_pair(32, 32, "snr_tx32_rx32_forward.csv")


print("\nAll data extraction steps completed.")


