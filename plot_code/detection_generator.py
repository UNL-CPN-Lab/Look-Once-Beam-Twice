import os
import pandas as pd

# Load detections
detections_df = pd.read_csv('<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/nh_apr4_gain14db_3m_t1/detections.csv')




print(detections_df.head())
print(detections_df.columns)

# Set constant TX beam
tx_beam_fixed = 32

# Base directory path
base_dir = '/media/cse-vuran-32/mmWaveSSD/Nebraska_Hall/NH_full_forward_14db_4.5m_sweep'

# Initialize SNR column
detections_df['snr'] = None

# Loop through detections
for idx, row in detections_df.iterrows():
    try:
        if pd.isna(row['Rx Beam Index']):
            continue

        rx_beam = int(row['Rx Beam Index'])
        # if rx_beam == 32:
        #     continue  # Skip N/A

        angle = int(row['Boresight Angle'])
        snr_file = os.path.join(base_dir, f'angle_{angle}', 'snr_data.csv')

        if not os.path.exists(snr_file):
            print(f"Missing file: angle_{angle}/snr_data.csv")
            continue

        # Load the file with no headers
        snr_df = pd.read_csv(snr_file, header=None, names=['sample', 'tx', 'rx', 'snr'])

        # Filter for TX = 32, RX = desired
        matching = snr_df[(snr_df['tx'] == tx_beam_fixed) & (snr_df['rx'] == rx_beam)]

        if matching.empty:
            print(f"No matching SNR for angle {angle}, TX 32, RX {rx_beam}")
            continue

        # Take the mean or first — here using mean
        detections_df.at[idx, 'snr'] = matching['snr'].mean()

    except Exception as e:
        print(f"Error at row {idx} → {e}")

# Save the new CSV
detections_df.to_csv('<DATA_ROOT>/mmWave_sivers/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH/nh_apr4_gain14db_3m_t1/detections_with_snr2.csv', index=False)