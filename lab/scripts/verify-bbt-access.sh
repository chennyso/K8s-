#!/usr/bin/env bash
set -euo pipefail

namespace=${1:?用法：bash scripts/verify-bbt-access.sh <namespace> <queue>}
queue=${2:?用法：bash scripts/verify-bbt-access.sh <namespace> <queue>}

command -v kubectl >/dev/null || { echo "缺少命令：kubectl" >&2; exit 1; }

kubectl get namespace "$namespace" >/dev/null
kubectl auth can-i create jobs.batch.volcano.sh -n "$namespace" | grep -Fxq yes || { echo "当前身份不能在 $namespace 创建 Volcano Job。" >&2; exit 1; }
kubectl auth can-i create persistentvolumeclaims -n "$namespace" | grep -Fxq yes || { echo "当前身份不能在 $namespace 创建 PVC。" >&2; exit 1; }
kubectl get queue "$queue" >/dev/null
kubectl get nodes -o custom-columns=NAME:.metadata.name,GPU:.status.allocatable.nvidia\\.com/gpu

echo "BBT 基础权限检查通过。提交 GPU Job 前，请将 volcano/bbt/gpu-smoke-job.yaml 中的 queue 改为 $queue。"
