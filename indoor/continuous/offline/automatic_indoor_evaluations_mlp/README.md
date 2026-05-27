# Indoor · Continuous · VIBE-MLP (offline)

Offline-replay evaluation of **VIBE-MLP** — the learned-offset variant — on the indoor testbed with the UE rotor sweeping continuously. Replaces VIBE-MA's moving-average history with a small MLP that predicts the corrective beam offset directly. SNR is read from a **pre-collected ground-truth sweep** instead of being measured live.

For the online (live SNR) counterpart see [../../online/automatic_indoor_evaluations_mlp/](../../online/automatic_indoor_evaluations_mlp/).

## Files

| File | Role |
|---|---|
| `offline_automatic_mlp_main.py` | **Entrypoint.** Orchestrator — iterates over `(SNR_QUANTILE, ROTOR_SPEED)` combinations, computes thresholds from the pre-collected ground truth, then launches the runner. |
| `continuous_offline_main_mlp.py` | The VIBE-MLP offline runner — drives Sivers TX/RX, the rotor, and the remote YOLO service. Loads `OffsetMLP` weights and predicts beam offset when YOLO's prediction misses the SNR threshold. SNR is looked up from the pre-collected ground-truth CSV. |
| `dataset_mlp_new.py` | Builds the offline-replay training dataset from prior experiments — produces `offset_dataset_*.csv`. |
| `optimized_beam_sweep.py` | Narrowed TX/RX sweep around the expected boresight beam (TX±5, RX±10) at 5° rotor steps; the orchestrator does **not** call this in offline mode but it is kept available for re-capture. |
| `run_ground_truth_data_extraction.py` | Post-processes the sweep into `forward_max_snr_per_angle.csv` + per-angle CSVs and computes the SNR threshold for the chosen quantile. |
| `plot_ground_truth.py` | Diagnostic plot of the ground-truth heatmap. |
| `eval.py` | Per-experiment summary — outage rate, mean SNR, beams searched. |
| `offset_dataset_*.csv`, `offset_scaler_*.pkl` | Multiple dated training datasets / fitted input scalers. The runner currently loads the `*_jul20_offline` pair. |
| `sivers_control.py`, `usrp_control.py`, `uhd_conf.py`, `imports.py` | Local copies of the hardware shims (folder-scoped). |

## Prerequisites

1. **Pre-collected ground truth.** A captured sweep directory with the per-angle SNR CSVs must exist on disk. The orchestrator builds the experiment ID from `<location>_<date>_gain<gain>_<distance>_<test_number>` and looks for a matching directory under your `<DATA_ROOT>/mmWaveSSD/...`. Edit the fields in `offline_automatic_mlp_main.py` (or capture a fresh sweep with `optimized_beam_sweep.py`) to point at your data. All four offline variants share the same source ground truth so their results are directly comparable.
2. **Hardware up.** Sivers TX/RX, USRP B200-mini, rotor, RX-side camera. See [docs/HARDWARE.md](../../../../docs/HARDWARE.md). Even though SNR is replayed, the script still drives the radios and rotor.
3. **YOLO service** running on the UE-side host listening at `JETSON_IP:PORT` (TCP).
4. **Config edited.** In [configurations/config.py](../../../../configurations/config.py), set `PROJECT_ROOT`, `JETSON_IP`, `NUC_IP`, `serial_port`, and the camera intrinsics.
5. **MLP weights.** A trained `offset_mlp_model_*.pt` and matching `offset_scaler_*.pkl` must be present in this folder (the runner currently expects `offset_mlp_model_sc_jul20_offline.pt` / `offset_scaler_sc_jul20_offline.pkl`). The `.pt` weights are not bundled with the repo — train one with `train_mlp.py` from the sibling [../../online/automatic_indoor_evaluations_mlp/](../../online/automatic_indoor_evaluations_mlp/) folder, or build a dataset locally with `dataset_mlp_new.py`.

## Run

```bash
cd indoor/continuous/offline/automatic_indoor_evaluations_mlp
python3 offline_automatic_mlp_main.py
```

Defaults sweep `SNR_QUANTILE ∈ {0.80, 0.90, 0.95}` × `ROTOR_SPEED ∈ {0.25, 0.5, 1, 2, 4} °/s` — 15 experiments per invocation.

## Outputs

Each experiment writes under `Adaptive_Beamforming_SC/<experiment_name>/`:

- `results_<experiment_name>.csv` — per-step log (rotor angle, YOLO-predicted beam, MLP-predicted offset, selected beam, SNR, beams checked, adjustment method).
- `experiment_metadata.json` — config snapshot used for this run.
- Sivers TX/RX logs and any plots produced by `plot_experiment.py`.

A combined run log is written to `offline_automatic_evaluation_terminal_log.txt` in this folder.

## Algorithm summary

For every YOLO detection inside the rotor's active range:

1. Set RX beam to the YOLO-predicted index, look up SNR from the ground-truth CSV.
2. If SNR ≥ threshold → keep it (`adjustment_type = "YOLO"`).
3. Else feed `[boresight, threshold_snr, yolo_beam, snr_yolo]` into `OffsetMLP`, get a predicted offset, set RX beam to `yolo_beam + offset`, look up SNR. If it now passes the threshold → `OffsetCorrected`; if it still fails → revert to YOLO beam and label `OffsetFailed`.

VIBE-MLP commits to the network's offset prediction in one shot (no iterative neighbor search). The offline-replay condition isolates algorithmic decisions from RF measurement noise, making the four offline variants directly comparable.

### Model

`OffsetMLP` (defined in `continuous_offline_main_mlp.py`):

- Input: 4-dim `[boresight, threshold_snr, yolo_beam, snr_yolo]` (StandardScaler-normalized).
- 3 hidden layers, 128 units each, LayerNorm + ReLU; one Dropout(0.2) before the output.
- Output: scalar offset (cast to int).
- Training: SmoothL1 loss, Adam optimizer (see `train_mlp.py` in the online MLP folder).
