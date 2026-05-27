# Indoor · Continuous · 5G NR baseline (online)

Online evaluation of the **5G NR hierarchical beamforming baseline** on the indoor testbed with the UE rotor sweeping continuously. Used as a non-VIBE reference for outage and beam-management latency comparisons against the VIBE variants in the sibling folders. By design, this baseline only exists for the online/continuous condition (replaying SNR offline against a hierarchical baseline isn't meaningful).

The 5G NR baseline is **camera-free** — it does not contact the YOLO service. Each rotor angle triggers an exhaustive RX-then-TX sweep over the full 64-beam codebook on each side.

## Files

| File | Role |
|---|---|
| `automatic_5gnr_main.py` | **Entrypoint.** Orchestrator — iterates over `(SNR_QUANTILE, ROTOR_SPEED)` combinations, captures ground truth for each, then launches the runner. |
| `continuous_online_main_5gnr.py` | The 5G NR runner — drives Sivers TX/RX and the rotor; performs an exhaustive RX sweep then TX sweep at every rotor angle and logs the best `(rx, tx)` pair. |
| `optimized_beam_sweep.py` | Narrowed TX/RX sweep around the expected boresight beam (TX±5, RX±10) at 5° rotor steps; produces the ground-truth SNR table. The full 64×64 exhaustive variant lives at [ground_truth_collection/BeamSweeponRotor.py](../../../../ground_truth_collection/BeamSweeponRotor.py). |
| `run_ground_truth_data_extraction.py` | Single-quantile post-processing of the sweep into `forward_max_snr_per_angle.csv` + per-angle CSVs. |
| `run_ground_truth_data_extraction_multiple_threshold.py` | Multi-quantile variant of the above (accepts a comma-separated list of quantiles). |
| `plot_ground_truth.py` | Diagnostic plot of the ground-truth heatmap. |
| `eval.py` | Per-experiment summary — outage rate, mean SNR, beams searched. |
| `sivers_control.py`, `usrp_control.py`, `uhd_conf.py`, `imports.py` | Local copies of the hardware shims (folder-scoped). |

## Prerequisites

1. **Hardware up.** Sivers TX/RX, USRP B200-mini, rotor. See [docs/HARDWARE.md](../../../../docs/HARDWARE.md). Camera and YOLO service are **not** required for this folder.
2. **Config edited.** In [configurations/config.py](../../../../configurations/config.py), set `PROJECT_ROOT`, `serial_port`, and the camera intrinsics (still needed by other folders that share `config.py`).

## Run

```bash
cd indoor/continuous/online/automatic_indoor_evaluations_5gnr
python3 automatic_5gnr_main.py
```

Defaults sweep `SNR_QUANTILE ∈ {0.80, 0.90, 0.95}` × `ROTOR_SPEED ∈ {0.25, 0.5, 1, 2, 4} °/s` — 15 experiments per invocation. Edit the lists at the top of `automatic_5gnr_main.py` to narrow the sweep.

For each `(quantile, speed)` combination the orchestrator:

1. Updates the relevant fields in `configurations/config.py` in place.
2. Runs `optimized_beam_sweep.py` to capture a fresh ground-truth sweep.
3. Extracts forward SNR data via `run_ground_truth_data_extraction.py`.
4. Plots the ground-truth heatmap.
5. Computes the boresight-range (±30°) average max-SNR and writes it back to `REFERENCE_MAX_SNR_DB` in `config.py`.
6. Launches `continuous_online_main_5gnr.py --test_number <id>` for the live experiment.

## Outputs

Each experiment writes under `Adaptive_Beamforming_SC/<experiment_name>/`:

- `results_<experiment_name>.csv` — per-step log (rotor angle, best RX beam, best TX beam, SNR, beam-sweep time).
- `experiment_metadata.json` — config snapshot used for this run.
- Sivers TX/RX logs, ground-truth CSVs, and any plots produced by `plot_experiment.py`.

A combined run log is written to `automatic_evaluation_terminal_log.txt` in this folder.

## Algorithm summary

For every rotor angle in the active range:

1. Pin TX to beam 0; sweep all RX beams `1..63`, track `best_rx_beam` by SNR.
2. Pin RX to `best_rx_beam`; sweep all TX beams `1..63`, track `best_tx_beam` by SNR.
3. Log `(best_rx_beam, best_tx_beam, snr)` for that angle.

This is an exhaustive sequential search — no camera prior, no learned offset, no history. Beam-sweep time per rotor angle is by far the largest cost in this baseline, which is the main metric of interest when comparing against the VIBE variants.
