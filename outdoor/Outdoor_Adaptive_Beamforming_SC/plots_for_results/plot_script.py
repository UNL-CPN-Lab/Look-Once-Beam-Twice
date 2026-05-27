import os
import subprocess

# === New base name to update ===
new_base_name = "nh_jul12_gain9db_12db_16m"

# === Plotting scripts to update and run ===
plot_scripts = [
    # "plot_indices.py",
    "plot_snr_mlp.py",
    "plot_snr_yolor.py",
    "plot_snr_no_guard.py",
    "plot_snr_with_guard.py",
    "plot_time_no_guard.py",
    "plot_time_with_guard.py"
]

def update_base_name_in_file(filepath, new_base_name):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    with open(filepath, 'w') as f:
        for line in lines:
            if "base_name =" in line:
                f.write(f'base_name = "{new_base_name}"\n')
            else:
                f.write(line)

def run_script(script_name):
    print(f"\n--- Running {script_name} ---")
    subprocess.run(["python3", script_name], check=True)

# === Update and run each script ===
for script in plot_scripts:
    if os.path.exists(script):
        update_base_name_in_file(script, new_base_name)
        run_script(script)
        
    else:
        print(f"Script {script} not found.")
