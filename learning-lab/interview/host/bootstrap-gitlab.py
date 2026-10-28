import json
import pathlib
import subprocess

root = pathlib.Path("/var/lib/interview-lab")
values = json.loads((root / "secrets/platform.json").read_text())
subprocess.run(["docker", "exec", "-i", "-e", "BOOTSTRAP_TOKEN=" + values["gitlabtoken"], "interview-gitlab", "gitlab-rails", "runner", "-"], input=(root / "host/bootstrap-token.rb").read_text(), text=True, check=True)
