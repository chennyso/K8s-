set -euo pipefail
cd /var/lib/rke2-lab/monitoring
ssh_options=(-i /var/lib/rke2-lab/id_ed25519 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)
ssh "${ssh_options[@]}" ubuntu@192.168.204.12 'sudo install -d -m 2770 -o 1000 -g 2000 /var/lib/monitoring/prometheus'
ssh "${ssh_options[@]}" ubuntu@192.168.204.13 'sudo install -d -m 2770 -o 472 -g 472 /var/lib/monitoring/grafana'
ssh "${ssh_options[@]}" ubuntu@192.168.204.14 'sudo install -d -m 2770 -o 1000 -g 2000 /var/lib/monitoring/alertmanager'
for number in 11 12 13 14; do
  address=192.168.204.${number}
  role=agent
  file=agent-metrics.yaml
  if [ "$number" = 11 ]; then
    role=server
    file=server-metrics.yaml
  fi
  scp "${ssh_options[@]}" "$file" ubuntu@"$address":/home/ubuntu/monitoring-metrics.yaml
  ssh "${ssh_options[@]}" ubuntu@"$address" "sudo install -d -m 700 /etc/rancher/rke2/config.yaml.d && sudo install -m 600 /home/ubuntu/monitoring-metrics.yaml /etc/rancher/rke2/config.yaml.d/monitoring.yaml && sudo systemctl restart rke2-${role}"
done
