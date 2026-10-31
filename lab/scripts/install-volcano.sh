#!/usr/bin/env bash
set -euo pipefail

for command in helm kubectl; do
  command -v "$command" >/dev/null || { echo "缺少命令：$command" >&2; exit 1; }
done

helm repo add volcano-sh https://volcano-sh.github.io/helm-charts
helm repo update
helm upgrade --install volcano volcano-sh/volcano \
  --namespace volcano-system \
  --create-namespace
kubectl -n volcano-system rollout status deployment/volcano-scheduler --timeout=300s
kubectl get queue default
