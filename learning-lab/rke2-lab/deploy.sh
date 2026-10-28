set -euo pipefail
cd /var/lib/rke2-lab
exec > work/deploy.log 2>&1
cd work
sha256sum --ignore-missing -c ../sha256sum-amd64.txt
cd ..
bash install-cluster.sh
ssh_options=(-i /var/lib/rke2-lab/id_ed25519 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)
for number in 11 12 13 14; do
  address=192.168.204.${number}
  scp "${ssh_options[@]}" work/busybox-1.37.0.tar ubuntu@"$address":/home/ubuntu/
  ssh "${ssh_options[@]}" ubuntu@"$address" 'sudo /var/lib/rancher/rke2/bin/ctr --address /run/k3s/containerd/containerd.sock --namespace k8s.io images import /home/ubuntu/busybox-1.37.0.tar'
done
scp "${ssh_options[@]}" validation.yaml validate-cluster.sh ubuntu@192.168.204.11:/home/ubuntu/
ssh "${ssh_options[@]}" ubuntu@192.168.204.11 'sudo bash /home/ubuntu/validate-cluster.sh' > work/acceptance.log 2>&1
