set -euo pipefail
cd /var/lib/interview-lab
archive=${1:-platform-images.tar.gz}
for address in 192.168.204.11 192.168.204.12 192.168.204.13 192.168.204.14; do
  gzip -dc "$archive" | ssh -i /var/lib/rke2-lab/id_ed25519 ubuntu@"$address" sudo /var/lib/rancher/rke2/bin/ctr --address /run/k3s/containerd/containerd.sock -n k8s.io images import --local --platform linux/amd64 -
done
