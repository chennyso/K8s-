set -euo pipefail
cd /var/lib/rke2-lab/monitoring
sha256sum -c monitoring-images.sha256
ssh_options=(-i /var/lib/rke2-lab/id_ed25519 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)
for number in 11 12 13 14; do
  address=192.168.204.${number}
  scp "${ssh_options[@]}" monitoring-images.tar.gz ubuntu@"$address":/home/ubuntu/
  ssh "${ssh_options[@]}" ubuntu@"$address" 'sudo /var/lib/rancher/rke2/bin/ctr --address /run/k3s/containerd/containerd.sock --namespace k8s.io images import /home/ubuntu/monitoring-images.tar.gz && rm /home/ubuntu/monitoring-images.tar.gz'
done
