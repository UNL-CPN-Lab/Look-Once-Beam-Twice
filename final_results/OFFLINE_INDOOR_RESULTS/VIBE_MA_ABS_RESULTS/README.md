# VIBE-MA-ABS — offline indoor results

Results for the **VIBE-MA ablation** on the indoor testbed with **replayed** SNR. Same as VIBE-MA but with the moving-average history fallback **disabled**, isolating the contribution of offset tracking under replayed (noise-free) SNR.

- **Produced by:** [indoor/continuous/offline/automatic_indoor_evaluations_mavg_absent/](../../../indoor/continuous/offline/automatic_indoor_evaluations_mavg_absent/)
- **Algorithm:** YOLO-predicted beam → if below threshold, fall back to a nearby-beam search only (no `mean(offset history)` correction). Compare against [VIBE_MA_RESULTS](../VIBE_MA_RESULTS/) to see the effect of the offset history.

## Layout

NFOV-only (`nfov_results/`, Intel RealSense D435, 60° FOV).

Per-run dirs contain `results_<exp>.csv`, `cleaned_`/`balanced_` CSVs, `metadata.json`, and per-metric plots (PNG).

Author: Apala Pramanik
