set -euo pipefail
cd "$(dirname "$0")"
: "${KUBECONFIG:?请指定管理员 kubeconfig 的绝对路径}"
export KUBECONFIG
for resource in $(kubectl -n monitoring get deployments,statefulsets,daemonsets -o name); do
  kubectl -n monitoring rollout status "$resource" --timeout=300s
done
kubectl -n monitoring get pods -o wide
kubectl -n monitoring get pvc
test "$(kubectl -n monitoring get pvc -o json | jq '[.items[] | select(.status.phase == "Bound")] | length')" -eq 3
curl --fail --silent http://127.0.0.1:3000/api/health | tee grafana-health.json
jq -e '.database == "ok"' grafana-health.json
curl --fail --silent http://127.0.0.1:9090/-/ready
curl --fail --silent http://127.0.0.1:9093/-/ready
curl --fail --silent http://127.0.0.1:9090/api/v1/targets > targets.json
jq -e '.status == "success" and (.data.activeTargets | length > 0) and ([.data.activeTargets[] | select(.health != "up")] | length == 0)' targets.json
jq -r '.data.activeTargets[] | [.labels.job, .labels.instance, .health] | @tsv' targets.json
curl --fail --silent --get --data-urlencode 'query=count(kube_node_info)' http://127.0.0.1:9090/api/v1/query | tee node-count.json
jq -e '.data.result[0].value[1] == "4"' node-count.json
curl --fail --silent --get --data-urlencode 'query=count(node_uname_info)' http://127.0.0.1:9090/api/v1/query | tee exporter-count.json
jq -e '.data.result[0].value[1] == "4"' exporter-count.json
curl --fail --silent --get --data-urlencode 'query=etcd_server_has_leader' http://127.0.0.1:9090/api/v1/query | tee etcd-leader.json
jq -e '.data.result[0].value[1] == "1"' etcd-leader.json
curl --fail --silent http://127.0.0.1:9090/api/v1/alertmanagers > alertmanagers.json
jq -e '.data.activeAlertmanagers | length == 1' alertmanagers.json
curl --fail --silent http://127.0.0.1:9093/api/v2/alerts > alerts.json
jq -e '[.[] | select(.labels.alertname == "Watchdog")] | length > 0' alerts.json
password=$(kubectl -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d)
curl --fail --silent --user "admin:${password}" http://127.0.0.1:3000/api/datasources/uid/prometheus/health | tee datasource-health.json
jq -e '.status == "OK"' datasource-health.json
curl --fail --silent --user "admin:${password}" 'http://127.0.0.1:3000/api/search?type=dash-db&limit=1000' > dashboards.json
jq -e 'length > 0' dashboards.json
jq -r '.[].title' dashboards.json
