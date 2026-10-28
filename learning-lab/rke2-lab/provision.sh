set -euo pipefail
cd /var/lib/rke2-lab
test -c /dev/kvm
test -f noble-server-cloudimg-amd64.img
virsh net-define network.xml
virsh net-start rke2-lab
virsh net-autostart rke2-lab
mkdir -p /var/lib/libvirt/images/rke2-lab
for item in server-1:11 worker-1:12 worker-2:13 worker-3:14; do
  role=${item%:*}
  number=${item#*:}
  name=rke2-${role}
  directory=/var/lib/libvirt/images/rke2-lab/${name}
  mkdir "$directory"
  qemu-img convert -f qcow2 -O qcow2 noble-server-cloudimg-amd64.img "$directory/root.qcow2"
  qemu-img resize "$directory/root.qcow2" 20G
  cloud-localds "$directory/seed.img" user-data "${name}-meta-data"
  virt-install --name "$name" --memory 4096 --vcpus 4 --cpu host-passthrough --virt-type kvm --os-variant ubuntu20.04 --import --disk path="$directory/root.qcow2",format=qcow2,bus=virtio --disk path="$directory/seed.img",device=cdrom --network network=rke2-lab,model=virtio,mac=52:54:00:cc:04:${number} --graphics none --noautoconsole --autostart
done
virsh list --all
