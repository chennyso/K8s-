set -euo pipefail
: "${KUBECONFIG:?请指定可以访问实验集群的 kubeconfig}"
pids=()
cleanup() {
  for pid in "${pids[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then kill "$pid"; fi
  done
}
trap cleanup EXIT INT TERM
kubectl -n pod-lab port-forward service/pod-web 18084:8080 &
pids+=("$!")
kubectl -n interview-app port-forward service/tasks 18083:8080 &
pids+=("$!")
kubectl -n argocd port-forward service/argocd-server 18085:80 &
pids+=("$!")
kubectl -n monitoring port-forward service/monitoring-grafana 3000:80 &
pids+=("$!")
kubectl -n monitoring port-forward service/monitoring-prometheus 9090:9090 &
pids+=("$!")
kubectl -n monitoring port-forward service/monitoring-alertmanager 9093:9093 &
pids+=("$!")
printf 'Pod http://127.0.0.1:18084\n任务系统 http://127.0.0.1:18083\nArgo CD http://127.0.0.1:18085\nGrafana http://127.0.0.1:3000\nPrometheus http://127.0.0.1:9090\nAlertmanager http://127.0.0.1:9093\n'
while true; do
  for pid in "${pids[@]}"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      wait "$pid"
      exit 1
    fi
  done
  sleep 2
done
