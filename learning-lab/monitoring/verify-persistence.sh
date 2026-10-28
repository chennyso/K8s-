set -euo pipefail
cd "$(dirname "$0")"
: "${KUBECONFIG:?请指定管理员 kubeconfig 的绝对路径}"
export KUBECONFIG
timestamp=$(jq -r '.data.result[0].value[0]' node-count.json)
before=$(kubectl -n monitoring get pod prometheus-monitoring-prometheus-0 -o jsonpath='{.metadata.uid}')
kubectl -n monitoring delete pod prometheus-monitoring-prometheus-0
kubectl -n monitoring wait --for=create pod/prometheus-monitoring-prometheus-0 --timeout=180s
kubectl -n monitoring wait --for=condition=Ready pod/prometheus-monitoring-prometheus-0 --timeout=300s
after=$(kubectl -n monitoring get pod prometheus-monitoring-prometheus-0 -o jsonpath='{.metadata.uid}')
test "$before" != "$after"
printf '重启前 Pod UID：%s\n重启后 Pod UID：%s\n历史查询时间戳：%s\n' "$before" "$after" "$timestamp"
curl --fail --silent --get --data-urlencode "query=count(kube_node_info @ ${timestamp})" http://127.0.0.1:9090/api/v1/query | tee persistence-query.json
jq -e '.data.result[0].value[1] == "4"' persistence-query.json
