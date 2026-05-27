# VIBE-MLP — offline indoor results

Results for **VIBE-MLP** (learned offset correction) on the indoor testbed with **replayed** SNR.

- **Produced by:** [indoor/continuous/offline/automatic_indoor_evaluations_mlp/](../../../indoor/continuous/offline/automatic_indoor_evaluations_mlp/)
- **Algorithm:** YOLO-predicted beam → if below threshold, correct by `prediction + MLP(features)` where the offset is predicted by a small trained network → else nearby-beam search. Same logic as the online variant; only the SNR source differs.

## Layout

NFOV-only (`nfov_results/`, Intel RealSense D435, 60° FOV).

Per-run dirs contain `results_<exp>.csv`, `cleaned_`/`balanced_` CSVs, `metadata.json`, and per-metric plots (PNG).

Author: Apala Pramanik
