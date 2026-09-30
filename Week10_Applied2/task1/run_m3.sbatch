#!/bin/bash
#SBATCH --job-name=fit3143_rotate
#SBATCH --time=00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --gres=gpu:1
#SBATCH --output=rotate_%j.out
# Partition: check `sinfo -o "%P %G"` on the cluster and add  #SBATCH --partition=<gpu partition>
module load cuda
nvidia-smi
nvcc -O3 --fmad=false -arch=native -o rotate_cuda rotate_cuda.cu
gcc -O3 -o rotate_cpu rotate_cpu.c -lm
./rotate_cuda
