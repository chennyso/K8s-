import json
import pathlib
import subprocess

root = pathlib.Path("/var/lib/interview-lab")
values = json.loads((root / "secrets/platform.json").read_text())
registry = "192.168.204.1:15000"
docker_certs = pathlib.Path("/etc/docker/certs.d") / registry
docker_certs.mkdir(parents=True, exist_ok=True)
subprocess.run(["cp", str(root / "certs/ca.crt"), str(docker_certs / "ca.crt")], check=True)
subprocess.run(["docker", "login", registry, "--username", "learning", "--password-stdin"], input=values["registry"], text=True, check=True)
for address in ["192.168.204.11", "192.168.204.12", "192.168.204.13", "192.168.204.14"]:
    ssh = ["ssh", "-i", "/var/lib/rke2-lab/id_ed25519", "ubuntu@" + address]
    subprocess.run([*ssh, "sudo", "install", "-d", "/etc/rancher/rke2"], check=True)
    subprocess.run(["scp", "-i", "/var/lib/rke2-lab/id_ed25519", str(root / "certs/ca.crt"), "ubuntu@" + address + ":/home/ubuntu/interview-ca.crt"], check=True)
    subprocess.run([*ssh, "sudo", "cp", "/home/ubuntu/interview-ca.crt", "/etc/rancher/rke2/interview-ca.crt"], check=True)
    subprocess.run(["scp", "-i", "/var/lib/rke2-lab/id_ed25519", str(root / "host/registries.yaml"), "ubuntu@" + address + ":/home/ubuntu/registries.yaml"], check=True)
    subprocess.run([*ssh, "sudo", "install", "-m", "600", "/home/ubuntu/registries.yaml", "/etc/rancher/rke2/registries.yaml"], check=True)
    service = "rke2-server" if address.endswith(".11") else "rke2-agent"
    subprocess.run([*ssh, "sudo", "systemctl", "restart", service], check=True)
