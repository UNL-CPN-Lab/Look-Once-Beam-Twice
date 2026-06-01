#!/bin/bash -l
#SBATCH --job-name=YOLOR-radio
#SBATCH --partition=guest_gpu
#SBATCH --gres=gpu:1
#SBATCH --constraint='gpu_32gb|gpu_48gb|gpu_140gb'
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=120G
#SBATCH --time=168:00:00
#SBATCH --signal=B:SIGTERM@120
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/logs/train_m1_%j.out
#SBATCH --error=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/logs/train_m1_%j.err

SELF=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/slurm/train_model1.slurm
KEEP=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/.YOLOR-radio.keepgoing
# Resubmit on pre-emption ONLY while the sentinel exists. To stop cleanly:
#   rm "$KEEP" && scancel <jobid>      (trap sees no sentinel -> no resubmit)
on_preempt() {
  echo "[preempt] SIGTERM $(date)"
  if [ -f "$KEEP" ]; then
    echo "[preempt] sentinel present -> resubmit (cp_train auto-resumes from last.pt)"
    sbatch "$SELF"
  else
    echo "[preempt] sentinel absent -> clean stop, NOT resubmitting"
  fi
  exit 0
}
trap on_preempt SIGTERM
touch "$KEEP"

export YOLOR_ROOT=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining
export YOLOR_BATCH=4
export CP_ES_MIN_EPOCH=181  # Opt1: only post-close_mosaic (ep181-200) is meaningful
export CP_ES_PATIENCE=8  # real overtrain brake in the ep181-200 clean window
VENV=/mnt/nrdstor/vuran/shared/mmWave_Shared/yolor11_venv
module purge 2>/dev/null || true
module load python/3.9
[ -d "$VENV" ] || python3 -m venv "$VENV"
source "$VENV/bin/activate"
pip install --no-cache-dir --upgrade pip -q
pip install --no-cache-dir -q ultralytics==8.3.158 torch torchvision opencv-python pyyaml
cd "$YOLOR_ROOT/YOLOR_Training"
python cp_train.py --model 1 --run &
TPID=$!
wait $TPID; RC=$?
rm -f "$KEEP"
echo "[exit] cp_train rc=$RC $(date) - clean end (sentinel cleared, no resubmit)"
