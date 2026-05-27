# VIBE-MLP — online indoor results

Results for **VIBE-MLP** (learned offset correction) on the indoor testbed with live SNR measurement.

- **Produced by:** [indoor/continuous/online/automatic_indoor_evaluations_mlp/](../../../indoor/continuous/online/automatic_indoor_evaluations_mlp/)
- **Algorithm:** YOLO-predicted beam → if below threshold, correct by `prediction + MLP(features)` where the offset is predicted by a small trained network → else nearby-beam search.

## Layout

- `nfov_results/` — Intel RealSense D435 (60° FOV).
- `wfov_results/` — Luxonis OAK-D (90° FOV).

Each FOV folder holds the per-run experiment dirs plus an `online_evaluation_experiments_results_summary_<date>.csv` aggregating outage / mean-SNR / timing across runs. Per-run dirs contain `results_<exp>.csv`, `cleaned_`/`balanced_` CSVs, `metadata.json`, and per-metric plots (PNG).

Author: Apala Pramanik
