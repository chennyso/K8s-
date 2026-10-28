set -euo pipefail
cd "$(dirname "$0")"
original_image=$(kubectl -n interview-app get deployment tasks -o jsonpath='{.spec.template.spec.containers[0].image}')
restore() {
  kubectl -n interview-app set image deployment/tasks "tasks=$original_image"
  kubectl -n argocd patch application learning-tasks --type=merge --patch-file=k8s/argocd-auto-patch.yaml
}
trap restore EXIT
kubectl -n argocd patch application learning-tasks --type=merge --patch-file=k8s/argocd-manual-patch.yaml
kubectl -n interview-app patch deployment tasks --patch-file=k8s/failed-image-patch.yaml
set +e
output=$(kubectl -n interview-app rollout status deployment/tasks --timeout=45s 2>&1)
result=$?
set -e
printf '%s\n' "$output"
test "$result" -ne 0
printf '%s' "$output" | rg 'timed out'
kubectl -n interview-app get deployment tasks -o json | jq -e '.status.availableReplicas >= 2'
kubectl -n interview-app get pods -l app=tasks
kubectl -n interview-app set image deployment/tasks "tasks=$original_image"
kubectl -n interview-app rollout status deployment/tasks --timeout=180s
kubectl -n argocd patch application learning-tasks --type=merge --patch-file=k8s/argocd-auto-patch.yaml
trap - EXIT
printf '错误镜像发布期间旧副本可用，修正镜像配置后恢复成功\n'
