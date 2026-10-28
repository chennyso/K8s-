import base64
import json
import os
import pathlib
import subprocess

import requests

root = pathlib.Path(__file__).resolve().parent
values = json.loads((root / "secrets/platform.json").read_text())
session = requests.Session()
session.trust_env = False
session.headers["PRIVATE-TOKEN"] = values["gitlabtoken"]
base = "http://127.0.0.1:18080/api/v4"
response = session.post(base + "/projects", json={"name": "learning-tasks", "path": "learning-tasks", "visibility": "private", "initialize_with_readme": False}, timeout=30)
response.raise_for_status()
project = response.json()
(root / "gitlab-project.json").write_text(json.dumps(project))
response = session.post(base + "/user/runners", json={"runner_type": "project_type", "project_id": project["id"], "description": "204 Kubernetes 学习 Runner", "run_untagged": True}, timeout=30)
response.raise_for_status()
token = response.json()["token"]
k = ["kubectl", "--kubeconfig", os.environ["KUBECONFIG"]]
subprocess.run(k + ["apply", "-f", str(root / "k8s/runner.yaml")], check=True)
subprocess.run(k + ["-n", "ci", "create", "secret", "generic", "runner-token", "--from-literal=RUNNER_TOKEN=" + token], check=True, stdout=subprocess.DEVNULL)
subprocess.run(k + ["-n", "ci", "create", "secret", "docker-registry", "registry", "--docker-server=192.168.204.1:15000", "--docker-username=learning", "--docker-password=" + values["registry"]], check=True, stdout=subprocess.DEVNULL)
subprocess.run(k + ["-n", "ci", "create", "configmap", "runner-template", "--from-file=config.toml=" + str(root / "k8s/runner-template.toml")], check=True)
subprocess.run(k + ["-n", "ci", "create", "configmap", "buildkit-config", "--from-file=buildkitd.toml=" + str(root / "k8s/buildkitd.toml"), "--from-file=ca.crt=" + str(root / "secrets/ca.crt")], check=True)
auth = base64.b64encode(("learning:" + values["registry"]).encode()).decode()
auth_path = root / "secrets/registry-auth.json"
auth_path.write_text(json.dumps({"auths": {"192.168.204.1:15000": {"auth": auth}}}))
auth_path.chmod(0o600)
subprocess.run(k + ["-n", "ci", "create", "secret", "generic", "buildkit-auth", "--from-file=config.json=" + str(auth_path)], check=True)
response = session.post(base + f'/projects/{project["id"]}/variables', json={"key": "LEARNING_PASSWORD", "value": values["admin"], "masked": True}, timeout=30)
response.raise_for_status()
subprocess.run(k + ["-n", "argocd", "create", "secret", "generic", "learning-repository", "--from-literal=type=git", "--from-literal=url=http://192.168.204.1:18080/root/learning-tasks.git", "--from-literal=username=root", "--from-literal=password=" + values["gitlabtoken"]], check=True, stdout=subprocess.DEVNULL)
subprocess.run(k + ["-n", "argocd", "label", "secret", "learning-repository", "argocd.argoproj.io/secret-type=repository"], check=True)
print("GitLab 项目、Runner 和 Argo CD 仓库认证配置完成")
