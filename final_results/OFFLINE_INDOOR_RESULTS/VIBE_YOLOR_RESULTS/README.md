# VIBE-YOLOR — offline indoor results

Results for **VIBE-YOLOR** (camera prior only, no closed loop) on the indoor testbed with **replayed** SNR. Open-loop baseline: the beam is taken directly from the YOLO prediction with no offset correction or search.

- **Produced by:** [indoor/continuous/offline/automatic_indoor_evaluations_basic/](../../../indoor/continuous/offline/automatic_indoor_evaluations_basic/)
- **Algorithm:** YOLO-predicted beam selected as-is. No threshold-triggered correction or nearby-beam search — the gap between this and the closed-loop variants is the value the loop adds.

## Layout

- `nfov_results/` — Intel RealSense D435 (60° FOV).
- `wfov_results/` — Luxonis OAK-D (90° FOV).

Per-run dirs contain `results_<exp>.csv`, `cleaned_`/`balanced_` CSVs, `metadata.json`, and per-metric plots (PNG).

Author: Apala Pramanik
