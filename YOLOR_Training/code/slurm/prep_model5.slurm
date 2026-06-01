#!/bin/bash -l
#SBATCH --job-name=YOLOR-prep-5
#SBATCH --partition=guest_gpu
#SBATCH --gres=gpu:1
#SBATCH --constraint='gpu_32gb|gpu_48gb|gpu_140gb'
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --signal=B:SIGTERM@120
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/logs/%x_%j.out
#SBATCH --error=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/logs/%x_%j.err
SELF=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/slurm/prep_model5.slurm
on_pre(){ echo "[preempt] prep5 $(date) - resubmit (idempotent)"; sbatch --job-name="$SLURM_JOB_NAME" "$SELF"; exit 0; }
trap on_pre SIGTERM
export YOLOR_ROOT=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining
VENV=/mnt/nrdstor/vuran/shared/mmWave_Shared/yolor11_venv
module purge 2>/dev/null||true; module load python/3.9
[ -d "$VENV" ]||python3 -m venv "$VENV"; source "$VENV/bin/activate"
pip install --no-cache-dir -q ultralytics==8.3.158 torch torchvision opencv-python pyyaml pillow
cd "$YOLOR_ROOT/YOLOR_Training"

echo "[prep5] $(date) building unified YOLOR (all 4 datasets + COCO replay)"

# 1) Translate each dataset's labels_p1/ -> labels_p1_m5/ with unified remap
#    (cots: 80->80; outdoor: 80->81,81->82; commercial: 80->80,81->83; streetlight: 80->84)
for DS in cots outdoor commercial streetlight; do
  echo "[prep5] translate labels_p1 -> labels_p1_m5 for dataset=$DS"
  python cp_data.py --action translate_unified --dataset "$DS" \
    || { echo "[prep5] translate FAILED for $DS"; exit 1; }
done

# 2) Materialize unified — union of all 4 datasets + COCO replay/val
#    Commercial gets dedup_splits=train (the th=1 cp_dedup output from prep_model3 reuses)
python cp_coco_replay.py --step materialize --model 5 --dedup-splits train \
  || { echo "[prep5] materialize FAILED"; exit 1; }

echo "[prep5 done] $(date)"
