import http.client
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path

import psycopg

root = Path(__file__).resolve().parents[1]
expected_commit = os.environ["EXPECTED_COMMIT"]
password = secrets.token_urlsafe(24)
environment = os.environ.copy()
environment["ADMIN_PASSWORD"] = password
environment["ADMIN_SALT"] = secrets.token_urlsafe(24)
with psycopg.connect(environment["DATABASE_URL"], connect_timeout=5) as database:
    database.execute("SELECT 1")

process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "18090"], cwd=root, env=environment)
checks = []
try:
    deadline = time.monotonic() + 30
    while True:
        if process.poll() is not None:
            raise RuntimeError("候选应用在启动期间退出")
        with socket.socket() as connection:
            connection.settimeout(1)
            state = connection.connect_ex(("127.0.0.1", 18090))
        if state == 0:
            break
        if time.monotonic() > deadline:
            raise TimeoutError("候选应用启动超时")
        time.sleep(0.2)

    def call(method, path, body=None, cookie=None, expected=200):
        connection = http.client.HTTPConnection("127.0.0.1", 18090, timeout=10)
        headers = {"Content-Type": "application/json"}
        if cookie:
            headers["Cookie"] = cookie
        connection.request(method, path, json.dumps(body) if body is not None else None, headers)
        response = connection.getresponse()
        data = response.read()
        if response.status != expected:
            raise AssertionError(f"{method} {path}: HTTP {response.status}, 预期 {expected}")
        session_cookie = response.getheader("Set-Cookie")
        connection.close()
        return json.loads(data) if data else None, session_cookie

    call("GET", "/livez")
    call("GET", "/readyz")
    version, _ = call("GET", "/version")
    if version["commit"] != expected_commit:
        raise AssertionError("运行镜像中的版本与待测试提交不一致")
    checks.append("candidate_version")
    call("GET", "/api/tasks", expected=401)
    call("POST", "/api/login", {"username": "learner", "password": "invalid-password-for-negative-test"}, expected=401)
    _, cookie = call("POST", "/api/login", {"username": "learner", "password": password})
    cookie = cookie.split(";", 1)[0]
    checks.append("authentication")
    call("POST", "/api/tasks", {"title": ""}, cookie, 422)
    item, _ = call("POST", "/api/tasks", {"title": "CI 候选镜像真实计算验证"}, cookie, 201)
    tasks, _ = call("GET", "/api/tasks", cookie=cookie)
    if not any(task["id"] == item["id"] for task in tasks):
        raise AssertionError("刚创建的数据没有出现在查询中")
    updated, _ = call("PUT", f'/api/tasks/{item["id"]}', {"title": "CI 验证完成", "done": True}, cookie)
    if updated["done"] is not True:
        raise AssertionError("更新数据后状态未改变")
    call("DELETE", f'/api/tasks/{item["id"]}', cookie=cookie, expected=204)
    tasks, _ = call("GET", "/api/tasks", cookie=cookie)
    if any(task["id"] == item["id"] for task in tasks):
        raise AssertionError("删除后仍查询到原数据")
    checks.append("postgresql_crud")
    Path("test-report.json").write_text(json.dumps({"commit": expected_commit, "checks": checks, "passed": True}, ensure_ascii=False, indent=2) + "\n")
    print("候选应用版本、身份检查、输入校验和真实 PostgreSQL CRUD 验证通过")
finally:
    process.terminate()
    process.wait(timeout=10)
