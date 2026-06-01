
# YOLOR

![PyTorch](https://img.shields.io/badge/PyTorch-Ultralytics-EE4C2C?logo=pytorch&logoColor=white)
![YOLOv11](https://img.shields.io/badge/YOLOv11-Unified%20Release-00FFFF?logo=yolo&logoColor=black)
![mmWave](https://img.shields.io/badge/mmWave-5%20Custom%20Classes-6f42c1)
![arXiv](https://img.shields.io/badge/arXiv-2605.05071-b31b1b.svg)
![Venue](https://img.shields.io/badge/IEEE-SECON%202026-00629B)

YOLOR is a fine-tuned object detection model for BS identification for beam initialization to detect **all five YOLOR custom classes** — `radio`,
`5G BS`, `LampPost`, `mmWave radio`, `streetlight` — in one inference
pass. The combined release
model of the YOLOR detector family used for
the Look Once, Beam Twice mmWave V2X beam-management pipeline
(SECON 2026).

<p align="center">
  <img src="all detection.png" alt="YOLOR — example detection of all five custom classes in one inference pass" width="90%">
</p>

### Source hardware and data

| Model | Source hardware / location |
|---|---|
| `YOLOR-radio` | [Sivers Semiconductors](https://www.sivers-semiconductors.com/) 60 GHz mmWave Radio frontends (EVK06002) |
| `YOLOR-5GBS` | 5G small cells + co-located lamp/utility poles, captured in Downtown [Lincoln, Nebraska](https://lincoln.ne.gov/), USA |
| `YOLOR-comm-mmWave` | [Terragraph Sounders](https://terragraph.com/) from [Meta](https://about.meta.com/), deployed in indoor commercial spaces |
| `YOLOR-Streetlights` | Urban streetlights on the [University of Nebraska–Lincoln](https://www.unl.edu/) campus |
| `YOLOR` (unified) | Union of all four sources above |

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
| **Architecture** | YOLOv11x, **85-class** output head (COCO 80 + 5 custom) |
| **Initialization** | stock `yolo11x.pt` |
| **Schedule** | 200 epochs, `cos_lr`, `close_mosaic=20`, `lr0=0.01` |
| **Training data** | union of all four YOLOR source domains (cots + outdoor + commercial + streetlight), ~10,800 custom train frames + 8,000 COCO replay |
| **Custom classes** | `radio` (80), `5G BS` (81), `LampPost` (82), `mmWave radio` (83), `streetlight` (84) |
| **Released checkpoint** | `last.pt` |

## Usage

```python
from huggingface_hub import hf_hub_download
from ultralytics import YOLO

weights = hf_hub_download(repo_id="<org>/YOLOR", filename="last.pt")
model = YOLO(weights)
results = model.predict("path/to/image.jpg", conf=0.25)
```

Class indices in returned detections:
- `0–79` — the 80 standard COCO classes
- `80` — `radio`
- `81` — `5G BS`
- `82` — `LampPost`
- `83` — `mmWave radio`
- `84` — `streetlight`



## Training data and Code

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
