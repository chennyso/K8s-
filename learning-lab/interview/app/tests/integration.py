import http.client
import json
import os

connection = http.client.HTTPConnection("tasks.interview-app.svc.cluster.local", 8080, timeout=10)


def call(method, path, body=None, cookie=None, expected=200):
    headers = {"Content-Type": "application/json"}
    if cookie:
        headers["Cookie"] = cookie
    connection.request(method, path, json.dumps(body) if body is not None else None, headers)
    response = connection.getresponse()
    data = response.read()
    assert response.status == expected, (response.status, data)
    return response, json.loads(data) if data else None


call("GET", "/livez")
call("GET", "/readyz")
call("GET", "/api/tasks", expected=401)
response, data = call("POST", "/api/login", {"username": "learner", "password": os.environ["LEARNING_PASSWORD"]})
cookie = response.getheader("Set-Cookie").split(";", 1)[0]
response, created = call("POST", "/api/tasks", {"title": "CI 实际数据库读写验收"}, cookie, 201)
response, tasks = call("GET", "/api/tasks", cookie=cookie)
assert any(task["id"] == created["id"] for task in tasks)
response, changed = call("PUT", f'/api/tasks/{created["id"]}', {"title": "CI 验收完成", "done": True}, cookie)
assert changed["done"] is True
call("DELETE", f'/api/tasks/{created["id"]}', cookie=cookie, expected=204)
response, tasks = call("GET", "/api/tasks", cookie=cookie)
assert all(task["id"] != created["id"] for task in tasks)
print("真实 HTTP 登录、权限检查和 PostgreSQL CRUD 验收通过")
