# MobileNet + LeNet analysis summaries

Aggregated outage + inference-timing results for the **MobileNet + LeNet-5** baseline vs. VIBE, on the DeepSense 6G dataset. These CSVs back the MNet-LeNet rows of the cross-scenario comparison (Table II / Fig. 11 of the paper); they are produced by the `ExternalEvalScenario{7,9}_MNetLeNet_VIBE.ipynb` notebooks one level up.

## Model

**MobileNet + LeNet** (Imran *et al.*, ICC-W 2023): a segmentation network (MobileNet) feeds a small LeNet-5 classifier that predicts the beam index from the camera image. Vision-only baseline — no radio feedback. Weights: `LeNet5_64_beam` (see the parent [README](../README.md) for the source link).

## Dataset

**DeepSense 6G** (<https://www.deepsense6g.net/>), camera + mmWave:
- **Scenario 7** — *seen* by the MNet-LeNet model (in-distribution).
- **Scenario 9** — *unseen* (out-of-distribution generalization test).

## Files

| File | Contents |
|---|---|
| `combined_outage_timing_summary_Scenario7.csv` | Scenario 7 summary. |
| `combined_outage_timing_summary_Scenario9.csv` | Scenario 9 summary. |

Each row is keyed by the **SNR threshold quantile** (80, 90, 95, …). Columns:

- `YOLOR_Top1`, `YOLOR_Corr` — VIBE-YOLOR outage % (Top-1 prediction, and after closed-loop correction).
- `LeNet_Top1`, `LeNet_Top2`, `LeNet_Top3`, `LeNet_Corr` — LeNet outage % at Top-1/2/3 and after correction.
- `* TopKTime`, `* CorrTime` — per-decision inference time (seconds) for each method.

Lower outage % is better; the unseen-scenario (9) gap is the headline result — VIBE generalizes where the vision-only baseline degrades.

Author: Avhishek Biswas
