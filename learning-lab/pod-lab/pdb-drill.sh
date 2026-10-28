set -euo pipefail
node=$(kubectl -n pod-lab get pod -l app=pod-web -o jsonpath='{.items[0].spec.nodeName}')
trap 'kubectl uncordon "$node"' EXIT
kubectl -n pod-lab get pdb pod-web
kubectl drain "$node" --pod-selector=app=pod-web --ignore-daemonsets --delete-emptydir-data --timeout=180s
kubectl -n pod-lab rollout status deployment/pod-web --timeout=120s
kubectl -n pod-lab exec client-allowed -- wget -qO- -T 5 http://pod-web:8080/status.json
kubectl -n pod-lab get pods -l app=pod-web -o wide
kubectl uncordon "$node"
trap - EXIT
printf '\n已通过驱逐 API 完成 Pod 项目维护演练，节点已经恢复调度\n'
