# Indoor · Continuous · VIBE-MA ablation, no history fallback (offline)

Offline-replay evaluation of a **VIBE-MA ablation**: identical to VIBE-MA except the moving-average offset history is disabled. When the YOLO-predicted beam fails the SNR threshold the runner skips the `prediction + mean(history)` correction step and goes straight to a nearby-beam search. Used to isolate the contribution of the offset-history mechanism in VIBE-MA. SNR is read from a **pre-collected ground-truth sweep** rather than measured live.

For the online (live SNR) counterpart see [../../online/automatic_indoor_evaluations_mavg_absent/](../../online/automatic_indoor_evaluations_mavg_absent/). For the full VIBE-MA variant (offline, no ablation) see [../automatic_indoor_evaluations_mavg/](../automatic_indoor_evaluations_mavg/).

## Files

| File | Role |
|---|---|
| `offline_automatic_mavg_absent_main.py` | **Entrypoint.** Orchestrator — iterates over `(SNR_QUANTILE, ROTOR_SPEED)` combinations, computes thresholds from the pre-collected ground truth, then launches the runner. |
| `continuous_offline_main_mavg_absent.py` | The ablation offline runner — drives Sivers TX/RX, the rotor, and the remote YOLO service; SNR for each `(boresight, tx_beam, rx_beam)` triple is looked up from the pre-collected ground-truth CSV. |
| `optimized_beam_sweep.py` | Narrowed TX/RX sweep around the expected boresight beam (TX±5, RX±10) at 5° rotor steps; the orchestrator does **not** call this in offline mode but it is kept available for re-capture. |
| `run_ground_truth_data_extraction.py` | Post-processes the sweep into `forward_max_snr_per_angle.csv` + per-angle CSVs and computes the SNR threshold for the chosen quantile. |
| `plot_ground_truth.py` | Diagnostic plot of the ground-truth heatmap. |
| `eval.py` | Per-experiment summary — outage rate, mean SNR, beams searched. |
| `sivers_control.py`, `usrp_control.py`, `uhd_conf.py`, `imports.py` | Local copies of the hardware shims (folder-scoped). |

## Prerequisites

1. **Pre-collected ground truth.** A captured sweep directory with the per-angle SNR CSVs must exist on disk. The orchestrator builds the experiment ID from `<location>_<date>_gain<gain>_<distance>_<test_number>` and looks for a matching directory under your `<DATA_ROOT>/mmWaveSSD/...`. Edit the fields in `offline_automatic_mavg_absent_main.py` (or capture a fresh sweep with `optimized_beam_sweep.py`) to point at your data. All four offline variants share the same source ground truth so their results are directly comparable.
2. **Hardware up.** Sivers TX/RX, USRP B200-mini, rotor, RX-side camera. See [docs/HARDWARE.md](../../../../docs/HARDWARE.md).
3. **YOLO service** running on the UE-side host listening at `JETSON_IP:PORT` (TCP).
4. **Config edited.** In [configurations/config.py](../../../../configurations/config.py), set `PROJECT_ROOT`, `JETSON_IP`, `NUC_IP`, `serial_port`, and the camera intrinsics.

## Run

```bash
cd indoor/continuous/offline/automatic_indoor_evaluations_mavg_absent
python3 offline_automatic_mavg_absent_main.py
```

Defaults sweep `SNR_QUANTILE ∈ {0.80, 0.90, 0.95}` × `ROTOR_SPEED ∈ {0.25, 0.5, 1, 2, 4} °/s` — 15 experiments per invocation.

## Outputs

Each experiment writes under `Adaptive_Beamforming_SC/<experiment_name>/`:

- `results_<experiment_name>.csv` — per-step log (rotor angle, YOLO-predicted beam, selected beam, SNR, beams checked, adjustment method).
- `experiment_metadata.json` — config snapshot used for this run.

A combined run log is written to `automatic_evaluation_terminal_log.txt` in this folder.

## Algorithm summary

For every YOLO detection inside the rotor's active range:

1. Set RX beam to the YOLO-predicted index, look up SNR from the ground-truth CSV.
2. If SNR ≥ threshold → keep it (`adjustment_type = "YOLO"`).
3. **Else immediately fall back to a nearby-beam search** (`"NeighborSearch"`). The `OffsetCorrected` step that VIBE-MA does (using the moving-average history) is intentionally absent here.

Compared against [../automatic_indoor_evaluations_mavg/](../automatic_indoor_evaluations_mavg/) on the same ground truth, this isolates the contribution of the moving-average history fallback.
