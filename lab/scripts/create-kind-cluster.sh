#!/usr/bin/env bash
set -euo pipefail

for command in docker kind kubectl; do
  command -v "$command" >/dev/null || { echo "缺少命令：$command" >&2; exit 1; }
done

docker info >/dev/null || { echo "Docker 没有运行，请启动 Docker Desktop 或 Docker 服务。" >&2; exit 1; }

if kind get clusters | grep -Fxq "cloud-native-lab"; then
  echo "Kind 集群 cloud-native-lab 已存在。"
else
  kind create cluster --config kind/cluster.yaml
fi

kubectl cluster-info
kubectl get nodes
