import concurrent.futures
import http.client
import json
import os
import time

password = os.environ["LEARNING_PASSWORD"]
deadline = time.monotonic() + 180


def load(worker):
    connection = http.client.HTTPConnection("tasks.interview-app.svc.cluster.local", 8080, timeout=30)
    count = 0
    while time.monotonic() < deadline:
        connection.request("POST", "/api/login", json.dumps({"username": "learner", "password": password}), {"Content-Type": "application/json"})
        response = connection.getresponse()
        body = response.read()
        assert response.status == 200, (response.status, body)
        count += 1
    return count


with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
    print("实际登录请求总数", sum(pool.map(load, range(12))))
