# Indoor · Continuous · VIBE-MA (offline)

Offline-replay evaluation of **VIBE-MA** (moving-average offset tracking) on the indoor testbed with the UE rotor sweeping continuously. SNR is read from a **pre-collected ground-truth sweep** instead of being measured live; everything else (Sivers TX/RX init, rotor motion, YOLO service) is driven exactly as in the online variant.

For the online (live SNR) counterpart see [../../online/automatic_indoor_evaluations_mavg/](../../online/automatic_indoor_evaluations_mavg/).

## Files

| File | Role |
|---|---|
| `offline_automatic_mavg_main.py` | **Entrypoint.** Orchestrator — iterates over `(SNR_QUANTILE, ROTOR_SPEED)` combinations, computes thresholds from the pre-collected ground truth, then launches the runner. |
| `continuous_offline_main_mavg.py` | The VIBE-MA offline runner — drives Sivers TX/RX, the rotor, and the remote YOLO service; SNR for each `(boresight, tx_beam, rx_beam)` triple is looked up from the pre-collected ground-truth CSV. |
| `optimized_beam_sweep.py` | Narrowed TX/RX sweep around the expected boresight beam (TX±5, RX±10) at 5° rotor steps; the orchestrator does **not** call this in offline mode but it is kept available for re-capture. |
| `run_ground_truth_data_extraction.py` | Post-processes the sweep into `forward_max_snr_per_angle.csv` + per-angle CSVs and computes the SNR threshold for the chosen quantile. |
| `plot_ground_truth.py` | Diagnostic plot of the ground-truth heatmap. |
| `eval.py` | Per-experiment summary — outage rate, mean SNR, beams searched. |
| `sivers_control.py`, `usrp_control.py`, `uhd_conf.py`, `imports.py` | Local copies of the hardware shims (folder-scoped). |

## Prerequisites

1. **Pre-collected ground truth.** A captured sweep directory with the per-angle SNR CSVs must exist on disk. The orchestrator builds the experiment ID from `<location>_<date>_gain<gain>_<distance>_<test_number>` and looks for a matching directory under your `<DATA_ROOT>/mmWaveSSD/...`. Edit the `location`/`gain`/`distance`/`test_number` fields in `offline_automatic_mavg_main.py` (or capture a fresh sweep with `optimized_beam_sweep.py`) to point at your data. All four offline variants share the same source ground truth so their results are directly comparable.
2. **Hardware up.** Sivers TX/RX, USRP B200-mini, rotor, RX-side camera. See [docs/HARDWARE.md](../../../../docs/HARDWARE.md). Even though SNR is replayed, the script still drives the radios and rotor.
3. **YOLO service** running on the UE-side host listening at `JETSON_IP:PORT` (TCP).
4. **Config edited.** In [configurations/config.py](../../../../configurations/config.py), set `PROJECT_ROOT`, `JETSON_IP`, `NUC_IP`, `serial_port`, and the camera intrinsics.

## Run

```bash
cd indoor/continuous/offline/automatic_indoor_evaluations_mavg
python3 offline_automatic_mavg_main.py
```

Defaults sweep `SNR_QUANTILE ∈ {0.80, 0.90, 0.95}` × `ROTOR_SPEED ∈ {0.25, 0.5, 1, 2, 4} °/s` — 15 experiments per invocation.

For each `(quantile, speed)` combination the orchestrator:

1. Updates the relevant fields in `configurations/config.py` in place.
2. Runs `run_ground_truth_data_extraction.py` against the pre-collected sweep.
3. Plots the ground-truth heatmap (when enabled).
4. Computes the boresight-range (±30°) average max-SNR and writes it back to `REFERENCE_MAX_SNR_DB` in `config.py`.
5. Launches `continuous_offline_main_mavg.py --test_number <id>` for the live experiment.

## Outputs

Each experiment writes under `Adaptive_Beamforming_SC/<experiment_name>/`:

- `results_<experiment_name>.csv` — per-step log (rotor angle, YOLO-predicted beam, selected beam, SNR, offset, beams checked, adjustment method).
- `experiment_metadata.json` — config snapshot used for this run.
- Sivers TX/RX logs and any plots produced by `plot_experiment.py`.

A combined run log is written to `automatic_evaluation_terminal_log.txt` in this folder.

## Algorithm summary

For every YOLO detection inside the rotor's active range:

1. Set RX beam to the YOLO-predicted index, look up SNR from the ground-truth CSV.
2. If SNR ≥ threshold → keep it (`adjustment_type = "YOLO"`).
3. Else try `YOLO_beam + mean(beam_offset_history)` (`"OffsetCorrected"`).
4. Else fall back to a nearby-beam search (`"NeighborSearch"`).
5. If the final SNR meets the threshold, append the resulting offset to the moving-average history (`maxlen=10`).

The offline-replay condition isolates algorithmic decisions from RF measurement noise: feeding the same ground truth to all four offline variants makes their results directly comparable.
