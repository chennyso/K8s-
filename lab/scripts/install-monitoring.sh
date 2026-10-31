#!/usr/bin/env bash
set -euo pipefail

for command in helm kubectl; do
  command -v "$command" >/dev/null || { echo "缺少命令：$command" >&2; exit 1; }
done

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
kubectl -n monitoring rollout status deployment/monitoring-kube-prometheus-operator --timeout=300s
kubectl apply -f monitoring/prometheus-rule.yaml
kubectl -n monitoring get prometheusrule lab-web-alerts
