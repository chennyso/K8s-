import json
import pathlib

import requests

root = pathlib.Path(__file__).resolve().parent
values = json.loads((root / "secrets/platform.json").read_text())
project = json.loads((root / "gitlab-project.json").read_text())
session = requests.Session()
session.trust_env = False
session.headers["PRIVATE-TOKEN"] = values["gitlabtoken"]
base = f'http://127.0.0.1:18080/api/v4/projects/{project["id"]}'
response = session.get(base + "/pipelines", timeout=20)
response.raise_for_status()
pipelines = response.json()
print("流水线", [(item["id"], item["status"], item["sha"]) for item in pipelines])
if pipelines:
    response = session.get(base + f'/pipelines/{pipelines[0]["id"]}/jobs', timeout=20)
    response.raise_for_status()
    jobs = response.json()
    print("任务", [(item["id"], item["name"], item["status"]) for item in jobs])
    (root / "pipeline-evidence.json").write_text(json.dumps({"pipeline": pipelines[0], "jobs": jobs}, ensure_ascii=False, indent=2))
    for job in jobs:
        response = session.get(base + f'/jobs/{job["id"]}/trace', timeout=20)
        response.raise_for_status()
        (root / f'job-{job["id"]}.log').write_text(response.text)
