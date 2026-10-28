import base64
import json
import os
import pathlib
import subprocess
import time

import requests

root = pathlib.Path(__file__).resolve().parent
k = ["kubectl", "--kubeconfig", os.environ["KUBECONFIG"]]
session = requests.Session()
session.trust_env = False
evidence = {"time": time.time()}


def get(args):
    return json.loads(subprocess.check_output(k + args + ["-o", "json"]))


def http(url, **kwargs):
    response = session.get(url, timeout=30, **kwargs)
    response.raise_for_status()
    return response


nodes = get(["get", "nodes"])
assert len(nodes["items"]) == 4
for node in nodes["items"]:
    assert not node["spec"].get("unschedulable", False)
    conditions = {item["type"]: item["status"] for item in node["status"]["conditions"]}
    assert conditions["Ready"] == "True"
    assert conditions["DiskPressure"] == "False"
evidence["nodes"] = [{"name": node["metadata"]["name"], "version": node["status"]["nodeInfo"]["kubeletVersion"]} for node in nodes["items"]]
pods = get(["get", "pods", "-A"])
active = [pod for pod in pods["items"] if pod["status"]["phase"] != "Succeeded"]
for pod in active:
    assert pod["status"]["phase"] == "Running", pod["metadata"]
    assert all(container["ready"] for container in pod["status"]["containerStatuses"]), pod["metadata"]
evidence["running_ready_pods"] = len(active)
print("四个节点 Ready，全部活动 Pod 就绪，节点均可调度", flush=True)
for url in ["http://127.0.0.1:18083/", "http://127.0.0.1:18083/readyz", "http://127.0.0.1:18084/status.json", "http://127.0.0.1:18084/metrics.txt", "http://127.0.0.1:3000/api/health", "http://127.0.0.1:9090/-/ready", "http://127.0.0.1:9093/-/ready", "http://127.0.0.1:18085/healthz", "http://127.0.0.1:18080/users/sign_in"]:
    http(url)
http("https://localhost:18443/readyz", headers={"Host": "tasks.204.test"}, verify=str(root / "secrets/ca.crt"))
print("全部管理页面、业务入口和 HTTPS 校验通过", flush=True)


def query(expression):
    data = http("http://127.0.0.1:9090/api/v1/query", params={"query": expression}).json()
    assert data["status"] == "success"
    return data["data"]["result"]


evidence["prometheus_targets"] = int(query("count(up)")[0]["value"][1])
assert evidence["prometheus_targets"] >= 33
assert not query("up == 0")
assert len(query("pod_lab_heartbeats_total")) == 2
assert query("learning_http_requests_total")
assert not any(alert["labels"].get("alertname") == "LearningAppUnavailable" for alert in http("http://127.0.0.1:9090/api/v1/alerts").json()["data"]["alerts"])
print("Prometheus 全部目标 UP，业务指标可查询，演练告警已解除", flush=True)
evidence["loki"] = {}
for namespace, container in [("interview-app", "tasks"), ("pod-lab", "writer")]:
    data = http("http://127.0.0.1:13100/loki/api/v1/query_range", params={"query": f'{{namespace="{namespace}",container="{container}"}}', "limit": 5}).json()
    assert data["status"] == "success" and data["data"]["result"]
    evidence["loki"][namespace] = len(data["data"]["result"])
grafana = json.loads((root / "secrets/grafana-admin.json").read_text())
password = base64.b64decode(grafana["data"]["admin-password"]).decode()
health = http("http://127.0.0.1:3000/api/datasources/uid/loki/health", auth=("admin", password)).json()
assert health["status"] == "OK", health
print("Loki 查询真实应用日志，Grafana Loki 数据源健康检查通过", flush=True)
app = get(["-n", "argocd", "get", "application", "learning-tasks"])
assert app["status"]["sync"]["status"] == "Synced"
assert app["status"]["health"]["status"] == "Healthy"
deployment = get(["-n", "interview-app", "get", "deployment", "tasks"])
assert deployment["spec"]["template"]["spec"]["containers"][0]["image"].endswith(":1.0.1")
pipeline = json.loads((root / "pipeline-evidence.json").read_text())
assert pipeline["pipeline"]["status"] == "success"
assert all(job["status"] == "success" for job in pipeline["jobs"])
assert app["status"]["sync"]["revision"] == pipeline["pipeline"]["sha"]
evidence["release"] = {"pipeline": pipeline["pipeline"]["id"], "revision": app["status"]["sync"]["revision"], "image": deployment["spec"]["template"]["spec"]["containers"][0]["image"]}
print("GitLab 流水线成功，Argo CD 同步提交一致，1.0.1 镜像已运行", flush=True)
for kind, name in [("backup", "learning-drill"), ("restore", "learning-drill-restore")]:
    resource = get(["-n", "velero", "get", kind, name])
    assert resource["status"]["phase"] == "Completed"
    evidence[kind] = resource["status"]
hpa = get(["-n", "interview-app", "get", "hpa", "tasks"])
assert hpa["status"]["currentReplicas"] == 2 and hpa["status"]["desiredReplicas"] == 2
evidence["hpa"] = hpa["status"]
print("备份恢复 Completed，HPA 已恢复两个副本", flush=True)
(root / "final-acceptance.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
print("平台最终验收通过", flush=True)
