'''
Extract max SNR value and corresponding Tx and Rx beams from all angle folders
'''
import os
import pandas as pd
import re

# Forward Sweep
base_dir = "/media/cse-vuran-32/mmWaveSSD/Nebraska_Hall/Full_Sweep_Experiment/gain13db/NH_full_forward_13db_3m_apr16"
exp_dir = "<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/exhaustive_sweep_13db_apr16"
output_csv = os.path.join(base_dir, "forward_max_snr_per_angle.csv")


# List to store extracted data
max_snr_data = []

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

         
            df = df.iloc[:, [2, 4, 5]]
            df.columns = ["Tx Beam Angle", "Rx Beam Angle", "SNR (dB)"]

            # Find the row with the maximum SNR value
            max_row = df.loc[df["SNR (dB)"].idxmax()]

            # Append to the list
            max_snr_data.append([
                angle,
                max_row["Tx Beam Angle"],
                max_row["Rx Beam Angle"],
                max_row["SNR (dB)"]
            ])

        except Exception as e:
            print(f"[ERROR] Could not process {snr_file_path}: {e}")

# Save to CSV if data exists
if max_snr_data:
    df_output = pd.DataFrame(max_snr_data, columns=["Rotor Angle", "Tx Beam Angle", "Rx Beam Angle", "SNR (dB)"])
    df_output = df_output.sort_values(by="Rotor Angle")
    df_output.to_csv(output_csv, index=False)
    print(f"[SUCCESS] Max SNR data saved to: {output_csv}")
else:
    print("[INFO] No valid SNR data found.")
