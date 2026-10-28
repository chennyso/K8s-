set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y curl ca-certificates apparmor apparmor-utils nfs-common iptables
swapoff -a
test -z "$(swapon --noheadings)"
systemctl is-active systemd-timesyncd
