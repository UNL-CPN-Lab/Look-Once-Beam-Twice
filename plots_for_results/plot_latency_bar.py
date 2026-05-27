import matplotlib.pyplot as plt

# === Step Names and Time Values (in ms) ===
labels = [
    "Communication Delay",
    "Capture Image",
    "Detect BS",
    "Estimate Beam Index",
    "Communication Delay",
    "Set RX Beam",
    "Communication Delay",
    "Set TX Beam",
    "Communication Delay",
    "Stabilize UE Beam",
    "Measure SNR"
]
 

hex_colors = ["#a7eaf6","#c3f73a","#95e06c","#68b684","#a7eaf6", "#FCBF49","#a7eaf6", "#ffadad","#a7eaf6","#edbff9", "#d3aef2"]


values = [1, 1, 75, 1, 1, 50, 1, 50, 1, 15, 35]
total_time = 231



# hex_colors = ["#84D1F0","#ACD86E","#F7D85B","#F49366","#84D1F0","#F77CB1","#84D1F0","#D569CE","#84D1F0","#A574EB","#77A9F8"]


# === Plot Setup ===
plt.figure(figsize=(12, 1.2))
bar_y = 0
bar_height = 0.8
x_start = 0

# === Draw Bar Without Text ===
for value, color in zip(values, hex_colors):
    if value == 0:
        continue
    plt.barh(
        y=bar_y,
        width=value,
        left=x_start,
        color=color,
        height=bar_height,
        zorder=1
    )
    x_start += value

# === Clean Plot ===
plt.axis('off')
plt.xlim(0, total_time + 20)
plt.ylim(-0.5, 1)

# === Save Plot ===
plt.savefig("latency_breakdown_stacked_no_labels.svg", format='svg', dpi=600, bbox_inches='tight')
plt.show()

# === Print Values to Terminal ===
print("=== Latency Breakdown ===")
for label, value in zip(labels, values):
    if value == 0:
        continue
    percent = round((value / total_time) * 100)
    print(f"{label:25}: {value} ms → {percent:>5.6f}%")
