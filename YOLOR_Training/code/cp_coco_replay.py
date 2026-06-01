"""COCO replay + retention data, and the unified-dataset materialize step.

Two reasons we keep COCO around:

  REPLAY      a slice of COCO train2017 (real labels, classes 0-79) mixed into
              every training run so COCO classes keep getting true positive
              gradients — covers COCO classes that don't appear in the custom
              scenes and that pseudo-labels alone can't protect.
  RETENTION   the full COCO val2017 used by cp_eval to measure how much COCO
              the fine-tuned model kept vs the stock baseline.

COCO category ids are 1..90 with gaps; we remap to the contiguous 0..79 order
of `cp_config.COCO_NAMES` (the standard "coco80" indexing).

HCC note: compute nodes usually have no internet. Pre-stage COCO anywhere and
set `YOLOR_COCO=<dir>`; this module will then only convert/link, never
download. Locally it downloads val2017 + a per-image train slice.

This file also owns the **unified dataset materialize** step: it builds
`datasets/YOLOR/` (model 5) and `datasets/<single-domain-name>/` (models 1-4)
from `labels_p1_m5/` / `labels_p1/` (see `cp_data.py` for the two label
remap stages). The materialize logic uses per-file symlinks inside regular
directories so Ultralytics' dataloader derives label paths against the
project-side (P1-remapped) tree.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cp_config as cfg

IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp")


# --- COCO id -> coco80 index ------------------------------------------------
# Source COCO categories are 1..90 with 10 unused ids; the standard Ultralytics
# "coco80" indexing removes those gaps. Index by source id, value is the
# 0..79 coco80 slot (None = unused source id).
_COCO91_TO_80 = [None,
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, None, 11, 12, 13, 14, 15, 16, 17, 18,
    19, 20, 21, 22, 23, None, 24, 25, None, None, 26, 27, 28, 29, 30, 31, 32,
    33, 34, 35, 36, 37, 38, 39, None, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
    50, 51, 52, 53, 54, 55, 56, 57, 58, 59, None, 60, None, None, 61, None,
    62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, None, 73, 74, 75, 76, 77, 78,
    79, None,
]

VAL_IMG_URL    = "http://images.cocodataset.org/zips/val2017.zip"
ANN_URL        = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
TRAIN_IMG_TMPL = "http://images.cocodataset.org/train2017/{fn}"


# --- download helpers --------------------------------------------------------

def _atomic_download(url: str, dest: Path) -> Path:
    """Download `url` to `dest` via a `.part` temp file (atomic rename). If a
    prior `dest` is present, trust it only when (a) it's non-empty AND (b)
    it's a valid zip if its suffix is `.zip` (guards against half-finished
    downloads from a previous interrupted run)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        if dest.suffix != ".zip" or zipfile.is_zipfile(dest):
            return dest
        print(f"  {dest} present but not a valid zip — redownloading")
        dest.unlink()

    part = dest.with_suffix(dest.suffix + ".part")
    print(f"  downloading {url} -> {dest}")
    urllib.request.urlretrieve(url, part)
    os.replace(part, dest)
    return dest


def _unzip(zp: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zp) as z:
        z.extractall(dest)


def ensure_annotations() -> Path:
    """Make sure COCO annotation jsons are present. Returns the annotations dir."""
    ann_dir = cfg.COCO_DIR / "annotations"
    if (ann_dir / "instances_val2017.json").exists():
        return ann_dir
    zp = cfg.COCO_DIR / "annotations_trainval2017.zip"
    _atomic_download(ANN_URL, zp)
    _unzip(zp, cfg.COCO_DIR)
    return ann_dir


# --- COCO json -> YOLO labels -----------------------------------------------

def _coco_json_to_yolo(ann_json: Path, img_ids: set[int] | None,
                       images_dir: Path, labels_dir: Path) -> int:
    """Convert one COCO annotations json into YOLO label files.

    Writes one .txt per image in `img_ids` (or all images if None) to
    `labels_dir`. Class ids are coco80 (0..79); boxes are normalized
    [cx, cy, w, h]. iscrowd annotations are skipped. Returns the number of
    label files written.
    """
    labels_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(ann_json.read_text())
    imgs = {im["id"]: im for im in data["images"]}
    if img_ids is None:
        img_ids = set(imgs)
    by_img: dict[int, list[str]] = {i: [] for i in img_ids}

    for a in data["annotations"]:
        if a["image_id"] not in by_img or a.get("iscrowd", 0):
            continue
        coco80 = _COCO91_TO_80[a["category_id"]]
        if coco80 is None:
            continue
        im = imgs[a["image_id"]]
        W, H = im["width"], im["height"]
        x, y, w, h = a["bbox"]                            # COCO: xywh top-left, pixels
        cx, cy = (x + w / 2) / W, (y + h / 2) / H
        by_img[a["image_id"]].append(
            f"{coco80} {cx:.6f} {cy:.6f} {w / W:.6f} {h / H:.6f}")

    for iid, lines in by_img.items():
        stem = Path(imgs[iid]["file_name"]).stem
        (labels_dir / f"{stem}.txt").write_text(
            "\n".join(lines) + ("\n" if lines else ""))
    return len(by_img)


# --- replay-slice selection + download --------------------------------------

def select_replay_ids(ann_json: Path, n: int, seed: int = 0) -> list[int]:
    """Pick `n` COCO train2017 image ids for the replay slice.

    Two-pass selection so every class gets some representation even when n is
    small relative to the per-class image counts:

      Pass 1 (class-coverage): for each category, take a small per-cat
        baseline (~`n / (4 * num_cats)` images); guarantees rare classes
        aren't squeezed out by frequent ones.
      Pass 2 (top-up): randomly fill the remainder from the global image
        pool up to `n` total.
    """
    import random
    data = json.loads(ann_json.read_text())
    rng = random.Random(seed)

    per_cat: dict[int, list[int]] = {}
    for a in data["annotations"]:
        per_cat.setdefault(a["category_id"], []).append(a["image_id"])

    per_cat_baseline = max(1, n // (4 * len(per_cat)))
    picked: set[int] = set()
    for ids in per_cat.values():
        rng.shuffle(ids)
        picked.update(ids[:per_cat_baseline])

    all_ids = [im["id"] for im in data["images"]]
    rng.shuffle(all_ids)
    for i in all_ids:
        if len(picked) >= n:
            break
        picked.add(i)
    return list(picked)[:n]


def download_train_slice(ann_json: Path, img_ids: list[int], dest: Path,
                         workers: int = 16) -> int:
    """Concurrently download the train images for `img_ids` into `dest`.
    Skips ids whose file is already present. Returns the number actually
    downloaded this call."""
    dest.mkdir(parents=True, exist_ok=True)
    data = json.loads(ann_json.read_text())
    fn = {im["id"]: im["file_name"] for im in data["images"]}
    todo = [(i, fn[i]) for i in img_ids if not (dest / fn[i]).exists()]

    def grab(item):
        iid, name = item
        try:
            urllib.request.urlretrieve(TRAIN_IMG_TMPL.format(fn=name), dest / name)
            return True
        except Exception as e:                       # noqa: BLE001
            print(f"  [warn] {name}: {e}")
            return False

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for ok in as_completed(ex.submit(grab, t) for t in todo):
            done += 1 if ok.result() else 0
    print(f"  downloaded {done}/{len(todo)} train images -> {dest}")
    return done


def ensure_val2017() -> tuple[Path, Path]:
    """Make sure COCO val2017 images + YOLO labels are present. Downloads
    on first call. Returns (images_dir, labels_dir)."""
    img_dir = cfg.COCO_DIR / "images" / "val2017"
    lbl_dir = cfg.COCO_DIR / "labels" / "val2017"
    if not img_dir.exists() or not any(img_dir.iterdir()):
        zp = cfg.COCO_DIR / "val2017.zip"
        _atomic_download(VAL_IMG_URL, zp)
        _unzip(zp, cfg.COCO_DIR / "images")
    if not lbl_dir.exists() or not any(lbl_dir.glob("*.txt")):
        ann = ensure_annotations() / "instances_val2017.json"
        _coco_json_to_yolo(ann, None, img_dir, lbl_dir)
    return img_dir, lbl_dir


def ensure_replay() -> tuple[Path, Path]:
    """Make sure the COCO train2017 replay slice is present (download + label).
    Returns (images_dir, labels_dir). Skips download if ≥90% of the target
    slice is already on disk."""
    img_dir = cfg.COCO_DIR / "images" / "train2017_replay"
    lbl_dir = cfg.COCO_DIR / "labels" / "train2017_replay"
    ann = ensure_annotations() / "instances_train2017.json"

    have = len(list(img_dir.glob("*.jpg"))) if img_dir.exists() else 0
    if not img_dir.exists() or have < cfg.COCO_REPLAY_TRAIN_IMAGES * 0.9:
        ids = select_replay_ids(ann, cfg.COCO_REPLAY_TRAIN_IMAGES)
        download_train_slice(ann, ids, img_dir)
        present = {int(p.stem) for p in img_dir.glob("*.jpg")}
        _coco_json_to_yolo(ann, present, img_dir, lbl_dir)
    return img_dir, lbl_dir


# --- generic split materialize (per-file links into a regular dir) ----------
#
# Every materialize output is a regular directory of per-file symlinks. This
# guarantees Ultralytics' dataloader derives label paths via
# `image_path.replace("images", "labels")` against the project-side path
# (where the unified-remapped labels live), not against any symlink-resolved
# source path (which would carry the source dataset's class ids).

def _reset_path(p: Path) -> None:
    """Remove `p` whether it's a symlink, a file, or a real dir. Used to make
    rebuilds idempotent (stale entries never accumulate)."""
    if p.is_symlink() or p.is_file():
        p.unlink()
    elif p.is_dir():
        shutil.rmtree(p)


def _reset_dir_pair(parent: Path) -> None:
    """Clear `parent/images` and `parent/labels` so a fresh materialize is
    idempotent."""
    for sub in ("images", "labels"):
        _reset_path(parent / sub)
        (parent / sub).mkdir(parents=True, exist_ok=True)


def _label_stems(labels_dir: Path) -> set[str]:
    return {q.stem for q in labels_dir.iterdir()
            if q.suffix == ".txt" and not q.name.startswith("._")}


def _source_images(img_dir: Path) -> list[Path]:
    return [p for p in img_dir.iterdir()
            if p.suffix.lower() in IMG_EXTS and not p.name.startswith("._")]


def _dedup_keep_stems(ds_key: str, split_dir: str) -> set[str] | None:
    """If a cp_dedup keep-set exists for this dataset/split, return its stems.
    Otherwise return None (so the caller falls back to keeping every labelled
    image)."""
    keep_dir = cfg.WORKDIR / "dedup" / ds_key / split_dir / "images"
    if not keep_dir.exists():
        return None
    return {p.stem for p in keep_dir.iterdir()
            if p.suffix.lower() in IMG_EXTS and not p.name.startswith("._")}


def _link_pairs(images: list[Path], labels_dir: Path,
                lbl_stems: set[str], keep_stems: set[str] | None,
                dest: Path) -> int:
    """For each image, per-file-link `image -> dest/images/X` and
    `labels_dir/X.txt -> dest/labels/X.txt`. Only links images that have a
    label (and are in `keep_stems` if dedup is active). Returns count linked."""
    n = 0
    for ip in images:
        if ip.stem not in lbl_stems:
            continue
        if keep_stems is not None and ip.stem not in keep_stems:
            continue
        di = dest / "images" / ip.name
        dl = dest / "labels" / (ip.stem + ".txt")
        ls = labels_dir / (ip.stem + ".txt")
        if not di.exists():
            di.symlink_to(ip)
        if ls.exists() and not dl.exists():
            dl.symlink_to(ls)
        n += 1
    return n


def _materialize_split(ds_key: str, split_dir: str, dest: Path,
                       labels_src: Path, dedup: bool, scheme_tag: str) -> None:
    """Link a split's images (from source) + labels (from `labels_src`) into
    `dest/{images,labels}/` via per-file symlinks. `scheme_tag` is just a
    label for the print message (`p1` for single-domain, `m5` for unified)."""
    img_src = cfg.DATASETS[ds_key] / split_dir / "images"
    if not labels_src.exists():
        raise FileNotFoundError(
            f"{labels_src} missing — run the upstream prep step first")

    lbl_stems  = _label_stems(labels_src)
    img_list   = _source_images(img_src)
    keep_stems = _dedup_keep_stems(ds_key, split_dir) if dedup else None

    _reset_dir_pair(dest)
    n = _link_pairs(img_list, labels_src, lbl_stems, keep_stems, dest)
    tag = ("dedup" if dedup
           else "labeled subset" if len(lbl_stems) < len(img_list)
           else "all")
    print(f"  [materialize-{scheme_tag}] {ds_key}/{split_dir}: "
          f"linked {n} frames ({tag})")


def _materialize_p1(ds_key: str, split_dir: str, dest: Path, dedup: bool) -> None:
    """Materialize using stage-1 (per-model scheme) labels from labels_p1/."""
    _materialize_split(ds_key, split_dir, dest,
                       labels_src=cfg.labels_p1_dir(ds_key, split_dir),
                       dedup=dedup, scheme_tag="p1")


def _materialize_p1_m5(ds_key: str, split_dir: str, dest: Path, dedup: bool) -> None:
    """Materialize using stage-2 (unified-YOLOR scheme) labels from labels_p1_m5/."""
    src = cfg.WORKDIR / "labels_p1_m5" / ds_key / split_dir
    _materialize_split(ds_key, split_dir, dest,
                       labels_src=src, dedup=dedup, scheme_tag="m5")


# --- COCO replay/val attach (per-file linking, same as custom splits) -------
# Uniform with `_materialize_split` so every materialize output is a regular
# directory containing per-file symlinks. No whole-directory symlinks anywhere
# in the materialize pipeline.

def _link_coco_split_dir(src_images: Path, src_labels: Path, dst: Path) -> None:
    """Per-file-link every (image, label) pair from `src_images`/`src_labels`
    into `dst/images/` and `dst/labels/` (regular directories)."""
    _reset_dir_pair(dst)
    for ip in src_images.iterdir():
        if ip.suffix.lower() not in IMG_EXTS or ip.name.startswith("._"):
            continue
        di = dst / "images" / ip.name
        dl = dst / "labels" / (ip.stem + ".txt")
        ls = src_labels / (ip.stem + ".txt")
        if not di.exists():
            di.symlink_to(ip)
        if ls.exists() and not dl.exists():
            dl.symlink_to(ls)


def _attach_coco(base: Path) -> tuple[Path, Path]:
    """Link COCO replay (train slice) and COCO val2017 into `base/coco_replay`
    and `base/coco_val`. Returns the (images-dir, labels-dir) tuples are not
    needed by callers; instead returns the two images dirs for yaml building."""
    cv_img, cv_lbl = ensure_val2017()
    rp_img, rp_lbl = ensure_replay()
    _link_coco_split_dir(rp_img, rp_lbl, base / "coco_replay")
    _link_coco_split_dir(cv_img, cv_lbl, base / "coco_val")
    return base / "coco_replay" / "images", base / "coco_val" / "images"


# --- top-level: materialize one model's combined dataset --------------------

UNIFIED_DATASETS = ["cots", "outdoor", "commercial", "streetlight"]


def _materialize_unified(base: Path, dedup_splits: tuple[str, ...]) -> Path:
    """Build model 5's combined dataset = union of all 4 source datasets with
    unified-YOLOR labels + COCO replay/val. Writes `<base>/YOLOR_data.yaml`."""
    train_dirs, val_dirs, test_dirs = [], [], []
    for ds_key in UNIFIED_DATASETS:
        val_split = cfg.SPLIT_DIRNAMES[ds_key]
        commercial_train_dedup = (ds_key == "commercial" and "train" in dedup_splits)
        _materialize_p1_m5(ds_key, "train",    base / f"{ds_key}_train", commercial_train_dedup)
        _materialize_p1_m5(ds_key, val_split,  base / f"{ds_key}_val",   False)
        _materialize_p1_m5(ds_key, "test",     base / f"{ds_key}_test",  False)
        train_dirs.append(base / f"{ds_key}_train" / "images")
        val_dirs.append(  base / f"{ds_key}_val"   / "images")
        test_dirs.append( base / f"{ds_key}_test"  / "images")

    coco_replay_imgs, coco_val_imgs = _attach_coco(base)
    train_dirs.append(coco_replay_imgs)
    val_dirs.append(coco_val_imgs)

    nm = cfg.model_name(5)
    yaml_path = base / f"{nm}_data.yaml"
    cfg.write_data_yaml(yaml_path,
                        train=train_dirs, val=val_dirs, test=test_dirs,
                        names=cfg.names_for_model(5))
    print(f"{nm} data.yaml -> {yaml_path} "
          f"(nc={len(cfg.names_for_model(5))}, unified union of 4 datasets)")
    return yaml_path


def _materialize_single_domain(model_id: int, base: Path,
                               dedup_splits: tuple[str, ...]) -> Path:
    """Build a single-domain model's dataset (models 1-4): one source dataset
    with per-model-scheme labels + COCO replay/val. Writes the data.yaml."""
    ds_key = cfg.CUSTOM_BY_MODEL[model_id]["name"]
    val_split = cfg.SPLIT_DIRNAMES[ds_key]
    _materialize_p1(ds_key, "train",    base / f"{ds_key}_train", "train"   in dedup_splits)
    _materialize_p1(ds_key, val_split,  base / f"{ds_key}_val",   val_split in dedup_splits)
    _materialize_p1(ds_key, "test",     base / f"{ds_key}_test",  "test"    in dedup_splits)

    coco_replay_imgs, coco_val_imgs = _attach_coco(base)

    nm = cfg.model_name(model_id)
    yaml_path = base / f"{nm}_data.yaml"
    cfg.write_data_yaml(
        yaml_path,
        train=[base / f"{ds_key}_train" / "images", coco_replay_imgs],
        val=  [base / f"{ds_key}_val"   / "images", coco_val_imgs],
        test=  base / f"{ds_key}_test"  / "images",
        names=cfg.names_for_model(model_id),
    )
    print(f"{nm} data.yaml -> {yaml_path} (nc={len(cfg.names_for_model(model_id))})")
    return yaml_path


def materialize(model_id: int, dedup_splits=()) -> Path:
    """Build `model_id`'s combined training dataset + write its data.yaml.

    `dedup_splits` is a tuple of split names ('train', 'val', 'test') that
    should be restricted to the cp_dedup keep-set. For the standard pipeline
    that is `('train',)` for models that use it; the val/test sets are never
    deduped.
    """
    base = cfg.DATASETS_BUILD / cfg.model_name(model_id)
    if model_id == 5:
        return _materialize_unified(base, tuple(dedup_splits))
    return _materialize_single_domain(model_id, base, tuple(dedup_splits))


def materialize_model1() -> Path:
    """Back-compat wrapper (YOLOR-radio = model 1)."""
    return materialize(1)


# --- CLI --------------------------------------------------------------------

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--step", choices=["val", "replay", "materialize", "all"],
                    default="all")
    ap.add_argument("--model", type=int, default=1, choices=[1, 2, 3, 4, 5])
    ap.add_argument("--dedup-splits", nargs="*", default=[],
                    help="splits to restrict to the cp_dedup keep-set (e.g. train)")
    a = ap.parse_args()
    if a.step in ("val", "all"):
        ensure_val2017()
    if a.step in ("replay", "all"):
        ensure_replay()
    if a.step in ("materialize", "all"):
        materialize(a.model, tuple(a.dedup_splits))
