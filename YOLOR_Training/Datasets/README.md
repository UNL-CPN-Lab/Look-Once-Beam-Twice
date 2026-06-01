# Datasets

The four source datasets used to train the YOLOR detector family **are
not distributed in this repository**. The directory structure below is
checked in so you can see the expected layout; the actual `Images/`,
`Labels/`, and `splits/*.txt` files have to be obtained separately and
dropped in by hand.

## How to obtain the data

The full dataset bundle is being released on **IEEE DataPort**:

- IEEE DataPort: <add IEEE DataPort DOI/URL here>

For early access or research collaboration before the IEEE DataPort
record is public, contact the paper authors:

- Avhishek Biswas — abiswas3@huskers.unl.edu
- Apala Pramanik — apramanik2@huskers.unl.edu

## Expected layout

```
YOLOR_Training/Datasets/
├── IndoorCOTSDataset/       (model 1: radio)
├── 5G_BaseStation/          (model 2: 5G BS + LampPost)
├── Commercial-mmWave/       (model 3: radio + mmWave radio)
└── Streetlights/            (model 4: streetlight)

# inside each dataset folder:
<DatasetName>/
├── FullDataset/
│   ├── Images/    (all paired image files, flat; e.g. cots_00001.jpg)
│   └── Labels/    (matching YOLO label files, same stems)
└── splits/
    ├── train.txt  (one stem per line — the paper's train split)
    ├── val.txt    (the paper's val split)
    └── test.txt   (the paper's test split)
```

## Materializing the splits

Once `FullDataset/` and `splits/` exist for at least one dataset,
`cp_data.py` discovers them automatically:

```bash
python cp_data.py --action discover
```

It creates the YOLO-conventional `train/`, `val/`, `test/`
subdirectories as symlinks back into `FullDataset/`. No data is
duplicated; the symlinked tree is regeneratable in seconds.

See [`../README.md`](../README.md) for the rest of the training pipeline.
