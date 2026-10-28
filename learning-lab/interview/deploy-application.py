import json
import os
import pathlib
import subprocess

root = pathlib.Path(__file__).resolve().parent
values = json.loads((root / "secrets/platform.json").read_text())
k = ["kubectl", "--kubeconfig", os.environ["KUBECONFIG"]]
subprocess.run(k + ["apply", "-f", str(root / "k8s/application.yaml")], check=True)
subprocess.run(k + ["-n", "interview-app", "create", "secret", "generic", "application", "--from-env-file=" + str(root / "secrets/application.env")], check=True)
subprocess.run(k + ["-n", "interview-app", "create", "secret", "docker-registry", "registry", "--docker-server=192.168.204.1:15000", "--docker-username=learning", "--docker-password=" + values["registry"]], check=True, stdout=subprocess.DEVNULL)
subprocess.run(k + ["-n", "cert-manager", "create", "secret", "tls", "interview-root-ca", "--cert=" + str(root / "secrets/ca.crt"), "--key=" + str(root / "secrets/ca.key")], check=True)
subprocess.run(k + ["apply", "-f", str(root / "k8s/certificates.yaml")], check=True)
subprocess.run(k + ["-n", "interview-app", "rollout", "status", "deployment/postgres", "--timeout=240s"], check=True)
subprocess.run(k + ["-n", "interview-app", "rollout", "status", "deployment/tasks", "--timeout=240s"], check=True)
