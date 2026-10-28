set -euo pipefail
ssh -i /var/lib/rke2-lab/id_ed25519 ubuntu@192.168.204.13 sudo install -d -m 2770 -o 10001 -g 10001 /var/lib/loki-data
