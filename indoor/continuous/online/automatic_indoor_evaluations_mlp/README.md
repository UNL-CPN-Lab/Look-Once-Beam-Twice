# Indoor · Continuous · VIBE-MLP (online)

Online, end-to-end evaluation of **VIBE-MLP** — the learned-offset variant — on the indoor testbed with the UE rotor sweeping continuously. Replaces VIBE-MA's moving-average history with a small MLP that predicts the corrective beam offset directly.

## Files

| File | Role |
|---|---|
| `automatic_mlp_main.py` | **Entrypoint.** Orchestrator — iterates over `(SNR_QUANTILE, ROTOR_SPEED)` combinations, captures ground truth for each, then launches the runner. |
| `continuous_online_main_mlp.py` | The VIBE-MLP runner — drives Sivers TX/RX, the rotor, and the remote YOLO service. Loads `OffsetMLP` weights and predicts beam offset when YOLO's prediction misses the SNR threshold. |
| `train_mlp.py` | Trains `OffsetMLP` on offline offset-error data; emits `offset_mlp_model_*.pt` and `offset_scaler_*.pkl`. |
| `dataset_mlp_new.py` | Builds the training dataset from prior experiments — produces `offset_dataset_*.csv`. |
| `optimized_beam_sweep.py` | Narrowed TX/RX sweep around the expected boresight beam (TX±5, RX±10) at 5° rotor steps; produces the ground-truth SNR table. The full 64×64 exhaustive variant lives at [ground_truth_collection/BeamSweeponRotor.py](../../../../ground_truth_collection/BeamSweeponRotor.py). |
| `run_ground_truth_data_extraction.py` | Post-processes the sweep into `forward_max_snr_per_angle.csv` + per-angle CSVs. |
| `plot_ground_truth.py` | Diagnostic plot of the ground-truth heatmap. |
| `eval.py` | Per-experiment summary — outage rate, mean SNR, beams searched. |
| `offset_dataset_*.csv`, `offset_scaler_*.pkl` | Multiple dated training datasets / fitted input scalers. The runner currently loads the `*_jul23_oakd` pair. |
| `sivers_control.py`, `usrp_control.py`, `uhd_conf.py`, `imports.py` | Local copies of the hardware shims (folder-scoped). |

## Prerequisites

1. **Hardware up.** Sivers TX/RX, USRP B200-mini, rotor, RX-side camera. See [docs/HARDWARE.md](../../../../docs/HARDWARE.md).
2. **YOLO service** running on the UE-side host listening at `JETSON_IP:PORT` (TCP). The runner sends `DETECT:<rotor_angle>:<timestamp>` and expects a beam index (or `NO_RADIO`) in reply.
3. **Config edited.** In [configurations/config.py](../../../../configurations/config.py), set `PROJECT_ROOT`, `JETSON_IP`, `NUC_IP`, `serial_port`, and the camera intrinsics.
4. **MLP weights.** A trained `offset_mlp_model_*.pt` and matching `offset_scaler_*.pkl` must be present in this folder (the runner currently expects `offset_mlp_model_sc_jul23_oakd.pt` / `offset_scaler_sc_jul23_oakd.pkl`). The `.pt` weights are not bundled with the repo — train one with `python3 train_mlp.py` after collecting offset data via `dataset_mlp_new.py`.

## Run

```bash
cd indoor/continuous/online/automatic_indoor_evaluations_mlp
python3 automatic_mlp_main.py
```

Defaults sweep `SNR_QUANTILE ∈ {0.80, 0.90, 0.95}` × `ROTOR_SPEED ∈ {0.25, 0.5, 1, 2, 4} °/s` — 15 experiments per invocation. Edit the lists at the top of `automatic_mlp_main.py` to narrow the sweep.

For each `(quantile, speed)` combination the orchestrator:

1. Updates the relevant fields in `configurations/config.py` in place.
2. Runs `optimized_beam_sweep.py` to capture a fresh ground-truth sweep.
3. Extracts forward SNR data via `run_ground_truth_data_extraction.py`.
4. Plots the ground-truth heatmap.
5. Computes the boresight-range (±30°) average max-SNR and writes it back to `REFERENCE_MAX_SNR_DB` in `config.py`.
6. Launches `continuous_online_main_mlp.py --test_number <id>` for the live experiment.

## Outputs

Each experiment writes under `Adaptive_Beamforming_SC/<experiment_name>/`:

- `results_<experiment_name>.csv` — per-step log (rotor angle, YOLO-predicted beam, MLP-predicted offset, selected beam, SNR, beams checked, adjustment method).
- `experiment_metadata.json` — config snapshot used for this run.
- Sivers TX/RX logs, ground-truth CSVs, and any plots produced by `plot_experiment.py`.

A combined run log is written to `automatic_evaluation_terminal_log.txt` in this folder.

## Algorithm summary

For every YOLO detection inside the rotor's active range:

1. Set RX beam to the YOLO-predicted index, measure SNR.
2. If SNR ≥ threshold → keep it (`adjustment_type = "YOLO"`).
3. Else feed `[boresight, threshold_snr, yolo_beam, snr_yolo]` into `OffsetMLP`, get a predicted offset, set RX beam to `yolo_beam + offset`, measure SNR. If it now passes the threshold → `OffsetCorrected`; if it still fails → revert to YOLO beam and label `OffsetFailed`.

Compared to VIBE-MA, VIBE-MLP does not iterate over neighbors — it commits to the network's offset prediction in one shot. The trade-off vs. VIBE-MA: lower latency and more aggressive correction when the model is well-trained, at the cost of needing labeled offset data and a per-environment retrain.

### Model

`OffsetMLP` (defined in `continuous_online_main_mlp.py`):

- Input: 4-dim `[boresight, threshold_snr, yolo_beam, snr_yolo]` (StandardScaler-normalized).
- 3 hidden layers, 128 units each, LayerNorm + ReLU; one Dropout(0.2) before the output.
- Output: scalar offset (cast to int).
- Training (`train_mlp.py`): SmoothL1 loss, Adam optimizer.
