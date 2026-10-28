#!/bin/bash
#SBATCH --account=advisor-zhangsan
#SBATCH --partition=cpu-hpc
#SBATCH --job-name=bbt-learning-hello
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=128M
#SBATCH --time=00:02:00
#SBATCH --output=/workspace/runs/hello-%j.out

set -euo pipefail
printf 'Job ID: %s\n' "$SLURM_JOB_ID"
hostname
date -u
