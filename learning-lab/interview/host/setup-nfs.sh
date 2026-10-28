set -euo pipefail
cd /var/lib/interview-lab
install -d -m 2770 -o 0 -g 0 /var/lib/interview-lab/nfs
install -d -m 755 /etc/exports.d
install -m 644 host/nfs.exports /etc/exports.d/interview-lab.exports
exportfs -rav
systemctl enable --now nfs-kernel-server
exportfs -v
