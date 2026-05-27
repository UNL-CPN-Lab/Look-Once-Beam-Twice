import os
import pandas as pd

# ---------- RX Beam Angle Index Lookup ----------
RX_BEAM_ANGLES = [0, -45.0, -43.5, -42.1, -40.6, -39.2, -37.7, -36.3, -34.8, -33.4,
                  -31.9, -30.5, -29.0, -27.6, -26.1, -24.7, -23.2, -21.8, -20.3,
                  -18.9, -17.4, -16.0, -14.5, -13.1, -11.6, -10.2, -8.7, -7.3,
                  -5.8, -4.4, -2.9, -1.5, 0, 1.5, 2.9, 4.4, 5.8, 7.3, 8.7, 10.2,
                  11.6, 13.1, 14.5, 16.0, 17.4, 18.9, 20.3, 21.8, 23.2, 24.7,
                  26.1, 27.6, 29.0, 30.5, 31.9, 33.4, 34.8, 36.3, 37.7, 39.2,
                  40.6, 42.1, 43.5, 45.0]
rx_beam_angle_to_index = {angle: idx for idx, angle in enumerate(RX_BEAM_ANGLES)}

# ---------- 1. Define paths ----------
exp_base_path = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH"
experiment_name = "nh_apr22_gain13db_3m_t5"
experiment_path = os.path.join(exp_base_path, experiment_name)

ground_truth_name = "exhaustive_sweep_13db_apr16"
ground_truth_path = os.path.join(exp_base_path, ground_truth_name)

snr_file = os.path.join(ground_truth_path, "forward_all_snr_data.csv")
results_file = os.path.join(experiment_path, "results.csv")

# ---------- 2. Load data ----------
results_df = pd.read_csv(results_file)
snr_df = pd.read_csv(snr_file)

# ---------- 3. Clean column names ----------
results_df.columns = results_df.columns.str.strip()
snr_df.columns = snr_df.columns.str.strip()

# ---------- 4. Rename columns for matching ----------
results_df = results_df.rename(columns={
    'Boresight Angle': 'boresight',
    'Rx Beam Index (Selected)': 'rx_beam_index',
    'SNR (dB)': 'snr_result'
})

snr_df = snr_df.rename(columns={
    'Boresight Angle': 'boresight',
    'Tx Beam Index': 'tx_beam_index',
    'Rx Beam Index': 'rx_beam_index',
    'SNR (dB)': 'snr_gt'
})

# ---------- 5. Crop boresight range ----------
results_df = results_df[(results_df["boresight"] >= -45) & (results_df["boresight"] <= 45)]

# ---------- 6. Ensure integer type for exact matching ----------
results_df["boresight"] = results_df["boresight"].astype(int)
results_df["rx_beam_index"] = results_df["rx_beam_index"].astype(int)
snr_df["boresight"] = snr_df["boresight"].astype(int)
snr_df["rx_beam_index"] = snr_df["rx_beam_index"].astype(int)

# ---------- 7. Filter SNR data for Tx beam index = 27 ----------
snr_df = snr_df[snr_df["tx_beam_index"] == 30]

# ---------- 8. Calculate rx_beam_angle from index ----------
results_df["rx_beam_angle"] = results_df["rx_beam_index"].apply(
    lambda idx: RX_BEAM_ANGLES[idx] if 0 <= idx < len(RX_BEAM_ANGLES) else None
)


# ---------- 8. Merge SNR_GT into results ----------
merged_df = pd.merge(
    results_df[["boresight", "rx_beam_index", "rx_beam_angle", "snr_result"]],
    snr_df[["boresight", "rx_beam_index", "snr_gt"]],
    on=["boresight", "rx_beam_index"],
    how="left"
)

# ---------- 9. Save merged file ----------
output_csv_path = os.path.join(experiment_path, "rx_beam_with_snr_generated.csv")
merged_df.to_csv(output_csv_path, index=False)

print(f"SNR-augmented results saved to:\n{output_csv_path}")
