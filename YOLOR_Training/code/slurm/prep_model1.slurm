#!/bin/bash -l
#SBATCH --job-name=YOLOR-radio-prep
#SBATCH --partition=guest_gpu
#SBATCH --gres=gpu:1
#SBATCH --constraint='gpu_32gb|gpu_48gb|gpu_140gb'
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --signal=B:SIGTERM@120
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/logs/prep_m1_%j.out
#SBATCH --error=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/logs/prep_m1_%j.err
SELF=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining/YOLOR_Training/slurm/prep_model1.slurm
on_preempt(){ echo "[preempt] SIGTERM $(date) - resubmitting prep (idempotent)"; sbatch "$SELF"; exit 0; }
trap on_preempt SIGTERM
export YOLOR_ROOT=/mnt/nrdstor/vuran/shared/mmWave_Shared/YOLO_DatasetsandTraining
VENV=/mnt/nrdstor/vuran/shared/mmWave_Shared/yolor11_venv
module purge 2>/dev/null || true
module load python/3.9
[ -d "$VENV" ] || python3 -m venv "$VENV"
source "$VENV/bin/activate"
pip install --no-cache-dir -q ultralytics==8.3.158 torch torchvision opencv-python pyyaml
cd "$YOLOR_ROOT/YOLOR_Training"
python cp_pseudolabel.py --dataset cots --splits train val --conf 0.5 --iou-drop 0.5 &
P=$!; wait $P; RC=$?
[ $RC -ne 0 ] && { echo "[prep] pseudolabel FAILED rc=$RC"; exit 1; }
python cp_coco_replay.py --step materialize || { echo "[prep] materialize FAILED"; exit 1; }
echo "[prep done] $(date)"
