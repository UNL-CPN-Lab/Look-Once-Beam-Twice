---
library_name: ultralytics
pipeline_tag: object-detection
tags:
  - yolo
  - yolov11
  - object-detection
  - coco
  - mmwave
  - 6g
  - beamforming
  - vibe
  - yolor
---

# YOLOR-comm-mmWave

![PyTorch](https://img.shields.io/badge/PyTorch-Ultralytics-EE4C2C?logo=pytorch&logoColor=white)
![YOLOv11](https://img.shields.io/badge/YOLOv11-Detector-00FFFF?logo=yolo&logoColor=black)
![mmWave](https://img.shields.io/badge/mmWave-Commercial%20Indoor-6f42c1)
![arXiv](https://img.shields.io/badge/arXiv-2605.05071-b31b1b.svg)
![Venue](https://img.shields.io/badge/IEEE-SECON%202026-00629B)

<table>
<tr>
<td width="30%" valign="top">
<img src="commmmWave.png" alt="YOLOR-comm-mmWave — example radio and mmWave radio detection" width="100%">
</td>
<td valign="top">

**YOLOR-comm-mmWave** is a fine-tuned object detection model for BS identification for beam initialization to detect `mmWave radio` in one inference pass. The model is trained on imagery of **[Terragraph Sounders](https://terragraph.com/) from [Meta](https://about.meta.com/)**, deployed in indoor commercial spaces. Part of the YOLOR detector family used for the Look Once, Beam Twice mmWave V2X beam-management pipeline (SECON 2026).

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
| **Training data** | IndoorCommercialDataset, perceptual-hash deduped (`cp_dedup.py`, Hamming threshold = 1) — 1,631 train (kept from ~14,386 raw frames) / 1,798 val / 1,799 test |
| **Custom classes** | `radio` (id 80), `mmWave radio` (id 81) |
| **Released checkpoint** | `last.pt` |

## Usage

```python
from huggingface_hub import hf_hub_download
from ultralytics import YOLO

weights = hf_hub_download(repo_id="cpnlab/YOLOR-comm-mmWave", filename="last.pt")
model = YOLO(weights)
results = model.predict("path/to/image.jpg", conf=0.25)
```

Class indices: `0–79` = COCO; `80` = `radio`; `81` = `mmWave radio`.


## Training data

Code and Data: <https://github.com/UNL-CPN-Lab/Look-Once-Beam-Twice>

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

Paper: <https://doi.org/10.48550/arXiv.2605.05071> 

## Contact

For questions about this model or the paper, contact the corresponding authors:

- **Avhishek Biswas** — [abiswas3@huskers.unl.edu](mailto:abiswas3@huskers.unl.edu)
- **Apala Pramanik** — [apramanik2@huskers.unl.edu](mailto:apramanik2@huskers.unl.edu)

## Acknowledgments

Developed at the **[Cyber Physical Networking (CPN) Lab](https://cpn.unl.edu/)**, [School of Computing](https://computing.unl.edu/), [University of Nebraska–Lincoln](https://www.unl.edu/), in collaboration with [The Ohio State University](https://www.osu.edu/). Thanks to [Sivers Semiconductors](https://www.sivers-semiconductors.com/), [Ettus Research](https://www.ettus.com/), and the open-source [Ultralytics](https://ultralytics.com/), [PyTorch](https://pytorch.org/), and [Ettus UHD](https://www.ettus.com/) communities.
