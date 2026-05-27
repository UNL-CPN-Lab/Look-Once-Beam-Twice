# Outdoor · VIBE-MLP training

Scripts that build the training dataset and train the `OffsetMLP` used by `outdoor_online_main_mlp.py`. The MLP predicts a corrective beam offset given `[boresight, threshold_snr, yolo_beam, snr_yolo]`; once trained it replaces VIBE-MA's moving-average history with a single learned correction step.

Trained artifacts (datasets, scalers, `.pt` weights) live in the sibling [../mlp_models/](../mlp_models/) folder.

## Files

| File | Role |
|---|---|
| `dataset_mlp_new.py` | Builds the training CSV by replaying prior VIBE-MA experiment outputs. For each experiment under `<DATA_ROOT>/.../Outdoor_Adaptive_Beamforming_SC/mavg_Results/<exp_name>/`, reads `results_<exp_name>.csv` + `metadata.json` and appends rows `[Boresight, snr_thresh_db, YOLO-predicted beam, Initial SNR, Offset Error]` to `../mlp_models/offset_dataset_nh_outdoor.csv`. |
| `train_mlp.py` | Trains `OffsetMLP` (3-layer FC, 128 units, LayerNorm + ReLU + Dropout(0.2), Smooth L1, Adam) on the dataset. Writes `../mlp_models/offset_mlp_model_<run>.pt` and the fitted `StandardScaler` to `../mlp_models/offset_scaler_<run>.pkl`. Also renders a predicted-vs-actual scatter plot. |
| `ground_truth_sc_beam_results.csv` | Reference output of `extract_beam_indices_gt.py` — best (TX, RX) beam pair per ground-truth point for the SC dataset. Used for sanity-checking the dataset. |

## Workflow

1. **Capture VIBE-MA experiments** under `Outdoor_Adaptive_Beamforming_SC/mavg_Results/` (via [../outdoor_online_main_mavg.py](../outdoor_online_main_mavg.py)) — each run produces `results_*.csv` + `metadata.json`.
2. **Build the dataset.** Edit the experiment-name pattern + range in `dataset_mlp_new.py` to match the runs you want included, then:
   ```bash
   cd outdoor/mlp_training
   python3 dataset_mlp_new.py
   ```
   This appends to `../mlp_models/offset_dataset_nh_outdoor.csv`.
3. **Train.** Edit the dataset filename in `train_mlp.py:106` if you used a different name, then:
   ```bash
   python3 train_mlp.py
   ```
   Emits `offset_mlp_model_nh_outdoor.pt` + `offset_scaler_nh_outdoor.pkl` into `../mlp_models/`.
4. **Use.** Point [../outdoor_online_main_mlp.py](../outdoor_online_main_mlp.py) (or `alt_runners/*_mlp.py`) at the new weights — the runner currently loads `mlp_models/offset_mlp_model_<...>.pt` + matching scaler.

## Prerequisites

- A populated `Outdoor_Adaptive_Beamforming_SC/mavg_Results/` tree (run VIBE-MA first).
- `<DATA_ROOT>` set to your experiment storage volume in [../../configurations/config.py](../../configurations/config.py).
- Python deps: `torch`, `scikit-learn`, `joblib`, `matplotlib` (already in `../../requirements.txt`).

## Notes

- Network architecture lives **in the runner** (`outdoor_online_main_mlp.py`'s `OffsetMLP` class), not in `train_mlp.py`. The trainer defines its own copy; if you change the architecture, update both.
- The current dataset script assumes the experiment naming convention `nh_jul14_gain9db_12db_16m_t{t}` for `t=1..14`. Edit `dataset_mlp_new.py:46-47` to match your experiments.

Author: Apala Pramanik
