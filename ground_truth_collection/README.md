# Ground-truth collection

Toolbox of scripts for capturing **reference SNR measurements** that the online VIBE runners compare against. Each script combines a sweep pattern (full / narrowed / fixed-beam / single-pair), a rotor protocol (on-rotor / stationary), and an optional camera capture path. Outputs always include a per-step CSV; the rotor-driven scripts additionally produce a heatmap visualisation.

The canonical end-to-end capture is [`BeamSweeponRotor.py`](BeamSweeponRotor.py) — the same script that the top-level [README](../README.md) and [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) point to as the master ground-truth source.

## Scripts by purpose

### Full TX × RX sweep on a rotor

The canonical reference: at every rotor angle, sweep all (TX, RX) beam pairs and log SNR.

| File | Variant |
|---|---|
| [`BeamSweeponRotor.py`](BeamSweeponRotor.py) | **Full 64 × 64 sweep** at each rotor angle. Prompts for Full vs Single mode at startup. Master ground-truth source. |
| [`optimized_beam_sweep.py`](optimized_beam_sweep.py) | Narrowed variant: sweeps **TX±5 × RX±10** around the expected boresight beam to cut runtime when full coverage isn't needed. |

### Fixed-beam variants

These pin one or both sides of the link and characterize SNR vs other dimensions (rotor angle, time).

| File | Variant |
|---|---|
| [`fixed_beam_sweep_on_rotor.py`](fixed_beam_sweep_on_rotor.py) | Fix one side (TX or RX) and sweep the other across rotor angles. |
| [`single_beam_on_rotor.py`](single_beam_on_rotor.py) | Single (TX, RX) pair at every rotor angle — used to measure the link's angular response for one chosen beam pair. |
| [`fixed_beam_snr_collection.py`](fixed_beam_snr_collection.py) | Fixed-beam SNR over time at a single stationary position (no rotor motion). |
| [`fixed_beam_with_camera.py`](fixed_beam_with_camera.py) | Fixed-beam SNR captured alongside synchronized RealSense camera frames — useful for building the YOLO training dataset. |
| [`outdoor_fixed_beam.py`](outdoor_fixed_beam.py) | Outdoor variant of the fixed-beam collection (no rotor, real vehicle path). |

### Post-processing & visualisation

| File | Role |
|---|---|
| [`run_full_data_extraction.py`](run_full_data_extraction.py) | Reads the raw per-angle CSVs written by `BeamSweeponRotor.py` and derives the downstream artifacts: `forward_all_snr_data.csv`, `forward_max_snr_per_angle.csv`, per-`fixed_tx_beam` slices. Same logic as the per-runner `run_ground_truth_data_extraction.py`, just standalone. |
| [`plot_ground_truth.py`](plot_ground_truth.py) | Renders SNR-vs-rotor-angle plots for the extracted CSVs (best beam pair, fixed-TX + best-RX, TX/RX 0° LoS). |
| [`Sivers_Plot_Tx_Rx_Heatmaps.py`](Sivers_Plot_Tx_Rx_Heatmaps.py) | Imported by the sweep scripts as `heatmap`. `plotheatmap(sweep_dir, samples_per_beam)` renders a TX × RX SNR heatmap from `snr_data.csv`. |

### Helpers

| File | Role |
|---|---|
| [`controlrotor.py`](controlrotor.py) | Standalone rotor driver — sends raw angle numbers (one per line, `<angle>\n`) over the Arduino serial link via `move_servo_to_angle(arduino, current, target)`. Older / simpler protocol than the `D:`/`C:` commands in [../combined_rotor_motion/](../combined_rotor_motion/) — used here for the step-and-pause sweeps that don't need the continuous mode. |
| [`uhd_conf.py`](uhd_conf.py) | Local USRP configuration shim. |

## Typical workflow

1. **Capture** a ground truth on your testbed:
   ```bash
   cd ground_truth_collection
   python3 BeamSweeponRotor.py
   ```
   Pick **Full Sweep** for a fresh dataset, **Single Sweep** to redo one TX beam. Outputs land under your configured `BASE_DIR` (edit `BeamSweeponRotor.py:__main__` to point at your storage volume).

2. **Extract** the derived per-angle / max-SNR CSVs:
   ```bash
   python3 run_full_data_extraction.py
   ```
   Edit `base_dir` / `exp_dir` at the top of the script to match your capture directory.

3. **Plot** the heatmap and the SNR-vs-angle curves:
   ```bash
   python3 plot_ground_truth.py
   ```

4. **Use** the captured ground truth from an online runner by setting `GROUND_TRUTH_NAME` in [../configurations/config.py](../configurations/config.py).

## Prerequisites

1. **Hardware up.** Sivers EVK06002 TX + RX, USRP B200-mini, Arduino-driven rotor with the firmware in [../combined_rotor_motion/](../combined_rotor_motion/). For the camera-augmented scripts also wire up the Intel RealSense or OAK-D.
2. **Config edited.** In [../configurations/config.py](../configurations/config.py): `PROJECT_ROOT`, `serial_port`, `SAMPLE_SIZE`, `PADDING`. The camera-augmented scripts additionally use `PIXEL_PITCH`, `FX_MM`, `CX`.
3. **Storage path.** Each script has a `BASE_DIR` / `main_directory` literal near its `__main__` block — edit to point at a writable volume. Outputs are large (raw IQ per pair × per iteration × per rotor angle can fill GBs for a full sweep).

## Difference vs per-runner ground-truth captures

The per-runner `optimized_beam_sweep.py` (inside each `indoor/continuous/online/automatic_indoor_evaluations_<X>/` folder) is the **same code shape** as the one here but driven by the orchestrator inside its `(SNR_QUANTILE, ROTOR_SPEED)` sweep loop. Use the per-runner version when you want an end-to-end pipeline run; use this folder's scripts when you want a one-shot capture for offline analysis or model training.

Author: Avhishek Biswas and Apala Pramanik
