#!/bin/bash -l
#SBATCH --job-name=YOLOR-prepN
#SBATCH --partition=guest_gpu
#SBATCH --gres=gpu:1
#SBATCH --constraint='gpu_32gb|gpu_48gb|gpu_140gb'
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --signal=B:SIGTERM@120
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/logs/%x_%j.out
#SBATCH --error=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/logs/%x_%j.err
: "${YOLOR_MODEL:?set YOLOR_MODEL via --export}"
SELF=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/slurm/prep_modelN.slurm
on_pre(){ echo "[preempt] prep $(date) - resubmit (idempotent)"; sbatch --export=ALL,YOLOR_MODEL=$YOLOR_MODEL --job-name="$SLURM_JOB_NAME" "$SELF"; exit 0; }
trap on_pre SIGTERM
export YOLOR_ROOT=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining
VENV=/mnt/nrdstor/vuran/shared/mmWave_Shared/yolor11_venv
module purge 2>/dev/null||true; module load python/3.9
[ -d "$VENV" ]||python3 -m venv "$VENV"; source "$VENV/bin/activate"
pip install --no-cache-dir -q ultralytics==8.3.158 torch torchvision opencv-python pyyaml pillow
cd "$YOLOR_ROOT/YOLOR_Training"
DS=$(python -c "import cp_config as c;print(c.CUSTOM_BY_MODEL[$YOLOR_MODEL]['name'])")
echo "[prep] model $YOLOR_MODEL dataset=$DS"
python cp_pseudolabel.py --dataset "$DS" --splits train val test --conf 0.5 --iou-drop 0.5 || { echo "[prep] pseudolabel FAILED"; exit 1; }
DEDUP=""
if [ "$DS" = commercial ]; then
  # Commercial is a massive set of burst video frames (14,386 raw); we dedup
  # by dHash with Hamming threshold=1 — drops only true near-duplicate frames
  # and keeps ~1,631 diverse frames. (threshold=5 collapses to 355, too aggressive.)
  python cp_dedup.py --dataset "$DS" --splits train --threshold 1 || { echo "[prep] dedup FAILED"; exit 1; }
  DEDUP="--dedup-splits train"
fi
python cp_coco_replay.py --step materialize --model "$YOLOR_MODEL" $DEDUP || { echo "[prep] materialize FAILED"; exit 1; }
echo "[prep done] model $YOLOR_MODEL $(date)"
