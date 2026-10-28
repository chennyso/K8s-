import json
import os
import pathlib
import subprocess
import time

import requests

root = pathlib.Path(__file__).resolve().parent
values = json.loads((root / "secrets/platform.json").read_text())
k = ["kubectl", "--kubeconfig", os.environ["KUBECONFIG"], "-n", "interview-app"]


def get(resource):
    return json.loads(subprocess.check_output(k + ["get", resource, "-o", "json"]))


def wait_condition(check, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(3)
    raise RuntimeError("等待条件超时")


tasks = get("pods")
pods = [pod for pod in tasks["items"] if pod["metadata"].get("labels", {}).get("app") == "tasks"]
before = {pod["metadata"]["uid"]: sum(status["restartCount"] for status in pod["status"]["containerStatuses"]) for pod in pods}
print("数据库故障演练开始", flush=True)
subprocess.run(k + ["scale", "deployment/postgres", "--replicas=0"], check=True)
wait_condition(lambda: all(not condition["status"] == "True" for pod in get("pods")["items"] if pod["metadata"].get("labels", {}).get("app") == "tasks" for condition in pod["status"].get("conditions", []) if condition["type"] == "Ready"), 90)
wait_condition(lambda: any(alert["labels"].get("alertname") == "LearningAppUnavailable" and alert["state"] == "firing" for alert in requests.get("http://127.0.0.1:9090/api/v1/alerts", timeout=10).json()["data"]["alerts"]), 150)
print("Prometheus 实际触发 LearningAppUnavailable 告警", flush=True)
for pod in get("pods")["items"]:
    if pod["metadata"]["uid"] in before:
        assert sum(status["restartCount"] for status in pod["status"]["containerStatuses"]) == before[pod["metadata"]["uid"]]
print("数据库停止时应用退出就绪状态，存活容器没有增加重启次数", flush=True)
subprocess.run(k + ["scale", "deployment/postgres", "--replicas=1"], check=True)
subprocess.run(k + ["rollout", "status", "deployment/postgres", "--timeout=180s"], check=True)
subprocess.run(k + ["rollout", "status", "deployment/tasks", "--timeout=180s"], check=True)
dbpod = next(pod["metadata"]["name"] for pod in get("pods")["items"] if pod["metadata"].get("labels", {}).get("app") == "postgres")
result = subprocess.check_output(k + ["exec", dbpod, "--", "psql", "-U", "learning", "-d", "learning", "-Atc", "SELECT count(*) FROM tasks WHERE title='持久化恢复验收记录'"], text=True).strip()
assert int(result) >= 1
print("PostgreSQL 重建后保留验收数据", flush=True)
pod = next(pod["metadata"]["name"] for pod in get("pods")["items"] if pod["metadata"].get("labels", {}).get("app") == "tasks")
subprocess.run(k + ["delete", "pod", pod, "--wait=true"], check=True)
subprocess.run(k + ["rollout", "status", "deployment/tasks", "--timeout=180s"], check=True)
print("应用 Pod 删除后控制器恢复副本数", flush=True)
