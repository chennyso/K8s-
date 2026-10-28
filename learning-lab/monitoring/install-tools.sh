set -euo pipefail
cd /var/lib/rke2-lab/monitoring
tar -xzf helm-linux.tar.gz
ssh_options=(-i /var/lib/rke2-lab/id_ed25519 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)
ssh "${ssh_options[@]}" ubuntu@192.168.204.11 'mkdir -p /home/ubuntu/monitoring'
scp "${ssh_options[@]}" linux-amd64/helm kube-prometheus-stack-92.14.0.tgz values.yaml storage.yaml ubuntu@192.168.204.11:/home/ubuntu/monitoring/
ssh "${ssh_options[@]}" ubuntu@192.168.204.11 'sudo install -m 755 /home/ubuntu/monitoring/helm /usr/local/bin/helm && helm version --short'
