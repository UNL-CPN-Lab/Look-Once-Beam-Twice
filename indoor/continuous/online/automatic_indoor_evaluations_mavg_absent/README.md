# Indoor · Continuous · VIBE-MA ablation, no history fallback (online)

Online evaluation of a **VIBE-MA ablation**: identical to VIBE-MA except the moving-average offset history is disabled. When the YOLO-predicted beam fails the SNR threshold the runner skips the `prediction + mean(history)` correction step and goes straight to a nearby-beam search. Used to isolate the contribution of the offset-history mechanism in VIBE-MA.

For the full VIBE-MA variant see [../automatic_indoor_evaluations_mavg/](../automatic_indoor_evaluations_mavg/).

## Files

| File | Role |
|---|---|
| `automatic_mavg_main_absent.py` | **Entrypoint.** Orchestrator — iterates over `(SNR_QUANTILE, ROTOR_SPEED)` combinations, captures ground truth for each, then launches the runner. |
| `continuous_online_main_mavg_absent.py` | The ablation runner — drives Sivers TX/RX, the rotor, and the remote YOLO service; logs per-step results to CSV. |
| `optimized_beam_sweep.py` | Narrowed TX/RX sweep around the expected boresight beam (TX±5, RX±10) at 5° rotor steps; produces the ground-truth SNR table. The full 64×64 exhaustive variant lives at [ground_truth_collection/BeamSweeponRotor.py](../../../../ground_truth_collection/BeamSweeponRotor.py). |
| `run_ground_truth_data_extraction.py` | Post-processes the sweep into `forward_max_snr_per_angle.csv` + per-angle CSVs. |
| `plot_ground_truth.py` | Diagnostic plot of the ground-truth heatmap. |
| `eval.py` | Per-experiment summary — outage rate, mean SNR, beams searched. |
| `sivers_control.py`, `usrp_control.py`, `uhd_conf.py`, `imports.py` | Local copies of the hardware shims (folder-scoped). |

## Prerequisites

1. **Hardware up.** Sivers TX/RX, USRP B200-mini, rotor, RX-side camera. See [docs/HARDWARE.md](../../../../docs/HARDWARE.md).
2. **YOLO service** running on the UE-side host listening at `JETSON_IP:PORT` (TCP). The runner sends `DETECT:<rotor_angle>:<timestamp>` and expects a beam index (or `NO_RADIO`) in reply.
3. **Config edited.** In [configurations/config.py](../../../../configurations/config.py), set `PROJECT_ROOT`, `JETSON_IP`, `NUC_IP`, `serial_port`, and the camera intrinsics.

## Run

```bash
cd indoor/continuous/online/automatic_indoor_evaluations_mavg_absent
python3 automatic_mavg_main_absent.py
```

Defaults sweep `SNR_QUANTILE ∈ {0.80, 0.90, 0.95}` × `ROTOR_SPEED ∈ {0.25, 0.5, 1, 2, 4} °/s` — 15 experiments per invocation. Edit the lists at the top of `automatic_mavg_main_absent.py` to narrow the sweep.

For each `(quantile, speed)` combination the orchestrator:

1. Updates the relevant fields in `configurations/config.py` in place.
2. Runs `optimized_beam_sweep.py` to capture a fresh ground-truth sweep.
3. Extracts forward SNR data via `run_ground_truth_data_extraction.py`.
4. Plots the ground-truth heatmap.
5. Computes the boresight-range (±30°) average max-SNR and writes it back to `REFERENCE_MAX_SNR_DB` in `config.py`.
6. Launches `continuous_online_main_mavg_absent.py --test_number <id>` for the live experiment.

## Outputs

Each experiment writes under `Adaptive_Beamforming_SC/<experiment_name>/`:

- `results_<experiment_name>.csv` — per-step log (rotor angle, YOLO-predicted beam, selected beam, SNR, beams checked, adjustment method).
- `experiment_metadata.json` — config snapshot used for this run.
- Sivers TX/RX logs, ground-truth CSVs, and any plots produced by `plot_experiment.py`.

A combined run log is written to `automatic_evaluation_terminal_log.txt` in this folder.

## Algorithm summary

For every YOLO detection inside the rotor's active range:

1. Set RX beam to the YOLO-predicted index, measure SNR.
2. If SNR ≥ threshold → keep it (`adjustment_type = "YOLO"`).
3. **Else immediately fall back to a nearby-beam search** (`"NeighborSearch"`). The `OffsetCorrected` step that VIBE-MA does (using the moving-average history) is intentionally absent here.

The expected effect vs. full VIBE-MA: more beam searches per failed prediction (no history-driven shortcut), and slightly worse outage on fast-moving targets where the history would otherwise have absorbed drift.
