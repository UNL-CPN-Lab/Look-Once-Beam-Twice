# import numpy as np
# import matplotlib.pyplot as plt

# # === Matplotlib Config ===
# plt.rcParams.update({
#     'pdf.fonttype': 42,
#     'ps.fonttype': 42,
#     'text.usetex': False,
#     'font.size': 26,
#     'mathtext.fontset': 'dejavusans',
#     'font.family': 'DejaVu Sans'
# })

# # === Data ===
# quantiles = [r"$Q_{0.80}$", r"$Q_{0.90}$", r"$Q_{0.95}$"]

# offline_yolor = [3.8, 4.0, 4.7]
# online_yolor  = [5.0, 5.9, 33.1]
# offline_ma    = [3.8, 3.8, 2.4]
# online_ma     = [2.7, 4.5, 3.6]

# # === Grouped bar positions ===
# x = np.arange(len(quantiles))  # one group per quantile
# bar_width = 0.2  # narrow bars, no gaps inside groups

# fig, ax = plt.subplots(figsize=(9,6))

# # === Plot Bars with no gaps inside groups ===




# ax.bar(x + 1.5*bar_width, online_ma, bar_width,
#        label="VIBE-MA Online", color="#a50104", edgecolor='white', hatch='++', linewidth=1.5)

# ax.bar(x - 0.5*bar_width, offline_ma, bar_width,
#        label="VIBE-MA Offline", color="#ed6a5e", edgecolor='white', hatch='xx', linewidth=1.5)

# ax.bar(x - 1.5*bar_width, offline_yolor, bar_width,
#        label="VIBE-YOLOR Offline", color="#81a4cd", edgecolor='white', hatch='//', linewidth=1.5)

# ax.bar(x + 0.5*bar_width, online_yolor, bar_width,
#        label="VIBE-YOLOR Online", color="#175676", edgecolor='white', hatch='\\\\', linewidth=1.5)





# # === Formatting ===
# ax.set_xticks(x)
# ax.set_xticklabels(["Q₀.₈₀", "Q₀.₉₀", "Q₀.₉₅"])
# ax.set_ylabel("Outage (%)")
# ax.set_xlabel("Quantile Based Threshold")

# # === Legend flipped (reverse order) ===
# handles, labels = ax.get_legend_handles_labels()
# ax.legend(handles[::-1], labels[::-1], frameon=False, loc="upper left")

# ax.grid(axis='y', linestyle='--', alpha=0.5)

# # === Save ===
# plt.tight_layout()
# plt.savefig("outage_vibe_vertical_grouped.svg", format="svg", dpi=600, bbox_inches="tight")
# plt.savefig("outage_vibe_vertical_grouped.png", format="png", dpi=600, bbox_inches="tight")
# plt.savefig("outage_vibe_vertical_grouped.pdf", format="pdf", dpi=600, bbox_inches="tight")

# plt.show()
import numpy as np
import matplotlib.pyplot as plt

# === Matplotlib Config ===
plt.rcParams.update({
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'text.usetex': False,
    'font.size': 26,
    'mathtext.fontset': 'dejavusans',
    'font.family': 'DejaVu Sans'
})

# === Data ===
quantiles = [r"$Q_{0.80}$", r"$Q_{0.90}$", r"$Q_{0.95}$"]

offline_yolor = [3.8, 4.0, 4.7]
online_yolor  = [5.0, 5.9, 33.1]
offline_ma    = [3.8, 3.8, 2.4]
online_ma     = [2.7, 4.5, 3.6]

# === Grouped bar positions ===
x = np.arange(len(quantiles))  # one group per quantile
bar_width = 0.2  # narrow bars, no gaps inside groups

fig, ax = plt.subplots(figsize=(9,6))

# === Plot Bars in requested order ===
ax.bar(x - 1.5*bar_width, offline_ma, bar_width,
       label="VIBE-MA (Offline)", color="#ed6a5e", edgecolor='white', hatch='xx', linewidth=1.5)

ax.bar(x - 0.5*bar_width, online_ma, bar_width,
       label="VIBE-MA (Online)", color="#a50104", edgecolor='white', hatch='++', linewidth=1.5)

ax.bar(x + 0.5*bar_width, offline_yolor, bar_width,
       label="VIBE-YOLOR (Offline)", color="#81a4cd", edgecolor='white', hatch='//', linewidth=1.5)

ax.bar(x + 1.5*bar_width, online_yolor, bar_width,
       label="VIBE-YOLOR (Online)", color="#175676", edgecolor='white', hatch='\\\\', linewidth=1.5)

# === Formatting ===
ax.set_xticks(x)
ax.set_xticklabels(["Q₀.₈₀", "Q₀.₉₀", "Q₀.₉₅"])
ax.set_ylabel("Outage (%)")
ax.set_xlabel("Quantile Based Threshold")

# === Legend in the same order as bars ===
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, frameon=False, loc="upper left")

ax.grid(axis='y', linestyle='--', alpha=0.5)

# === Save ===
plt.tight_layout()
plt.savefig("outage_vibe_vertical_grouped.svg", format="svg", dpi=600, bbox_inches="tight")
plt.savefig("outage_vibe_vertical_grouped.png", format="png", dpi=600, bbox_inches="tight")
plt.savefig("outage_vibe_vertical_grouped.pdf", format="pdf", dpi=600, bbox_inches="tight")

plt.show()
