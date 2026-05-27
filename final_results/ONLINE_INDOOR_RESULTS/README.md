# Online indoor results

Recorded results from the **online (live-SNR) indoor** experiments — CPN Lab testbed, UE on the motorized rotor sweeping continuously, SNR measured in real time during each run.

Produced by the orchestrators under [indoor/continuous/online/](../../indoor/continuous/online/).

## Variants

| Folder | Method | Runner |
|---|---|---|
| `VIBE_MA_RESULTS/` | VIBE-MA — moving-average offset tracking (main proposed) | `automatic_indoor_evaluations_mavg/` |
| `VIBE_MA_ABS_RESULTS/` | VIBE-MA ablation — history fallback disabled | `automatic_indoor_evaluations_mavg_absent/` |
| `VIBE_MLP_RESULTS/` | VIBE-MLP — learned offset | `automatic_indoor_evaluations_mlp/` |
| `VIBE_YOLOR_RESULTS/` | VIBE-YOLOR — camera prior only, no closed loop | `automatic_indoor_evaluations_basic/` |

Each variant folder (except `VIBE_MA_ABS_RESULTS`, which is NFOV-only) splits by camera FOV: `nfov_results/` (Intel RealSense D435, 60°) and `wfov_results/` (Luxonis OAK-D, 90°). Leaf folders are individual test runs named `sc_<date>_gain<g>_<dist>_<test>` and contain `results_<exp>.csv`, post-processed `cleaned_`/`balanced_` CSVs, `metadata.json`, and per-metric plots (PNG).

Author: Apala Pramanik
