import concurrent.futures
import json
import pathlib
import time

import requests

root = pathlib.Path(__file__).resolve().parent
values = json.loads((root / "secrets/platform.json").read_text())
base = "http://127.0.0.1:18083"
session = requests.Session()
session.trust_env = False
response = session.get(base + "/api/tasks", timeout=10)
assert response.status_code == 401, response.text
response = session.post(base + "/api/login", json={"username": "learner", "password": values["admin"]}, timeout=10)
response.raise_for_status()
created = session.post(base + "/api/tasks", json={"title": "持久化恢复验收记录"}, timeout=10)
assert created.status_code == 201, created.text
task_id = created.json()["id"]
response = session.put(base + f"/api/tasks/{task_id}", json={"title": "持久化恢复验收记录", "done": True}, timeout=10)
response.raise_for_status()
assert response.json()["done"]
response = session.get(base + "/api/tasks", timeout=10)
response.raise_for_status()
assert any(task["id"] == task_id for task in response.json())
print("真实登录、权限拒绝和 PostgreSQL 创建、修改、查询通过", task_id)
(root / "acceptance-task.json").write_text(json.dumps({"task_id": task_id}))
response = session.post(base + "/api/tasks", json={"title": "删除接口验收"}, timeout=10)
response.raise_for_status()
delete_id = response.json()["id"]
response = session.delete(base + f"/api/tasks/{delete_id}", timeout=10)
assert response.status_code == 204
response = session.get(base + "/metrics", timeout=10)
response.raise_for_status()
assert "learning_http_requests_total" in response.text
print("删除接口、Prometheus 指标通过")
secure = requests.Session()
secure.trust_env = False
response = secure.get("https://localhost:18443/readyz", headers={"Host": "tasks.204.test"}, verify=str(root / "secrets/ca.crt"), timeout=10)
response.raise_for_status()
print("HTTPS CA 和主机名校验通过")
