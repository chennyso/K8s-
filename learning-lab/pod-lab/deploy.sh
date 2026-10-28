set -euo pipefail
cd "$(dirname "$0")"
: "${KUBECONFIG:?请指定管理员 kubeconfig 的绝对路径}"
kubectl apply -f namespace.yaml
kubectl -n pod-lab create configmap pod-lab-scripts --from-file=writer.sh --from-file=server.sh --from-file=index.html --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f workload.yaml -f access.yaml -f clients.yaml
kubectl -n pod-lab rollout status deployment/pod-web --timeout=180s
kubectl -n pod-lab wait --for=condition=Ready pod/client-allowed pod/client-denied --timeout=180s
