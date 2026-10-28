import json
import os
import pathlib
import subprocess
import time

root = pathlib.Path(__file__).resolve().parent
k = ["kubectl", "--kubeconfig", os.environ["KUBECONFIG"], "-n", "interview-app"]
records = []
scaled = False
deadline = time.monotonic() + 360
while time.monotonic() < deadline:
    hpa = json.loads(subprocess.check_output(k + ["get", "hpa", "tasks", "-o", "json"]))
    deployment = json.loads(subprocess.check_output(k + ["get", "deployment", "tasks", "-o", "json"]))
    job = json.loads(subprocess.check_output(k + ["get", "job", "login-load", "-o", "json"]))
    record = {"time": time.time(), "hpa": hpa.get("status", {}), "deployment": deployment.get("status", {})}
    records.append(record)
    available = deployment.get("status", {}).get("availableReplicas", 0)
    scaled = scaled or available >= 3
    print("HPA", record["hpa"].get("currentReplicas"), record["hpa"].get("desiredReplicas"), "可用副本", available, flush=True)
    if job.get("status", {}).get("failed", 0):
        raise RuntimeError("负载 Job 失败")
    if job.get("status", {}).get("succeeded", 0):
        break
    time.sleep(5)
else:
    raise RuntimeError("负载等待超时")
assert scaled, "没有观察到至少三个可用副本"
subprocess.run(k + ["logs", "job/login-load"], check=True)
(root / "hpa-evidence.json").write_text(json.dumps(records, ensure_ascii=False, indent=2))
print("真实登录负载触发 HPA 扩容，负载 Job 完成", flush=True)
deadline = time.monotonic() + 300
while time.monotonic() < deadline:
    hpa = json.loads(subprocess.check_output(k + ["get", "hpa", "tasks", "-o", "json"]))
    if hpa.get("status", {}).get("currentReplicas") == 2 and hpa["status"].get("desiredReplicas") == 2:
        print("负载结束后自动缩容到两个副本", flush=True)
        break
    time.sleep(5)
else:
    raise RuntimeError("HPA 未恢复最小副本数")
