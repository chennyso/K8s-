#!/usr/bin/env bash
set -euo pipefail

command -v kubectl >/dev/null || { echo "缺少命令：kubectl" >&2; exit 1; }
kubectl get crd jobs.batch.volcano.sh >/dev/null || { echo "Volcano 尚未安装，请先运行 bash scripts/install-volcano.sh" >&2; exit 1; }

if kubectl -n cloud-native-lab get vcjob cpu-gang-demo >/dev/null 2>&1; then
  kubectl -n cloud-native-lab delete vcjob cpu-gang-demo --wait=true
fi

kubectl apply -f volcano/local/cpu-gang-job.yaml
kubectl -n cloud-native-lab get vcjob cpu-gang-demo
echo "已提交。使用 kubectl -n cloud-native-lab get vcjob,pods 观察任务状态。"
