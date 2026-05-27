# Offline indoor results

Recorded results from the **offline (replayed-SNR) indoor** experiments — same CPN Lab testbed and variants as the online tree, but SNR is replayed from a pre-collected ground-truth sweep instead of measured live. Isolates algorithmic decisions from RF measurement noise.

Produced by the orchestrators under [indoor/continuous/offline/](../../indoor/continuous/offline/).

## Variants

| Folder | Method | Runner |
|---|---|---|
| `VIBE_MA_RESULTS/` | VIBE-MA — moving-average offset tracking | `offline/automatic_indoor_evaluations_mavg/` |
| `VIBE_MA_ABS_RESULTS/` | VIBE-MA ablation — history fallback disabled | `offline/automatic_indoor_evaluations_mavg_absent/` |
| `VIBE_MLP_RESULTS/` | VIBE-MLP — learned offset | `offline/automatic_indoor_evaluations_mlp/` |
| `VIBE_YOLOR_RESULTS/` | VIBE-YOLOR — camera prior only, no closed loop | `offline/automatic_indoor_evaluations_basic/` |

Variant folders split by camera FOV (`nfov_results/` = RealSense, `wfov_results/` = OAK-D). Offline replay was run on the NFOV configuration for most variants — only `VIBE_YOLOR_RESULTS` has both `nfov_results/` and `wfov_results/`; `VIBE_MA_RESULTS`, `VIBE_MA_ABS_RESULTS`, and `VIBE_MLP_RESULTS` are NFOV-only. Leaf folders are individual test runs containing `results_<exp>.csv`, post-processed CSVs, `metadata.json`, and per-metric plots (PNG).

Author: Apala Pramanik
