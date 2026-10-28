set -euo pipefail
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml
export PATH=/var/lib/rancher/rke2/bin:$PATH
kubectl get --raw='/readyz?verbose'
kubectl wait --for=condition=Ready nodes --all --timeout=300s
test "$(kubectl get nodes -o name | wc -l)" -eq 4
kubectl get nodes -o wide
for resource in $(kubectl get daemonsets,deployments -n kube-system -o name); do
  kubectl rollout status "$resource" -n kube-system --timeout=180s
done
kubectl apply -f /home/ubuntu/validation.yaml
kubectl rollout status daemonset/web -n cluster-validation --timeout=180s
test "$(kubectl get pods -n cluster-validation -l app=validation-web -o name | wc -l)" -eq 3
for pod in $(kubectl get pods -n cluster-validation -l app=validation-web -o jsonpath='{.items[*].metadata.name}'); do
  kubectl exec -n cluster-validation "$pod" -- nslookup kubernetes.default.svc.cluster.local
  kubectl exec -n cluster-validation "$pod" -- wget -qO- -T 10 http://web.cluster-validation.svc.cluster.local/hostname
  for address in $(kubectl get pods -n cluster-validation -l app=validation-web -o jsonpath='{.items[*].status.podIP}'); do
    kubectl exec -n cluster-validation "$pod" -- wget -qO- -T 10 "http://${address}:8080/hostname"
  done
done
kubectl top nodes
kubectl get pods -A -o wide
RKE2_CONFIG_FILE=/dev/null rke2 etcd-snapshot save --name acceptance
RKE2_CONFIG_FILE=/dev/null rke2 etcd-snapshot ls
