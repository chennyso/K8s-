import base64
import json
import pathlib
import subprocess

root = pathlib.Path(__file__).resolve().parent
values = json.loads((root / "secrets/platform.json").read_text())
folder = root / "app"
subprocess.run(["git", "-C", str(folder), "init", "-b", "main"], check=True)
subprocess.run(["git", "-C", str(folder), "config", "user.name", "Learning Lab"], check=True)
subprocess.run(["git", "-C", str(folder), "config", "user.email", "learning@204.test"], check=True)
subprocess.run(["git", "-C", str(folder), "add", "Dockerfile", "requirements.txt", "app.py", "index.html", "wheels", "tests", "gitops", ".gitlab-ci.yml", ".gitignore"], check=True)
subprocess.run(["git", "-C", str(folder), "commit", "-m", "Deploy Kubernetes learning application with real integration checks"], check=True)
auth = base64.b64encode(("root:" + values["gitlabtoken"]).encode()).decode()
subprocess.run(["git", "-C", str(folder), "-c", "http.extraHeader=Authorization: Basic " + auth, "push", "http://127.0.0.1:18080/root/learning-tasks.git", "main"], check=True)
