import os
import pandas as pd
import re

# --- CONFIGURATION ---
base_dir = "/media/cse-vuran-32/mmWaveSSD/Nebraska_Hall/Full_Sweep_Experiment/gain13db/NH_full_forward_13db_3m_apr16"
output_csv = os.path.join(base_dir, "snr_selected_tx_rx.csv")
tx_beam_input = 32  # Set user-provided Tx Beam Index
rx_beam_input = 32  # Set user-provided Rx Beam Index

# --- PROCESSING ---
snr_data_selected = []

for folder in sorted(os.listdir(base_dir)):
    folder_path = os.path.join(base_dir, folder)

    if not os.path.isdir(folder_path):
        continue

    # Parse rotor angle from folder name
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

        filtered_df = df[
            (df["Tx Beam Index"] == tx_beam_input) & (df["Rx Beam Index"] == rx_beam_input)
        ]

        if not filtered_df.empty:
            snr_value = filtered_df.iloc[0]["SNR (dB)"]
            snr_data_selected.append([rotor_angle, snr_value])

    except Exception as e:
        continue

# --- SAVE AND DISPLAY ---
if snr_data_selected:
    df_output = pd.DataFrame(snr_data_selected, columns=["Rotor Angle", "SNR (dB)"])
    df_output = df_output.sort_values(by="Rotor Angle")
    df_output.to_csv(output_csv, index=False)

    import ace_tools as tools; tools.display_dataframe_to_user(name="Filtered SNR Data", dataframe=df_output)
else:
    df_output = pd.DataFrame(columns=["Rotor Angle", "SNR (dB)"])  # empty frame
    tools.display_dataframe_to_user(name="Filtered SNR Data", dataframe=df_output)
