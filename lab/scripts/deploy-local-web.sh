#!/usr/bin/env bash
set -euo pipefail

for command in docker kind kubectl; do
  command -v "$command" >/dev/null || { echo "缺少命令：$command" >&2; exit 1; }
done

kind get clusters | grep -Fxq "cloud-native-lab" || { echo "请先运行 bash scripts/create-kind-cluster.sh" >&2; exit 1; }

docker build --tag cloud-native-lab:dev app
kind load docker-image cloud-native-lab:dev --name cloud-native-lab
kubectl apply -k k8s/base
kubectl -n cloud-native-lab rollout status deployment/lab-web --timeout=120s
kubectl -n cloud-native-lab get pods,svc
