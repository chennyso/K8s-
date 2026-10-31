#!/usr/bin/env bash
set -euo pipefail

command -v kubectl >/dev/null || { echo "缺少命令：kubectl" >&2; exit 1; }

kubectl -n cloud-native-lab rollout status deployment/lab-web --timeout=120s
available=$(kubectl -n cloud-native-lab get deployment/lab-web -o jsonpath='{.status.availableReplicas}')
[ "$available" = "2" ] || { echo "预期 2 个可用副本，实际为：${available:-0}" >&2; exit 1; }

kubectl -n cloud-native-lab get service/lab-web >/dev/null
response=$(kubectl -n cloud-native-lab run verification-client --image=curlimages/curl:8.12.1 --restart=Never --rm -i --quiet -- curl --fail --silent http://lab-web)
printf '%s\n' "$response" | grep -Fq "Cloud Native Learning Lab" || { echo "网页返回内容不符合预期。" >&2; exit 1; }

echo "网页验证通过：2 个副本可用，Service 可以返回预期页面。"
