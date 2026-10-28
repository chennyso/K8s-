set -euo pipefail
cd "$(dirname "$0")"
: "${KUBECONFIG:?请指定 kubeconfig}"
k() { kubectl -n pod-lab "$@"; }
wait_value() {
  for attempt in $(seq 1 90); do
    value=$(k get pod "$1" -o "jsonpath=$2")
    if [ "$value" = "$3" ]; then return; fi
    sleep 2
  done
  printf '等待失败：%s %s 期望=%s 实际=%s\n' "$1" "$2" "$3" "$value"
  return 1
}
pod=$(k get pod -l app=pod-web -o jsonpath='{.items[0].metadata.name}')
uid=$(k get pod "$pod" -o jsonpath='{.metadata.uid}')
printf '\n共享进程和 localhost 通信\n'
k exec "$pod" -c inspector -- ps
k exec "$pod" -c inspector -- wget -qO- http://127.0.0.1:8080/status.json
k exec client-allowed -- nslookup pod-web.pod-lab.svc.cluster.local
k exec client-allowed -- wget -qO- -T 5 http://pod-web:8080/status.json
printf '\nNetworkPolicy 拒绝未授权来源\n'
set +e
denied=$(k exec client-denied -- wget -qO- -T 3 http://pod-web:8080/status.json 2>&1)
result=$?
set -e
printf '%s\n' "$denied"
test "$result" -ne 0
printf '%s' "$denied" | rg 'timed out|timeout'
printf '\nreadiness 摘除端点\n'
restarts=$(k get pod "$pod" -o jsonpath='{.status.containerStatuses[?(@.name=="server")].restartCount}')
k exec "$pod" -c inspector -- rm /data/ready
wait_value "$pod" '{.status.conditions[?(@.type=="Ready")].status}' False
k get endpointslice -l kubernetes.io/service-name=pod-web -o json | jq -e '[.items[].endpoints[] | select(.conditions.ready==true)] | length==1'
k exec client-allowed -- wget -qO- -T 5 http://pod-web:8080/status.json
test "$(k get pod "$pod" -o jsonpath='{.status.containerStatuses[?(@.name=="server")].restartCount}')" = "$restarts"
k exec "$pod" -c inspector -- touch /data/ready
k wait --for=condition=Ready pod/"$pod" --timeout=60s
printf '\nwriter 进程退出和容器重启\n'
writer_restarts=$(k get pod "$pod" -o jsonpath='{.status.containerStatuses[?(@.name=="writer")].restartCount}')
k exec "$pod" -c inspector -- sh -ec 'kill -TERM "$(cat /data/writer.pid)"'
wait_value "$pod" '{.status.containerStatuses[?(@.name=="writer")].restartCount}' "$((writer_restarts+1))"
test "$(k get pod "$pod" -o jsonpath='{.metadata.uid}')" = "$uid"
test "$(k get pod "$pod" -o jsonpath='{.status.containerStatuses[?(@.name=="server")].restartCount}')" = "$restarts"
k logs "$pod" -c writer --previous --tail=3
printf '\nliveness 重启 server 容器\n'
k exec "$pod" -c inspector -- rm /data/live
wait_value "$pod" '{.status.containerStatuses[?(@.name=="server")].restartCount}' "$((restarts+1))"
k wait --for=condition=Ready pod/"$pod" --timeout=90s
printf '\nRBAC 允许读取并拒绝删除\n'
kubectl auth can-i list pods -n pod-lab --as=system:serviceaccount:pod-lab:learner
set +e
answer=$(kubectl auth can-i delete pods -n pod-lab --as=system:serviceaccount:pod-lab:learner)
result=$?
set -e
test "$answer" = no
test "$result" -eq 1
printf 'delete pods=%s\n' "$answer"
printf '\nStatefulSet 重建后保留 PVC 数据\n'
token="pod-lab-$(date +%s)"
k exec notebook-0 -- sh -ec "printf '%s' '$token' > /data/notes.txt"
notebook_uid=$(k get pod notebook-0 -o jsonpath='{.metadata.uid}')
k delete pod notebook-0 --wait=true
k wait --for=condition=Ready pod/notebook-0 --timeout=180s
test "$(k get pod notebook-0 -o jsonpath='{.metadata.uid}')" != "$notebook_uid"
test "$(k exec notebook-0 -- cat /data/notes.txt)" = "$token"
printf '\nDeployment 重建和 emptyDir 生命周期\n'
k exec "$pod" -c inspector -- touch /data/ephemeral-marker
k delete pod "$pod" --wait=true
k rollout status deployment/pod-web --timeout=180s
for current in $(k get pod -l app=pod-web -o jsonpath='{.items[*].metadata.name}'); do
  k exec "$current" -c inspector -- test ! -e /data/ephemeral-marker
done
printf '\nJob 完成\n'
k apply -f http-check.yaml
k wait --for=condition=Complete job/http-check --timeout=90s
k logs job/http-check
printf '\n扩容和恢复副本数\n'
k scale deployment/pod-web --replicas=3
k rollout status deployment/pod-web --timeout=120s
k scale deployment/pod-web --replicas=2
k rollout status deployment/pod-web --timeout=120s
printf '\n验收成功\n'
k get pods,pvc,pdb
