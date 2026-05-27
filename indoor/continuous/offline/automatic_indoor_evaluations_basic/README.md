# Indoor · Continuous · VIBE-YOLOR (offline)

Offline-replay evaluation of **VIBE-YOLOR** — the camera-only baseline (stages 1–3 of the VIBE pipeline, **no closed-loop refinement**) — on the indoor testbed with the UE rotor sweeping continuously. SNR is read from a **pre-collected ground-truth sweep** instead of being measured live; everything else (Sivers TX/RX init, rotor motion, YOLO service) is driven exactly as in the online variant.

For the online (live SNR) counterpart see [../../online/automatic_indoor_evaluations_basic/](../../online/automatic_indoor_evaluations_basic/).

## Files

| File | Role |
|---|---|
| `offline_automatic_basic_main.py` | **Entrypoint.** Orchestrator — iterates over `(SNR_QUANTILE, ROTOR_SPEED)` combinations, computes thresholds from the pre-collected ground truth, then launches the runner. Skips the live ground-truth capture step. |
| `continuous_offline_main_basic.py` | The VIBE-YOLOR offline runner — drives Sivers TX/RX, the rotor, and the remote YOLO service; instead of measuring SNR it looks up `(boresight, tx_beam, rx_beam) → SNR` from the pre-collected ground-truth CSV. |
| `optimized_beam_sweep.py` | Narrowed TX/RX sweep around the expected boresight beam (TX±5, RX±10) at 5° rotor steps; the orchestrator does **not** call this in offline mode but it is kept available for re-capture. |
| `run_ground_truth_data_extraction.py` | Post-processes the sweep into `forward_max_snr_per_angle.csv` + per-angle CSVs and computes the SNR threshold for the chosen quantile. |
| `plot_ground_truth.py` | Diagnostic plot of the ground-truth heatmap. |
| `eval.py` | Per-experiment summary — outage rate, mean SNR, beams searched. |
| `sivers_control.py`, `usrp_control.py`, `uhd_conf.py`, `imports.py` | Local copies of the hardware shims (folder-scoped). |

## Prerequisites

1. **Pre-collected ground truth.** A captured sweep directory with the per-angle SNR CSVs must exist on disk. The orchestrator builds the experiment ID from `<location>_<date>_gain<gain>_<distance>_<test_number>` and looks for a matching directory under your `<DATA_ROOT>/mmWaveSSD/...`. Edit the `location`/`gain`/`distance`/`test_number` fields in `offline_automatic_basic_main.py` (or capture a fresh sweep with `optimized_beam_sweep.py`) to point at your data.
2. **Hardware up.** Sivers TX/RX, USRP B200-mini, rotor, RX-side camera. See [docs/HARDWARE.md](../../../../docs/HARDWARE.md). Even though SNR is replayed, the script still drives the radios and rotor.
3. **YOLO service** running on the UE-side host listening at `JETSON_IP:PORT` (TCP).
4. **Config edited.** In [configurations/config.py](../../../../configurations/config.py), set `PROJECT_ROOT`, `JETSON_IP`, `NUC_IP`, `serial_port`, and the camera intrinsics.

## Run

```bash
cd indoor/continuous/offline/automatic_indoor_evaluations_basic
python3 offline_automatic_basic_main.py
```

Defaults sweep `SNR_QUANTILE ∈ {0.80, 0.90, 0.95}` × `ROTOR_SPEED ∈ {0.25, 0.5, 1, 2, 4} °/s` — 15 experiments per invocation.

For each `(quantile, speed)` combination the orchestrator:

1. Updates the relevant fields in `configurations/config.py` in place.
2. Runs `run_ground_truth_data_extraction.py` against the pre-collected sweep.
3. Plots the ground-truth heatmap.
4. Computes the boresight-range (±30°) average max-SNR and writes it back to `REFERENCE_MAX_SNR_DB` in `config.py`.
5. Launches `continuous_offline_main_basic.py --test_number <id>` for the live experiment.

## Outputs

Each experiment writes under `Adaptive_Beamforming_SC/<experiment_name>/`:

- `results_<experiment_name>.csv` — per-step log (rotor angle, YOLO-predicted beam, SNR, max power, YOLO time, beam-set time).
- `experiment_metadata.json` — config snapshot used for this run.
- Sivers TX/RX logs and any plots produced by `plot_experiment.py`.

A combined run log is written to `automatic_evaluation_terminal_log.txt` in this folder.

## Algorithm summary

For every YOLO detection inside the rotor's active range:

1. Set TX beam to `fixed_tx_beam` and RX beam directly to the YOLO-predicted index.
2. Look up the `(boresight, tx_beam, rx_beam) → SNR` entry in the pre-collected ground-truth CSV.
3. Log the result.

No closed loop, no offset history, no neighbor search — VIBE-YOLOR uses only the camera prior. The offline-replay condition isolates algorithmic decisions from RF measurement noise: the same ground truth fed to all four offline variants makes their results directly comparable.
