---
library_name: ultralytics
pipeline_tag: object-detection
tags:
  - yolo
  - yolov11
  - object-detection
  - coco
  - 5g
  - beamforming
  - vibe
  - yolor
---

# YOLOR-5GBS

![PyTorch](https://img.shields.io/badge/PyTorch-Ultralytics-EE4C2C?logo=pytorch&logoColor=white)
![YOLOv11](https://img.shields.io/badge/YOLOv11-Detector-00FFFF?logo=yolo&logoColor=black)
![5G](https://img.shields.io/badge/5G-BS%20Detection-00629B)
![arXiv](https://img.shields.io/badge/arXiv-2605.05071-b31b1b.svg)
![Venue](https://img.shields.io/badge/IEEE-SECON%202026-00629B)

<table>
<tr>
<td width="30%" valign="top">
<img src="5GBS.png" alt="YOLOR-5GBS — example 5G BS and LampPost detection" width="100%">
</td>
<td valign="top">

YOLOv11x fine-tuned to detect outdoor RF infrastructure — `5G BS` (5G
small cells) and `LampPost` with the 80 COCO classes.
Part of the YOLOR detector family used for Stage 1 (camera priming) of
the Look Once, Beam Twice mmWave V2X beam-management pipeline (SECON 2026).
Data was captured in **Downtown [Lincoln, Nebraska](https://lincoln.ne.gov/), USA**.

</td>
</tr>
</table>

Reference implementation for the paper:

> Avhishek Biswas\*, Apala Pramanik\*, Eylem Ekici, Mehmet C. Vuran.
> *"Look Once, Beam Twice: Camera-Primed Real-Time Double-Directional mmWave Beam Management for Vehicular Connectivity."* (\*equal contribution)
>
> arXiv: <https://doi.org/10.48550/arXiv.2605.05071>

<p align="center">
  <img src="overview2_updated.png" alt="VIBE five-stage camera-primed beam-management pipeline" width="90%">
</p>

## Quick links

- Paper (arXiv): <https://doi.org/10.48550/arXiv.2605.05071>
- Code: <https://github.com/UNL-CPN-Lab/Look-Once-Beam-Twice>
- Training pipeline: <https://github.com/UNL-CPN-Lab/Look-Once-Beam-Twice/tree/main/YOLOR_Training>

| | |
|---|---|
| **Architecture** | YOLOv11x, 82-class output head (COCO 80 + 2 custom) |
| **Initialization** | stock `yolo11x.pt` |
| **Schedule** | 200 epochs, `cos_lr`, `close_mosaic=20`, `lr0=0.01` |
| **Training data** | OutdoorDataset labeled subset — 4,107 train / 336 val / 362 test |
| **Custom classes** | `5G BS` (id 80), `LampPost` (id 81) |
| **Released checkpoint** | `last.pt` |

## Usage

```python
from huggingface_hub import hf_hub_download
from ultralytics import YOLO

weights = hf_hub_download(repo_id="cpnlab/YOLOR-5GBS", filename="last.pt")
model = YOLO(weights)
results = model.predict("path/to/image.jpg", conf=0.25)
```

Class indices: `0–79` = COCO; `80` = `5G BS`; `81` = `LampPost`.

## Intended use

- Stage-1 BS-candidate detector for outdoor mmWave V2X beam management.
- Outdoor object detection where the relative position of 5G small cells
  and the lamp/utility-pole infrastructure they're co-located with
  matters.

## Training data

Not publicly redistributed. Contact the paper authors for access.


## Citation

```bibtex
@inproceedings{biswas2026look,
  title     = {Look Once, Beam Twice: Camera-Primed Real-Time Double-Directional
               mmWave Beam Management for Vehicular Connectivity},
  author    = {Biswas, Avhishek and Pramanik, Apala and Ekici, Eylem and Vuran, Mehmet C.},
  booktitle = {Proc. IEEE SECON},
  year      = {2026}
}
```

Paper: <https://doi.org/10.48550/arXiv.2605.05071> · Code: <https://github.com/UNL-CPN-Lab/Look-Once-Beam-Twice>

## Contact

For questions about this model or the paper, contact the corresponding authors:

- **Avhishek Biswas** — [abiswas3@huskers.unl.edu](mailto:abiswas3@huskers.unl.edu)
- **Apala Pramanik** — [apramanik2@huskers.unl.edu](mailto:apramanik2@huskers.unl.edu)

## Acknowledgments

Developed at the **[Cyber Physical Networking (CPN) Lab](https://cpn.unl.edu/)**, [School of Computing](https://computing.unl.edu/), [University of Nebraska–Lincoln](https://www.unl.edu/), in collaboration with [The Ohio State University](https://www.osu.edu/). Thanks to [Sivers Semiconductors](https://www.sivers-semiconductors.com/), [Ettus Research](https://www.ettus.com/), and the open-source [Ultralytics](https://ultralytics.com/), [PyTorch](https://pytorch.org/), and [Ettus UHD](https://www.ettus.com/) communities.
