set -euo pipefail
cd "$(dirname "$0")"
kubectl apply -f faults/
for attempt in $(seq 1 90); do
  crash=$(kubectl -n pod-lab get pod fault-crash -o jsonpath='{.status.containerStatuses[0].state.waiting.reason}')
  oom=$(kubectl -n pod-lab get pod fault-oom -o jsonpath='{.status.containerStatuses[0].state.terminated.reason}')
  pending=$(kubectl -n pod-lab get pod fault-pending -o jsonpath='{.status.conditions[?(@.type=="PodScheduled")].reason}')
  if [ "$crash" = CrashLoopBackOff ] && [ "$oom" = OOMKilled ] && [ "$pending" = Unschedulable ]; then break; fi
  sleep 2
done
test "$crash" = CrashLoopBackOff
test "$oom" = OOMKilled
test "$pending" = Unschedulable
kubectl -n pod-lab get pods fault-crash fault-oom fault-pending -o wide
kubectl -n pod-lab get pod fault-oom -o jsonpath='{.status.containerStatuses[0].state.terminated}'
kubectl -n pod-lab logs fault-crash --previous
kubectl -n pod-lab describe pod fault-pending
kubectl -n pod-lab delete -f faults/ --wait=true
printf '\nCrashLoopBackOff、OOMKilled、Unschedulable 演练完成，故障资源已清理\n'
