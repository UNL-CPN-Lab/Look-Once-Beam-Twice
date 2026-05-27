# Shared configuration + utilities

Project-wide constants and helper functions imported by every runner. Edit `config.py` before running anything.

## Files

| File | Role |
|---|---|
| `config.py` | All tunable constants: beambook tables, network IPs, paths, SNR/quantile parameters, camera intrinsics, serial port, gain/distance metadata. **Users must edit `PROJECT_ROOT`, `JETSON_IP`, `NUC_IP`, `serial_port`, and the camera intrinsics before running.** |
| `utils.py` | Helpers: SNR computation (`calculate_power_metrics`, `calculate_snr_with_min_noise_window`), pexpect shell helper (`run_interactive_command`), rotor timing (`get_rotation_time_ms`), threshold conversion (`snr_percent_db`), socket factory (`create_socket_connection`), per-experiment metadata + logging (`setup_logging`, `save_experiment_metadata`, `log_timing`). |
| `plot_experiment.py` | Per-experiment plotting glue. Runners shell out to it after each run (via the `PLOT_EXPERIMENT` path in `config.py`) to emit SNR heatmaps and summary plots next to the run's CSVs. Invoked automatically — not edited by users. |
| `__init__.py` | Package marker — empty. |

## Editing `config.py`

These are the **placeholder values** every public user must replace before running:

| Field | What to set |
|---|---|
| `PROJECT_ROOT` | Absolute path of this repo on your machine. Used by orchestrators to construct experiment output paths. |
| `JETSON_IP` | UE-side host running the YOLO inference service. |
| `NUC_IP` | TX-side host running `tx_server_zmq.py` (or `tx_server_raw_tcp.py`). |
| `PORT` | TCP port the YOLO service listens on (default `5001`). |
| `serial_port` | Arduino rotor USB port (default `/dev/ttyACM0`). |
| `GROUND_TRUTH_NAME` | Experiment ID of the ground-truth sweep being evaluated (e.g. `optimized_exhaustive_sweep_sc_<date>_gain<g>_<dist>_<tag>`). Auto-updated by the orchestrators. |
| Camera intrinsics (`PIXEL_PITCH`, `FX_MM`, `CX`) | Calibrate with OpenCV for your camera; defaults are for an Intel RealSense D435. |

## Runtime-mutated fields

Several constants are **rewritten in place** by the orchestrators while a sweep runs:

| Constant | Mutated by |
|---|---|
| `GROUND_TRUTH_NAME` | `automatic_<variant>_main.py` per `(SNR_QUANTILE, ROTOR_SPEED)` combo |
| `SNR_QUANTILE`, `ROTOR_SPEED` | same |
| `gain`, `distance`, `location` | same |
| `SNR_THRESHOLD` | Set by `run_ground_truth_data_extraction.py` from the quantile of the captured SNR distribution |
| `REFERENCE_MAX_SNR_DB` | Set by the orchestrator from the boresight-range max-SNR of the ground truth |
| `fixed_tx_beam` | Set by `run_ground_truth_data_extraction.py` to the most-frequent best-TX beam across angles |

These auto-edits are done by replacing the relevant line in `config.py` text. If you add new top-level constants, follow the same `NAME = value  # comment` convention so the regex in the orchestrators continues to match.



## Utility highlights

A few of the heavier helpers in `utils.py` that runners call frequently:

- **`calculate_power_metrics(complex_signal) → (IQ_power_dBm, avg_power_dBm, max_power_dBm)`** — converts raw complex IQ to dBm.
- **`calculate_snr_with_min_noise_window(IQ_power_dBm, window_size, noise_power_list)`** — SNR by min-noise-window method; appends estimated noise to `noise_power_list` so it accumulates across the experiment.
- **`run_interactive_command(child, cmd)`** — sends a command into a pexpect-spawned Sivers shell and waits for the prompt.
- **`get_rotation_time_ms(speed_deg_per_sec)`** — converts a target sweep speed (°/s) to the `C:<ms>` value expected by the Arduino firmware (for a 180° sweep).
- **`snr_percent_db(percentage, max_snr_db)`** — converts a fractional SNR threshold (e.g. 0.9) into an absolute dB threshold relative to the captured max.

Author: Avhishek Biswas and Apala Pramanik
