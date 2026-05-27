# VIBE-MA-ABS — online indoor results

Results for the **VIBE-MA ablation** on the indoor testbed with live SNR measurement. Same as VIBE-MA but with the moving-average history fallback **disabled**, isolating the contribution of offset tracking.

- **Produced by:** [indoor/continuous/online/automatic_indoor_evaluations_mavg_absent/](../../../indoor/continuous/online/automatic_indoor_evaluations_mavg_absent/)
- **Algorithm:** YOLO-predicted beam → if below threshold, fall back to a nearby-beam search only (no `mean(offset history)` correction). Compare against [VIBE_MA_RESULTS](../VIBE_MA_RESULTS/) to see the effect of the offset history.

## Layout

NFOV-only (no `wfov_results/` split) — the ablation was run on the Intel RealSense D435 (60° FOV) configuration.

Per-run dirs (`sc_<date>_gain8db_3m_QT_MAVG_ABS<n>`) contain `results_<exp>.csv`, `cleaned_`/`balanced_` CSVs, `metadata.json`, and per-metric plots (PNG), plus an `online_evaluation_experiments_results_summary_<date>.csv` aggregating outage / mean-SNR / timing across runs.

Author: Apala Pramanik
