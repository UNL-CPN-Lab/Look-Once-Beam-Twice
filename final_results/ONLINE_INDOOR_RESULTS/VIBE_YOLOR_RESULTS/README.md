# VIBE-YOLOR — online indoor results

Results for **VIBE-YOLOR** (camera prior only, no closed loop) on the indoor testbed with live SNR measurement. This is the open-loop baseline: the beam is taken directly from the YOLO prediction with no offset correction or search.

- **Produced by:** [indoor/continuous/online/automatic_indoor_evaluations_basic/](../../../indoor/continuous/online/automatic_indoor_evaluations_basic/)
- **Algorithm:** YOLO-predicted beam selected as-is. No threshold-triggered correction or nearby-beam search — the gap between this and the closed-loop variants is the value the loop adds.

## Layout

- `nfov_results/` — Intel RealSense D435 (60° FOV).
- `wfov_results/` — Luxonis OAK-D (90° FOV).

Each FOV folder holds the per-run experiment dirs plus an `online_evaluation_experiments_results_summary_<date>.csv` aggregating outage / mean-SNR / timing across runs. Per-run dirs contain `results_<exp>.csv`, `cleaned_`/`balanced_` CSVs, `metadata.json`, and per-metric plots (PNG).

Author: Apala Pramanik
