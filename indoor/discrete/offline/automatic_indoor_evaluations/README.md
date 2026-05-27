
# Automated Beamforming Experiment Runner

This Python script automates the full workflow for collecting, processing, and evaluating mmWave adaptive beamforming experiments. It is designed for the Outdoor Evaluation testbed and coordinates multiple beamforming stages based on configuration settings.

---

## What It Does

1. **Updates Experiment Metadata:**
   - Sets new `GROUND_TRUTH_NAME` and experiment details (`location`, `gain`, `distance`) in `config.py`.

2. **Runs Ground Truth Sweep:**
   - Launches the `optimized_beam_sweep.py` to perform a full beam sweep at all rotor angles.

3. **Extracts Beam SNR Data:**
   - Calls `run_ground_truth_data_extraction.py` to extract forward SNR data.

4. **Plots Ground Truth Results:**
   - Calls `plot_ground_truth.py` to generate visualizations of the sweep results.

5. **Auto-updates SNR Reference:**
   - Loads `forward_max_snr_per_angle.csv`, filters to boresight range [-30°, +30°], computes average SNR, and updates `reference_max_snr_db` in `config.py`.

6. **Runs Online Beamforming:**
   - Executes `online_main_basic.py` with updated rotor speed and SNR thresholds.
   - Iterates over combinations of SNR thresholds and rotor speeds from pre-defined lists.

---

## Requirements

- Python 3.8+
- Installed dependencies:
  - `pandas`
  - `subprocess`, `os`, `datetime` (standard)
- Directory structure:
  ```
  project_root/
  ├── configurations/
  │   └── config.py
  ├── optimized_beam_sweep.py
  ├── run_ground_truth_data_extraction.py
  ├── plot_ground_truth.py
  ├── online_main_basic.py
  └── automatic.py
  ```

---

## Configurable Parameters

- Edit these in the script:
  ```python
  location = "sc"
  gain = "13db"
  distance = "3m"
  test_number = "t4"
  ROTOR_SPEEDS = [1]
  SNR_FACTORS = [0.4]
  ```

- These values will be written into `config.py` and used downstream.

---

## Usage

From the terminal:
```bash
python3 this_script.py
```

It will sequentially:
1. Run the ground truth sweep
2. Extract and plot results
3. Update config
4. Run the online beamforming experiments

---

## Output Files

- **Experiment Data:** Saved under:
  ```
  /experiments/Adaptive_Beamforming_SC/{experiment_name}/
  ```

- **CSV Outputs:**
  - `forward_max_snr_per_angle.csv`
  - `snr_data.csv` (per angle folder)
  - `experiment_metadata.json`

- **Log Files:** All steps print status and errors to console for debugging.
