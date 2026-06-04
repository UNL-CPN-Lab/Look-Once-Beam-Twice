# YOLOR :  YOLOv11x fine-tuned object detection Models for BS identification for beam initialization

[![Hugging Face](https://img.shields.io/badge/HuggingFace-YOLOR-FFD21E?logo=huggingface&logoColor=black)](https://huggingface.co/cpnlab/YOLOR)
[![IEEE DataPort](https://img.shields.io/badge/IEEE%20DataPort-Dataset-00629B?logo=ieee&logoColor=white)](https://ieee-dataport.org/documents/look-once-beam-twice-camera-primed-real-time-double-directional-mmwave-beam-management-0)
[![arXiv](https://img.shields.io/badge/arXiv-2605.05071-b31b1b.svg?logo=arxiv&logoColor=white)](https://doi.org/10.48550/arXiv.2605.05071)
[![Venue](https://img.shields.io/badge/IEEE-SECON%202026-00629B?logo=ieee&logoColor=white)](https://secon2026.ieee-secon.org/)

## Quick links

- Trained models (Hugging Face): [cpnlab/YOLOR](https://huggingface.co/cpnlab/YOLOR)
- Dataset (IEEE DataPort): [Look Once, Beam Twice dataset](https://ieee-dataport.org/documents/look-once-beam-twice-camera-primed-real-time-double-directional-mmwave-beam-management-0)
- Paper (arXiv): <https://doi.org/10.48550/arXiv.2605.05071>

---

Training and evaluation code for the **YOLOR** detector family used in the camera-primed 6G mmWave beamforming work (SECON 2026). Each model fine-tunes
`yolo11x` to detect domain-specific hardware (radios, 5G base stations,
streetlights) **without forgetting the 80 COCO classes**, so a single
network can localise both general objects and the RF infrastructure that
drives beam selection.

<p align="center">
  <img src="model_cards/YOLOR/all detection.png" alt="YOLOR — example detection of all five custom classes in one inference pass" width="90%">
</p>

### Source hardware and data

| Model | Source hardware / location |
|---|---|
| `YOLOR-radio` | [Sivers Semiconductors](https://www.sivers-semiconductors.com/) 60 GHz mmWave Radio frontends (EVK06002) |
| `YOLOR-5GBS` | 5G small cells + co-located lamp/utility poles, captured in Downtown [Lincoln, Nebraska](https://lincoln.ne.gov/), USA |
| `YOLOR-comm-mmWave` | [Terragraph Sounders](https://terragraph.com/) from [Meta](https://about.meta.com/), deployed in indoor commercial spaces |
| `YOLOR-Streetlights` | Urban streetlights on the [University of Nebraska–Lincoln](https://www.unl.edu/) campus |
| `YOLOR` (unified) | Union of all four sources above |

> Released weights live on **🤗 Hugging Face**. The code in this repository is everything you need to reproduce the training and the paper-grade evaluation.

## Models at a glance

| # | Hugging Face name | Custom classes (idx) | Domain |
|--:|-------------------|----------------------|--------|
| 1 | [`YOLOR-radio`](https://huggingface.co/cpnlab/YOLOR-radio) | `radio` (80) | indoor lab / office (COTS) |
| 2 | [`YOLOR-5GBS`](https://huggingface.co/cpnlab/YOLOR-5GBS) | `5G BS` (80), `LampPost` (81) | outdoor street capture |
| 3 | [`YOLOR-comm-mmWave`](https://huggingface.co/cpnlab/YOLOR-comm-mmWave) | `radio` (80), `mmWave radio` (81) | indoor commercial space |
| 4 | [`YOLOR-Streetlights`](https://huggingface.co/cpnlab/YOLOR-Streetlights) | `streetlight` (80) | outdoor street capture (streetlight focus) |
| 5 | [`YOLOR`](https://huggingface.co/cpnlab/YOLOR) | all five classes (80–84) | unified release model |

Models 1–4 are single-domain fine-tunes (one custom class family each); the
combined release `YOLOR` (model 5) joins all five custom classes into one
85-class head over the union of the four source datasets. Each model's
own card on Hugging Face has download instructions.



## Quick start — inference from Hugging Face

```python
from huggingface_hub import hf_hub_download
from ultralytics import YOLO

# replace with the model you want — see https://huggingface.co/cpnlab
weights = hf_hub_download(repo_id="cpnlab/YOLOR", filename="last.pt")
model = YOLO(weights)

results = model.predict("path/to/image.jpg", conf=0.25)
results[0].show()
```

Custom class indices are stacked **on top of** COCO 80, so a single image
can return any of `0–79` (COCO) plus the model's custom classes
(`80`, `81`, …). The model's `names` dict tells you which.

## What YOLOR delivers

A single 85-class YOLOv11x detector head that returns, in one inference
pass:

- the 80 standard COCO classes (people, vehicles, indoor furniture, …)
- five custom RF-infrastructure classes (`radio`, `5G BS`, `LampPost`,
  `mmWave radio`, `streetlight`)

Suitable as the camera-priming front-end of a Look-Once-Beam-Twice beam-
management pipeline, or as a stand-alone detector wherever both general
objects and RF-infrastructure cues matter.

### Training recipe

- `nc = 80 + custom`, COCO indices preserved at `0–79`, custom classes
  stacked from index `80`.
- **Pseudo-labelling** — the stock `yolo11x` labels COCO objects in
  every custom image; merged with the manual labels.
- **COCO replay** — a class-stratified slice of COCO `train2017` is mixed
  into training so all 80 COCO classes keep seeing real positive examples
  throughout fine-tuning.
- **Full convergence schedule** — `cos_lr=True`, `warmup_epochs=5`,
  `close_mosaic=20`, run to the full epoch budget.



## Repository layout

```
YOLOR_Training/
├── README.md          ← this file
├── LICENSE            ← see repository root
├── code/
│   ├── YOLOR_train_all_models.ipynb   ← end-to-end pipeline notebook
│   ├── cp_config.py        single source of truth: paths, dataset registry, class
│   │                       scheme, model registry, training hyperparams (CP_*)
│   ├── cp_data.py          release data convention (FullDataset/ + splits/),
│   │                       auto-discover/materialize, stage-2 unified label remap
│   ├── cp_pseudolabel.py   Pseudo-label → labels_p1/
│   ├── cp_coco_replay.py   fetch/convert COCO + build per-model OR unified data.yaml
│   ├── cp_dedup.py         dHash near-duplicate frame removal (video-derived sets)
│   ├── cp_train.py         fine-tune + status log + auto-resume from last.pt
│   │                       (YOLOR_RUN_NAME overrides the run dir for parallel trainings)
│   ├── cp_eval.py          standalone eval: COCO retention vs stock + custom-class mAP
│   └── slurm/              optional cluster (SLURM) submission templates
└── runs/   logs/   outputs/   (auto-generated during training)
```

Source datasets are never modified — derived pseudo-labels go to a sibling
`labels_p1/` (and `labels_p1_m5/` for the unified model) directory and
combined training datasets are assembled with symlinks.

## Datasets

The four source datasets used to train the YOLOR family are **not publicly
distributed**. Please **contact the paper authors** to request access for
research reproduction or to discuss collaborative work — contact details
are in the SECON paper PDF (project root).

Once you have the datasets, the code expects them under
`YOLOR_Training/Datasets/` (auto-detected from the location of this
folder, or override with the `YOLOR_ROOT` env var):

```
<PROJECT_ROOT>/Datasets/
├── IndoorCOTSDataset/            (model 1: radio)
├── 5G_BaseStation/               (model 2: 5G BS + LampPost)
├── Commercial-mmWave/            (model 3: radio + mmWave radio)
└── Streetlights/                 (model 4: streetlight)
```

### Expected dataset layout (per source folder)

```
<DatasetName>/
├── FullDataset/
│   ├── Images/    (all paired image files, flat; e.g. cots_00001.jpg)
│   └── Labels/    (matching YOLO label files, same stems)
└── splits/
    ├── train.txt  (one stem per line — the paper's train split)
    ├── val.txt    (the paper's val split)
    └── test.txt   (the paper's test split)
```

`FullDataset/` is the complete image+label pool. `splits/*.txt` defines the
exact subset the paper trained / evaluated on — re-materializable from
`FullDataset` + the manifest, so a user can either reproduce the paper's
split or define their own.

After unpacking the source folders, run one command to symlink the splits
into the YOLO-conventional `train/`, `val/`, `test/` directories the rest
of the pipeline expects:

```bash
python cp_data.py --action discover                           # default path
python cp_data.py --action discover --path /any/folder/       # explicit
```

`discover` scans the given folder for every subdirectory that has both
`FullDataset/` and `splits/`, then materializes each dataset's
`train/val/test/{images,labels}/` as symlinks (no data duplication;
regeneratable in seconds). Use `--mode copy` if your filesystem doesn't
support symlinks.

### Two-stage label remap

Class ids go through **two** id renames on their way to the model:

| Stage | When | Where defined | Output | Why |
|---|---|---|---|---|
| 1 | during `cp_pseudolabel.py` | `cp_config.MANUAL_REMAP` | `labels_p1/<ds>/<split>/` | translate each source dataset's ids into that *single-domain* model's scheme (e.g. commercial: source `0,1` → per-model `80=radio, 81=mmWave radio`) |
| 2 | only for the unified YOLOR model | `cp_data.UNIFIED_REMAP_PER_DATASET` | `labels_p1_m5/<ds>/<split>/` | further translate the four per-model schemes into one shared contiguous id space (`80=radio, 81=5G BS, 82=LampPost, 83=mmWave radio, 84=streetlight`) so all four datasets can be unioned into one yaml |

Single-domain models (1–4) only need stage 1. The combined release model 5
runs both. `cp_data.py`'s module docstring has the full rationale.

## Configuration (environment variables)

| Variable | Purpose |
|---|---|
| `YOLOR_ROOT` | dataset root |
| `YOLOR_WORK` | where outputs/checkpoints/logs go (defaults to `<root>/YOLOR_Training`) |
| `YOLOR_COCO` | pre-staged COCO dir wabou |
| `YOLOR_EPOCHS` `YOLOR_PATIENCE` `YOLOR_IMGSZ` `YOLOR_BATCH` `YOLOR_MIXUP` `YOLOR_REPLAY_N` | per-run recipe overrides |
| `YOLOR_RUN_NAME` | override the run dir name (lets two parallel trainings of the same model coexist) |

`cp_config.py` auto-selects `imgsz`/`batch` by GPU class (640/4 on a 12 GB
card, 768/8 on a ≥32 GB card; pin `YOLOR_BATCH=4` for the proven V100@768
recipe).

## Training from scratch

If you have the source datasets and want to reproduce a model from
scratch:

```bash
cd code/
pip install ultralytics==8.3.158 torch torchvision opencv-python pyyaml pillow

# one-time per machine: pseudo-label + build COCO replay slice
python cp_pseudolabel.py --dataset cots          # repeat for outdoor/commercial/streetlight
python cp_coco_replay.py --step all              # downloads COCO val2017 + 8k train slice

# build per-model dataset (model 5 needs --dedup-splits train for commercial)
python cp_coco_replay.py --step materialize --model 1
python cp_coco_replay.py --step materialize --model 5 --dedup-splits train

# train (--run = real training; omit for a 1-epoch ETA probe)
python cp_train.py --model 1 --run
python cp_eval.py  --model 1                     # paper-grade evaluation
```

`cp_train.py` saves `runs/<model_name>/weights/last.pt` — the converged
final model after the full schedule. This is what `cp_eval.py` evaluates
and what gets uploaded to Hugging Face as the released checkpoint.

### Optional: cluster / SLURM

Template SLURM scripts for a guest-GPU partition (preemptable) live in
`code/slurm/`. The scripts trap `SIGTERM`, resubmit a continuation, and
`cp_train.py` auto-resumes from `last.pt` so long runs complete
unattended despite preemption.

If you have a single dedicated GPU box and don't need SLURM, just use the
direct `python` commands above — the same `cp_train.py` runs identically.

## Reproducibility

Default recipe (override via env): `epochs=200`, `patience=0`,
`cos_lr=True`, `warmup_epochs=5`, `close_mosaic=20`, `lr0=0.01`,
`weight_decay=0.0005`, `mosaic=1.0`, `mixup=0.1`, standard HSV/flip/scale
augmentation, `seed=0`. P1: conf ≥ 0.5, IoU-drop > 0.5. COCO replay:
8000 class-stratified `train2017` images by default.

## Citation

If you use this code or any of the released YOLOR models, please cite the
associated paper:

> *Camera-primed 6G mmWave Beamforming* (SECON 2026).
> arXiv: <https://doi.org/10.48550/arXiv.2605.05071> · IEEE Xplore: pending

```bibtex
@inproceedings{biswas2026look,
  title     = {Look Once, Beam Twice: Camera-Primed Real-Time Double-Directional
               mmWave Beam Management for Vehicular Connectivity},
  author    = {Biswas, Avhishek and Pramanik, Apala and Ekici, Eylem and Vuran, Mehmet C.},
  booktitle = {Proc. IEEE SECON},
  year      = {2026}
}
```
