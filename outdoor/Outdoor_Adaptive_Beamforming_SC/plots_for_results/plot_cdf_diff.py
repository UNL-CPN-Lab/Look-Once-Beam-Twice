import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Base folder
base_path = "mavg_Results"

# Color palettes
green_palette = ["#bfd200", "#aacc00", "#80b918", "#55a630", "#2b9348", "#007f5f"]
pink_red_palette = ["#ff85a1", "#ff7096", "#ff5c8a", "#ff477e", "#ff0a54"]
blue_palette = ["#a2c2e0", "#6fa3d9", "#3b84d1", "#1f66c9", "#0048c0"]

# Marker styles
markers = ['o', 's', 'D', '^', 'v', 'X', 'P', '*', '<', '>']

# Thresholds by trial id
threshold_map = {
    't1': 11, 't2': 14, 't3': 17, 't4': 20, 't5': 23,
    't11': 11, 't12': 14, 't13': 17, 't14': 20, 't15': 23
}

# Speed groupings
experiments_by_speed = {
    "1mph": [
        "sc_jul13_gain9db_12db_16m_t1",
        "sc_jul13_gain9db_12db_16m_t2",
        "sc_jul13_gain9db_12db_16m_t3",
        "sc_jul13_gain9db_12db_16m_t4",
        "sc_jul13_gain9db_12db_16m_t5"
    ],
    "5mph": [
        "nh_jul14_gain9db_12db_16m_t2",
        "nh_jul14_gain9db_12db_16m_t3",
        "nh_jul14_gain9db_12db_16m_t4",
        "nh_jul14_gain9db_12db_16m_t5",
        "nh_jul14_gain9db_12db_16m_t6"
    ],
    "8mph": [
        "nh_jul14_gain9db_12db_16m_t11",
        "nh_jul14_gain9db_12db_16m_t12",
        "nh_jul14_gain9db_12db_16m_t13",
        "nh_jul14_gain9db_12db_16m_t14",
        "nh_jul14_gain9db_12db_16m_t15"
    ]
}

palette_map = {
    "1mph": green_palette,
    "5mph": pink_red_palette,
    "8mph": blue_palette
}



# Create and save a plot for each speed group
for speed_label, experiments in experiments_by_speed.items():
    plt.figure(figsize=(10, 6))
    for i, base_filename in enumerate(experiments):
        experiment_folder = os.path.join(base_path, base_filename)
        csv_filename = f"results_{base_filename}.csv"
        csv_path = os.path.join(experiment_folder, csv_filename)

        if not os.path.exists(csv_path):
            print(f"[WARNING] CSV not found: {csv_path}")
            continue

        df = pd.read_csv(csv_path)
        if "SNR (dB)" not in df.columns:
            print(f"[WARNING] 'SNR (dB)' column missing in {csv_filename}")
            continue

        snr_values = df["SNR (dB)"].dropna().values
        if len(snr_values) == 0:
            print(f"[WARNING] No valid SNR values in {csv_filename}")
            continue

        trial_id = base_filename.split('_')[-1]
        threshold = threshold_map.get(trial_id, None)
        if threshold is None:
            print(f"[WARNING] No threshold found for {base_filename}")
            continue

        delta_snr = snr_values - threshold
        sorted_delta_snr = np.sort(delta_snr)
        cdf = np.arange(1, len(sorted_delta_snr) + 1) / len(sorted_delta_snr)

        plt.plot(
            sorted_delta_snr,
            cdf,
            linewidth=3,
            marker=markers[i % len(markers)],
            color=palette_map[speed_label][i % len(palette_map[speed_label])],
            markevery=max(1, len(sorted_delta_snr) // 20),
            markersize=6,
            label=f"VIBE+MA for Th: {threshold} dB"
        )

    plt.axvline(
        x=0,
        linestyle='--',
        color='black',
        linewidth=3,
        alpha=0.8,
        ymin=0.02,
        ymax=0.98,
        label=f"SNR Threshold"
    )


    

    # plt.xlabel(r"$\mathrm{SNR}_{\mathrm{th}} - \mathrm{SNR}$ (dB)", fontsize=18, fontweight='bold')
    plt.xlabel("SNR Normalized to Threshold", fontsize=18, fontweight='bold')
    plt.ylabel("CDF", fontsize=18, fontweight='bold')
    plt.title(f"CDF of $\\mathrm{{SNR}} - \\mathrm{{SNR_{{th}}}}$ for {speed_label} Trials", fontsize=18, fontweight='bold')
    plt.xticks(np.arange(-20, 20, 5), fontsize=16, fontweight='bold')
    plt.yticks(fontsize=16, fontweight='bold')
    plt.grid(True)
    plt.legend(fontsize=14, loc='lower right')
    plt.tight_layout()

    filename = f"normalized_delta_snr_cdf_{speed_label}"
    plt.savefig(f"{filename}.png")
    plt.savefig(f"{filename}.svg")
    plt.savefig(f"{filename}.eps")
