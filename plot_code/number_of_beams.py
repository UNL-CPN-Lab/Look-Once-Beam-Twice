# Re-import necessary libraries after code execution environment reset
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ---------- 1. Define experiment path ----------
exp_base_path = "<DATA_ROOT>/mmwave_vision_research/evk06002/eder_evk-Release_20220406_1715/NH_eval/Adaptive_Beamforming_NH"
experiment_name = "nh_apr22_gain13db_3m_t6"
experiment_path = os.path.join(exp_base_path, experiment_name)
csv_path = os.path.join(experiment_path, "results.csv")

# ---------- 2. Load CSV ----------
df = pd.read_csv(csv_path)



# Plot a barplot of beams checked vs. boresight angle
plt.figure(figsize=(18, 6))
sns.set_context("notebook", font_scale=1.6)
sns.barplot(data=df, x="Boresight Angle", y="Beams Checked in Search", palette="viridis")

plt.title("Number of Beams Checked vs Boresight Angle")
plt.xlabel("Boresight Angle (°)")
plt.ylabel("Number of Beams Checked")
plt.xticks(rotation=45, fontsize= 12)
plt.grid(True, axis='y')
plt.tight_layout()

plt.show()

# Save in multiple formats
plot_base_name = f"number_of_beams_{experiment_name}"
plt.savefig(os.path.join(experiment_path, f"{plot_base_name}.png"), format='png')
plt.savefig(os.path.join(experiment_path, f"{plot_base_name}.svg"), format='svg')
plt.savefig(os.path.join(experiment_path, f"{plot_base_name}.eps"), format='eps')
plt.show()

