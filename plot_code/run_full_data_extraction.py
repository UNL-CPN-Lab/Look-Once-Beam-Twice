
# =================== SETUP ===================
import os
import pandas as pd
import re

# Update these paths as needed
base_dir = "/media/cse-vuran-32/mmWaveSSD/Nebraska_Hall/Full_Sweep_Experiment/gain13db/NH_full_forward_13db_3m_apr16"
exp_dir = "<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/exhaustive_sweep_13db_apr16"

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
    match = re.search(r'\d+', folder)
    if not match:
        continue
    rotor_angle = int(match.group()) - 90
    snr_file_path = os.path.join(folder_path, "snr_data.csv")
    if not os.path.exists(snr_file_path):
        continue
    try:
        df = pd.read_csv(snr_file_path, header=None)
        if df.empty or df.shape[1] < 6:
            continue
        df = df.iloc[:, [1, 3, 5]]
        df.columns = ["Tx Beam Index", "Rx Beam Index", "SNR (dB)"]
        df["Tx Beam Angle"] = df["Tx Beam Index"].apply(lambda i: TX_BEAM_ANGLES[int(i)])
        df["Rx Beam Angle"] = df["Rx Beam Index"].apply(lambda i: RX_BEAM_ANGLES[int(i)])
        df["Boresight Angle"] = rotor_angle
        all_snr_data.append(df)
    except Exception as e:
        print(f"[ERROR] Failed {folder}: {e}")
if all_snr_data:
    df_all = pd.concat(all_snr_data, ignore_index=True)
df_all.to_csv(os.path.join(base_dir, "forward_all_snr_data.csv"), index=False)
df_all.to_csv(os.path.join(exp_dir, "forward_all_snr_data.csv"), index=False)

# =================== STEP 2: Extract max SNR for each boresight ===================
print("Step 2: Extracting max SNR per boresight...")
max_snr_data = []
for folder in sorted(os.listdir(base_dir)):
    folder_path = os.path.join(base_dir, folder)
    match = re.search(r'\d+', folder)
    if not match:
        continue
    angle = int(match.group())
    snr_file_path = os.path.join(folder_path, "snr_data.csv")
    if os.path.exists(snr_file_path):
        df = pd.read_csv(snr_file_path, header=None)
        if df.empty or df.shape[1] < 6:
            continue
        df = df.iloc[:, [2, 4, 5]]
        df.columns = ["Tx Beam Angle", "Rx Beam Angle", "SNR (dB)"]
        max_row = df.loc[df["SNR (dB)"].idxmax()]
        max_snr_data.append([angle, max_row["Tx Beam Angle"], max_row["Rx Beam Angle"], max_row["SNR (dB)"]])
if max_snr_data:
    df_max = pd.DataFrame(max_snr_data, columns=["Rotor Angle", "Tx Beam Angle", "Rx Beam Angle", "SNR (dB)"])
df_max.to_csv(os.path.join(base_dir, "forward_max_snr_per_angle.csv"), index=False)
df_max.to_csv(os.path.join(exp_dir, "forward_max_snr_per_angle.csv"), index=False)

# =================== STEP 3: Find most frequent Tx Beam ===================
print("Step 3: Finding most common Tx Beam in max SNR data...")
most_common_tx = df_max["Tx Beam Angle"].mode().iloc[0]
print(f"[INFO] Most common Tx Beam Angle: {most_common_tx}")

# =================== STEP 4: Extract best Rx beam per angle for fixed Tx ===================
print("Step 4: Extracting best Rx beam for Tx =", most_common_tx)
tx_fixed = most_common_tx
filtered_data = []
for folder in sorted(os.listdir(base_dir)):
    folder_path = os.path.join(base_dir, folder)
    match = re.search(r'\d+', folder)
    if not match:
        continue
    angle = int(match.group())
    boresight_angle = angle - 90
    snr_file_path = os.path.join(folder_path, "snr_data.csv")
    if os.path.exists(snr_file_path):
        df = pd.read_csv(snr_file_path, header=None)
        if df.empty or df.shape[1] < 6:
            continue
        df = df.iloc[:, [1, 3, 5]]
        df.columns = ["Tx Beam Index", "Rx Beam Index", "SNR (dB)"]
        df = df[df["Tx Beam Index"] == TX_BEAM_ANGLES.index(tx_fixed)]
        if df.empty:
            continue
        max_row = df.loc[df["SNR (dB)"].idxmax()]
        filtered_data.append({
            "Boresight Angle": boresight_angle,
            "Tx Beam Index": int(max_row["Tx Beam Index"]),
            "Rx Beam Index": int(max_row["Rx Beam Index"]),
            "SNR (dB)": max_row["SNR (dB)"]
        })
if filtered_data:
    df_filtered = pd.DataFrame(filtered_data)
df_filtered.to_csv(os.path.join(base_dir, "tx{}_max_snr.csv".format(TX_BEAM_ANGLES.index(tx_fixed))), index=False)
df_filtered.to_csv(os.path.join(exp_dir, "tx{}_max_snr.csv".format(TX_BEAM_ANGLES.index(tx_fixed))), index=False)

# =================== STEP 5: Extract Tx=tx_fixed, Rx=0 and Tx=0, Rx=0 pairs ===================
print("Step 5: Extracting Tx=2.9°, Rx=0 and Tx=0, Rx=0 SNR pairs...")
def extract_fixed_pair(tx_angle, rx_angle, output_filename):
    results = []
    for folder in sorted(os.listdir(base_dir)):
        folder_path = os.path.join(base_dir, folder)
        match = re.search(r'\d+', folder)
        if not match:
            continue
        angle = int(match.group())
        snr_file_path = os.path.join(folder_path, "snr_data.csv")
        if os.path.exists(snr_file_path):
            df = pd.read_csv(snr_file_path, header=None)
            if df.empty or df.shape[1] < 6:
                continue
            df = df.iloc[:, [2, 4, 5]]
            df.columns = ["Tx Beam Angle", "Rx Beam Angle", "SNR (dB)"]
            df_filtered = df[(df["Tx Beam Angle"] == tx_angle) & (df["Rx Beam Angle"] == rx_angle)]
            if not df_filtered.empty:
                results.append([angle, df_filtered.iloc[0]["SNR (dB)"]])
    if results:
        df_out = pd.DataFrame(results, columns=["Rotor Angle", "SNR (dB)"])
        df_out.to_csv(os.path.join(base_dir, output_filename), index=False)
        df_out.to_csv(os.path.join(exp_dir, output_filename), index=False)

extract_fixed_pair(tx_fixed, 0, "snr_tx{tx_fixed}_rx32_forward.csv")
extract_fixed_pair(0, 0, "snr_tx32_rx32_forward.csv")
print("\nAll data extraction steps completed.")
