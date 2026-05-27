# ResNet-50 analysis summaries

Aggregated outage + inference-timing results for the **ResNet-50** vision baseline (and a GPS baseline) vs. VIBE, on the DeepSense 6G dataset. These CSVs back the ResNet-50 rows of the cross-scenario comparison (Table II / Fig. 11 of the paper); they are produced by the `ExternalEvalScenario{6,9}_ResNet50_VIBE.ipynb` notebooks one level up.

## Models

- **ResNet-50** (Charan *et al.*, WCNC 2021): a ResNet-50 CNN predicts the beam index from the camera image. Vision-only baseline — no radio feedback. Weights: `CNN_beam_pred`, built via `build_net.py` (see the parent [README](../README.md) for source links).
- **GPS** baseline: predicts the beam from the transmitter's GPS position — a position-only reference included for comparison.

## Dataset

**DeepSense 6G** (<https://www.deepsense6g.net/>), camera + mmWave + GPS:
- **Scenario 6** — *seen* by the ResNet-50 model (in-distribution).
- **Scenario 9** — *unseen* (out-of-distribution generalization test).

## Files

| File | Contents |
|---|---|
| `combined_outage_timing_summary_Scenario6.csv` | Scenario 6 summary. |
| `combined_outage_timing_summary_Scenario9.csv` | Scenario 9 summary. |

Each row is keyed by the **SNR threshold quantile** (80, 90, 95, …). Columns:

- `YOLO_Top1/2/3`, `YOLO_Corr` — VIBE-YOLOR outage % (Top-1/2/3 predictions, and after closed-loop correction).
- `ResNet_Top1/2/3`, `ResNet_Corr` — ResNet-50 outage % at Top-1/2/3 and after correction.
- `GPS_Top1/2/3`, `GPS_Corr` — GPS-baseline outage %.
- `* TopKTime`, `* CorrTime` — per-decision inference time (seconds) for each method. Note ResNet-50's large `TopKTime` (~0.43 s) vs. VIBE-YOLOR (~0.036 s) — the latency advantage cited in the paper.

Lower outage % is better; the unseen-scenario (9) gap is the headline result.

Author: Avhishek Biswas 
