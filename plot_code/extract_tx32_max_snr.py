'''
Extract max SNR for Tx Beam 32 across all Rx Beams from angle folders
'''
import os
import pandas as pd
import re

# Forward Sweep
base_dir = "/media/cse-vuran-32/mmWaveSSD/Nebraska_Hall/Full_Sweep_Experiment/gain13db/NH_full_forward_13db_3m_apr10"
exp_dir = "<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/exhaustive_sweep_13db_apr10"
output_csv = os.path.join(exp_dir, "snr_tx32_max_rx_forwards.csv")


# List to store extracted data
snr_data_tx32 = []

# Iterate through angle directories
for folder in sorted(os.listdir(base_dir)):
    folder_path = os.path.join(base_dir, folder)

    # Extract numeric angle from folder name
    match = re.search(r'\d+', folder)
    if not match:
        print(f"[WARNING] Skipping folder '{folder}' (no numeric angle found).")
        continue
    angle = int(match.group())

    snr_file_path = os.path.join(folder_path, "snr_data.csv")
    if os.path.isdir(folder_path) and os.path.exists(snr_file_path):
        try:
            print(f"[INFO] Processing: {snr_file_path}")

            # Read CSV without header
            df = pd.read_csv(snr_file_path, header=None)

            if df.empty or df.shape[1] < 4:
                print(f"[WARNING] {snr_file_path} is empty or has insufficient columns.")
                continue

            # # Drop first column and assign column names
            # df = df.iloc[:, 1:]
            # df.columns = ["Tx Beam", "Rx Beam", "SNR (dB)"]

            df = df.iloc[:, [2, 4, 5]]
            df.columns = ["Tx Beam Angle", "Rx Beam Angle", "SNR (dB)"]

            # Filter only Tx Beam = 32
            df_filtered = df[df["Tx Beam Index"] == 32]

            if df_filtered.empty:
                print(f"[WARNING] No data for Tx Beam 32 in {snr_file_path}.")
                continue

            # Get row with max SNR for Tx Beam 32
            max_row = df_filtered.loc[df_filtered["SNR (dB)"].idxmax()]
            rx_beam = int(max_row["Rx Beam Angle"])
            snr_value = float(max_row["SNR (dB)"])

            # Append: angle, tx=32, best rx beam, max snr
            snr_data_tx32.append([angle, 32, rx_beam, snr_value])

        except Exception as e:
            print(f"[ERROR] Could not process {snr_file_path}: {e}")

# Save to CSV if data exists
if snr_data_tx32:
    df_output = pd.DataFrame(snr_data_tx32, columns=["Rotor Angle", "Tx Beam Index", "Rx Beam Index", "SNR (dB)"])
    df_output = df_output.sort_values(by="Rotor Angle")
    df_output.to_csv(output_csv, index=False)
    print(f"[SUCCESS] Max SNR per Rx Beam for Tx Beam 32 saved to: {output_csv}")
else:
    print("[INFO] No valid SNR data for Tx Beam 32 found.")
