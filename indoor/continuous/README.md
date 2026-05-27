# Indoor · Continuous-rotor experiments

Indoor evaluations on the CPN Lab testbed where the UE rotor sweeps **continuously** (smooth motion). Each subfolder is a self-contained experiment runner for one algorithmic variant under one SNR-measurement condition.

## Variant × condition layout

The tree is split into two parents — `online/` (live-SNR measurement) and `offline/` (SNR replayed from a pre-collected ground truth) — each holding the same per-variant subfolders. The orchestrator captures (or replays) ground truth, derives Q-thresholds, and runs the live experiment end-to-end.

| Variant | Online (live SNR) | Offline (replayed SNR) |
|---|---|---|
| **VIBE-YOLOR** (camera prior only, no closed loop) | [online/automatic_indoor_evaluations_basic/](online/automatic_indoor_evaluations_basic/) | [offline/automatic_indoor_evaluations_basic/](offline/automatic_indoor_evaluations_basic/) |
| **VIBE-MA** (moving-average offset, main proposed) | [online/automatic_indoor_evaluations_mavg/](online/automatic_indoor_evaluations_mavg/) | [offline/automatic_indoor_evaluations_mavg/](offline/automatic_indoor_evaluations_mavg/) |
| **VIBE-MA ablation** (history fallback disabled) | [online/automatic_indoor_evaluations_mavg_absent/](online/automatic_indoor_evaluations_mavg_absent/) | [offline/automatic_indoor_evaluations_mavg_absent/](offline/automatic_indoor_evaluations_mavg_absent/) |
| **VIBE-MLP** (learned offset) | [online/automatic_indoor_evaluations_mlp/](online/automatic_indoor_evaluations_mlp/) | [offline/automatic_indoor_evaluations_mlp/](offline/automatic_indoor_evaluations_mlp/) |
| **5G NR baseline** (exhaustive RX+TX sweep) | [online/automatic_indoor_evaluations_5gnr/](online/automatic_indoor_evaluations_5gnr/) | — *(no offline counterpart by design — only meaningful with real-time SNR)* |

## Per-subfolder structure

Each subfolder follows the same template:

- `automatic_<variant>_main.py` — entrypoint. Iterates over `(SNR_QUANTILE, ROTOR_SPEED)` combinations, captures (or replays) ground truth, then launches the runner.
- `continuous_online_main_<variant>.py` (online subfolders) or `continuous_offline_main_<variant>.py` (offline subfolders) — the actual VIBE / baseline runner.
- `optimized_beam_sweep.py` — narrowed TX/RX sweep around the boresight beam used to derive ground truth (TX±5, RX±10, 5° rotor steps).
- `run_ground_truth_data_extraction.py` — post-processes the sweep into `forward_max_snr_per_angle.csv` and per-angle CSVs.
- `plot_ground_truth.py`, `plot_experiment.py` invocation, `eval.py` — diagnostic plots and per-experiment summary.
- Local copies of the hardware shims (`sivers_control.py`, `usrp_control.py`, `uhd_conf.py`, `imports.py`).

See each subfolder's README for variant-specific algorithm details and run instructions.

## Top-level shared files

The `.py` files at this folder level are shims used by the per-folder runners:

| File | Role |
|---|---|
| [combined_continuous_discrete_rotor.py](combined_continuous_discrete_rotor.py) | Host-side rotor driver — sends `D:<deg>` (step-and-stop, used during ground-truth capture) and `C:<ms>` (continuous sweep, used during the live experiment) to the Arduino. |
| [sivers_control.py](sivers_control.py) | Sivers EVK06002 TX/RX init via pexpect. |
| [usrp_control.py](usrp_control.py) | USRP B200-mini stream init. |
| [uhd_conf.py](uhd_conf.py) | UHD device configuration. |
| [imports.py](imports.py) | Centralized imports used by the runners. |

Note: each subfolder also carries its own copy of these shims so it can run as a self-contained evaluation. The top-level versions match what the subfolders use.

## Quick start

The canonical reference variant is **VIBE-MA online**:

```bash
cd online/automatic_indoor_evaluations_mavg
python3 automatic_mavg_main.py
```

Default sweep: `SNR_QUANTILE ∈ {0.80, 0.90, 0.95}` × `ROTOR_SPEED ∈ {0.25, 0.5, 1, 2, 4} °/s` — 15 experiments per invocation. Edit the lists at the top of the orchestrator to narrow the sweep.

## Prerequisites

Common across all subfolders:

1. Hardware up: Sivers TX/RX, USRP B200-mini, rotor, RX-side camera. See [../../docs/HARDWARE.md](../../docs/HARDWARE.md).
2. YOLO service running on the UE-side host at `JETSON_IP:PORT` (TCP). *Not required for the 5G NR baseline.*
3. [configurations/config.py](../../configurations/config.py) edited with `PROJECT_ROOT`, `JETSON_IP`, `NUC_IP`, `serial_port`, and the camera intrinsics.
4. For VIBE-MLP only: trained `offset_mlp_model_*.pt` and matching `offset_scaler_*.pkl` (see the mlp folder's README).

## Outputs

Each experiment writes under `<subfolder>/Adaptive_Beamforming_SC/<experiment_name>/` (gitignored). Per-step results land in `results_<experiment_name>.csv`; metadata in `experiment_metadata.json`.

Author: Apala Pramanik
