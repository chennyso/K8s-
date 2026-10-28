set -euo pipefail
cd /var/lib/rke2-lab
ssh_options=(-i /var/lib/rke2-lab/id_ed25519 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)
jobs=()
for number in 12 13 14; do
  address=192.168.204.${number}
  scp "${ssh_options[@]}" prepare-node.sh ubuntu@"$address":/home/ubuntu/
  ssh "${ssh_options[@]}" ubuntu@"$address" 'sudo cloud-init status --wait && sudo bash /home/ubuntu/prepare-node.sh' > "work/prepare-${number}.log" 2>&1 &
  jobs+=("$!")
done
for job in "${jobs[@]}"; do
  wait "$job"
done
