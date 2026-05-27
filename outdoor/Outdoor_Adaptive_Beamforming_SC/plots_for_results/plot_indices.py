import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.ticker import MaxNLocator

# === Style Parameters ===
linewidth_val = 4
markersize_val = 8

# === Base Filename ===
base_name = "nh_jul12_gain9db_12db_16m"

# === RX Beam Angle Lookup Table ===
RX_BEAM_ANGLES = [
     0.0, -45.0, -43.5, -42.1, -40.6, -39.2, -37.7, -36.3, -34.8, -33.4, -31.9,
    -30.5, -29.0, -27.6, -26.1, -24.7, -23.2, -21.8, -20.3, -18.9, -17.4,
    -16.0, -14.5, -13.1, -11.6, -10.2,  -8.7,  -7.3,  -5.8,  -4.4,  -2.9,  -1.5,
     0,     1.5,   2.9,   4.4,   5.8,   7.3,   8.7,  10.2,  11.6,  13.1,  14.5,
    16.0,  17.4,  18.9,  20.3,  21.8,  23.2,  24.7,  26.1,  27.6,  29.0,  30.5,
    31.9,  33.4,  34.8,  36.3,  37.7,  39.2,  40.6,  42.1,  43.5,  45.0
]

TX_BEAM_ANGLES = [
     0.0,  45.0,  43.5,  42.1,  40.6,  39.2,  37.7,  36.3,  34.8,  33.4,  31.9,
    30.5,  29.0,  27.6,  26.1,  24.7,  23.2,  21.8,  20.3,  18.9,  17.4,  16.0,
    14.5,  13.1,  11.6,  10.2,   8.7,   7.3,   5.8,   4.4,   2.9,   1.5,   0,
    -1.5,  -2.9,  -4.4,  -5.8,  -7.3,  -8.7, -10.2, -11.6, -13.1, -14.5, -16.0,
   -17.4, -18.9, -20.3, -21.8, -23.2, -24.7, -26.1, -27.6, -29.0, -30.5, -31.9,
   -33.4, -34.8, -36.3, -37.7, -39.2, -40.6, -42.1, -43.5, -45.0
]

def rx_angle_from_index(index):
    if 0 <= index < len(RX_BEAM_ANGLES):
        return RX_BEAM_ANGLES[index]
    raise ValueError(f"Invalid RX beam index: {index}")

def tx_angle_from_index(index):
    if 0 <= index < len(TX_BEAM_ANGLES):
        return TX_BEAM_ANGLES[index]
    raise ValueError(f"Invalid TX beam index: {index}")

# === Model folders and threshold tags ===
experiments = {
    "mlp_Results": ["t1"],
    "yolor_Results": ["t1"],
    "mavg_Results": [f"t{i}" for i in range(1, 7)]
}

for model_folder, tags in experiments.items():
    for tag in tags:
        subfolder = f"{base_name}_{tag}"
        experiment_folder = os.path.join(model_folder, subfolder)
        csv_filename = f"results_{base_name}_{tag}.csv"
        csv_path = os.path.join(experiment_folder, csv_filename)

        if not os.path.exists(csv_path):
            print(f"Skipping missing file: {csv_path}")
            continue

        # === Load Data ===
        df = pd.read_csv(csv_path)
        x_vals = np.arange(len(df))

        if model_folder == "mavg_Results":
            if "Rx Beam Index(Selected)" not in df.columns:
                print(f"Missing  RX beam index columns in {csv_path}")
                continue
                
            elif "TX Beam Index" not in df.columns:
                print(f"Missing TX beam index columns in {csv_path}")
                continue
            try:

                rx_beam = [rx_angle_from_index(int(idx)) for idx in df["Rx Beam Index(Selected)"].values]
                tx_beam = [tx_angle_from_index(int(idx)) for idx in df["TX Beam Index"].values]
            except Exception as e:
                print(f"Error converting indices in {csv_path}: {e}")
                continue
        else:
            if "Rx Beam Angle" not in df.columns or "TX Beam Angle" not in df.columns:
                print(f"Missing beam angle columns in {csv_path}")
                continue
            rx_beam = df["Rx Beam Angle"].values
            tx_beam = df["Tx Beam Angle"].values

        # === Plot Settings ===
        plt.figure(figsize=(8, 6))

        # === Plot Beam Angles ===
        plt.plot(
            x_vals,
            rx_beam,
            label="RX Beam Angle",
            linewidth=linewidth_val,
            marker='o',
            markersize=markersize_val,
            color="blue"
        )

        plt.plot(
            x_vals,
            tx_beam,
            label="TX Beam Angle",
            linewidth=linewidth_val,
            marker='s',
            markersize=markersize_val,
            color="red"
        )

        # === Labels and Ticks ===
        plt.xlabel("Index", fontsize=16, fontweight='bold')
        plt.ylabel("Beam Angle (°)", fontsize=16, fontweight='bold')
        plt.xticks(fontsize=16, fontweight='bold')
        plt.yticks(fontsize=16, fontweight='bold')

        # === Force integer ticks on x-axis ===
        plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))

        # === Legend and Grid ===
        plt.legend(fontsize=14, loc='upper right', prop={'weight': 'bold'})
        plt.grid(True)
        plt.tight_layout()

        # === Save Plot ===
        base_plotname = "rx_tx_beam_angles_vs_index"
        for ext in ['eps', 'svg', 'png']:
            save_path = os.path.join(experiment_folder, f"{base_plotname}.{ext}")
            plt.savefig(save_path, format=ext, dpi=600)

        plt.close()
        print(f"Saved plot to {experiment_folder}")
