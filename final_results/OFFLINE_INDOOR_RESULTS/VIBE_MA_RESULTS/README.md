# VIBE-MA — offline indoor results

Results for **VIBE-MA** (moving-average offset tracking, the main proposed method) on the indoor testbed with **replayed** SNR — SNR is read back from a pre-collected ground-truth sweep instead of measured live, isolating algorithmic decisions from RF measurement noise.

- **Produced by:** [indoor/continuous/offline/automatic_indoor_evaluations_mavg/](../../../indoor/continuous/offline/automatic_indoor_evaluations_mavg/)
- **Algorithm:** YOLO-predicted beam → if below threshold, correct by `prediction + mean(offset history)` → else nearby-beam search. Offsets that meet the threshold feed the moving-average history. Same logic as the online variant; only the SNR source differs.

## Layout

NFOV-only (`nfov_results/`, Intel RealSense D435, 60° FOV) — the offline replay was run on the NFOV configuration.

Per-run dirs contain `results_<exp>.csv`, `cleaned_`/`balanced_` CSVs, `metadata.json`, and per-metric plots (PNG).

Author: Apala Pramanik
