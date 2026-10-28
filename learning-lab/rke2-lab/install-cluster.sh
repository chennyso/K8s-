set -euo pipefail
cd /var/lib/rke2-lab
ssh_options=(-i /var/lib/rke2-lab/id_ed25519 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)
for number in 11 12 13 14; do
  address=192.168.204.${number}
  ssh "${ssh_options[@]}" ubuntu@"$address" 'sudo cloud-init status --wait'
  scp "${ssh_options[@]}" prepare-node.sh ubuntu@"$address":/home/ubuntu/
  ssh "${ssh_options[@]}" ubuntu@"$address" 'sudo bash /home/ubuntu/prepare-node.sh'
  scp "${ssh_options[@]}" work/install-rke2.sh work/rke2.linux-amd64.tar.gz work/rke2-images.linux-amd64.tar.zst sha256sum-amd64.txt ubuntu@"$address":/home/ubuntu/
  ssh "${ssh_options[@]}" ubuntu@"$address" 'mkdir -p /home/ubuntu/work'
  if [ "$number" = 11 ]; then
    role=server
    scp "${ssh_options[@]}" server.yaml ubuntu@"$address":/home/ubuntu/config.yaml
  else
    role=agent
    scp "${ssh_options[@]}" agent.yaml ubuntu@"$address":/home/ubuntu/config.yaml
    scp "${ssh_options[@]}" work/node-token ubuntu@"$address":/home/ubuntu/node-token
    ssh "${ssh_options[@]}" ubuntu@"$address" 'sudo install -d -m 700 /etc/rancher/rke2 && sudo install -m 600 /home/ubuntu/node-token /etc/rancher/rke2/node-token && rm /home/ubuntu/node-token'
  fi
  ssh "${ssh_options[@]}" ubuntu@"$address" "sudo env TMPDIR=/home/ubuntu/work INSTALL_RKE2_VERSION=v1.36.5+rke2r1 INSTALL_RKE2_TYPE=${role} INSTALL_RKE2_ARTIFACT_PATH=/home/ubuntu sh /home/ubuntu/install-rke2.sh"
  ssh "${ssh_options[@]}" ubuntu@"$address" 'sudo install -d -m 700 /etc/rancher/rke2 && sudo install -m 600 /home/ubuntu/config.yaml /etc/rancher/rke2/config.yaml'
  ssh "${ssh_options[@]}" ubuntu@"$address" "sudo systemctl enable --now rke2-${role}"
  if [ "$number" = 11 ]; then
    ssh "${ssh_options[@]}" ubuntu@"$address" 'sudo cat /var/lib/rancher/rke2/server/node-token' > work/node-token
    chmod 600 work/node-token
  fi
done
ssh "${ssh_options[@]}" ubuntu@192.168.204.11 'sudo /var/lib/rancher/rke2/bin/kubectl --kubeconfig /etc/rancher/rke2/rke2.yaml wait --for=condition=Ready nodes --all --timeout=300s'
