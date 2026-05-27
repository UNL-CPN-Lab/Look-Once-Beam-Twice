# VIBE-MA — online indoor results

Results for **VIBE-MA** (moving-average offset tracking, the main proposed method) on the indoor testbed with live SNR measurement.

- **Produced by:** [indoor/continuous/online/automatic_indoor_evaluations_mavg/](../../../indoor/continuous/online/automatic_indoor_evaluations_mavg/)
- **Algorithm:** YOLO-predicted beam → if below threshold, correct by `prediction + mean(offset history)` → else nearby-beam search. Offsets that meet the threshold feed the moving-average history.

## Layout

- `nfov_results/` — Intel RealSense D435 (60° FOV).
- `wfov_results/` — Luxonis OAK-D (90° FOV).

Each FOV folder holds the per-run experiment dirs (`sc_<date>_gain8db_3m_QT_MAVG<n>`) plus a `online_evaluation_experiments_results_summary_<date>.csv` aggregating outage / mean-SNR / timing across runs. Per-run dirs contain `results_<exp>.csv`, `cleaned_`/`balanced_` CSVs, `metadata.json`, and per-metric plots (PNG).

Author: Apala Pramanik
