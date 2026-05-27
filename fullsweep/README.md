# Full 64×64 beam sweep + heatmap

Baseline characterization tooling: drives Sivers TX/RX through the full beam codebook (64 TX × 64 RX) at a **single, stationary** position and writes per-(tx, rx) SNR, raw IQ, and a heatmap plot. Used to measure the full beam-pair landscape independent of any algorithm.

This is the "exhaustive" counterpart to the narrowed `optimized_beam_sweep.py` inside each indoor runner folder (TX±5, RX±10 around the expected boresight) and to [outdoor/fullsweep/](../outdoor/fullsweep/) (the outdoor-deployment variant).

## Files

| File | Role |
|---|---|
| `Sivers_BeamSweep_Delay_Optimized_SNR.py` | **Entrypoint.** Two modes: `'F'` = full sweep (64 TX × 64 RX), or single-TX mode (`tx_beam` chosen at runtime, sweeps 64 RX). Captures IQ for every pair, computes SNR, and writes `snr_data.csv`, iteration timestamps, raw IQ vectors, and per-`tx_beam` final-iteration buffers. |
| `Sivers_Plot_Tx_Rx_Heatmaps.py` | Imported by the sweep script as `heatmap`. `plotheatmap(sweep_directory_path, samples_per_beam)` reads `snr_data.csv` and renders a TX×RX SNR heatmap (`<exp_name>_heatmap.png`). |
| `calibration_with_sa.py` | Calibration variant of the sweep script — pairs the Sivers beam scan with a spectrum-analyzer (SA) measurement loop. Same per-pair output structure but adds SA-derived power readings for absolute calibration. |
| `Calibrated_PRx.py` | Small helper: given a complex IQ vector, returns the average and max received power in dBm. Used by the calibration pipeline to convert raw IQ → reference dBm. |
| `uhd_conf.py` | Local USRP configuration shim. |

## Run

```bash
cd fullsweep
python3 Sivers_BeamSweep_Delay_Optimized_SNR.py
```

The script prompts for the sweep mode (`F` for full, anything else for single-TX with a follow-up TX-beam prompt) and an experiment name, then drives the radios.

## Output

Per run, under a directory named after the experiment (path set near the bottom of the script in the `__main__` block — edit `main_directory` to point at your storage volume):

- `snr_data.csv` — `Sample size, Tx Beam, Rx Beam, SNR (dB)` per row, 4096 rows for full sweep.
- `iteration_timestamps.csv` — per-(tx, rx, iteration) start/end timestamps (latency analysis).
- `recv_signal/<tx>_<rx>_<iter>.bin` — raw IQ per iteration.
- `tx_beam_<idx>.dat` — final-iteration IQ buffer per TX beam.
- `<exp_name>_heatmap.png` — TX×RX SNR heatmap rendered by `Sivers_Plot_Tx_Rx_Heatmaps.plotheatmap`.

## Prerequisites

1. **Hardware up.** Sivers EVK06002 TX + RX (both reachable from this host), USRP B200-mini, SA bench setup if running `calibration_with_sa.py`. See [../docs/HARDWARE.md](../docs/HARDWARE.md).
2. **Config edited.** In [../configurations/config.py](../configurations/config.py): `PROJECT_ROOT`, `serial_port`, `SAMPLE_SIZE`, `PADDING`, USRP gain/rate.
3. **Storage path.** Edit `main_directory` in `Sivers_BeamSweep_Delay_Optimized_SNR.py`'s `__main__` block — outputs are large (raw IQ per pair × per iteration easily fills GBs).

## Difference from per-runner `optimized_beam_sweep.py`

| | `fullsweep/Sivers_BeamSweep_Delay_Optimized_SNR.py` | `<runner>/optimized_beam_sweep.py` |
|---|---|---|
| TX × RX coverage | Full 64 × 64 | Narrowed: TX ± 5, RX ± 10 around expected boresight |
| Rotor | Single fixed position | Sweeps rotor (5° steps from 25° to 156°) |
| Use case | One-shot full-beam-landscape characterization | Per-(quantile, speed) ground-truth capture inside the orchestrator loop |
| Output size | One sweep per run | One sweep per rotor angle (~26 angles per orchestrator iteration) |

Author: Avhishek Biswas 