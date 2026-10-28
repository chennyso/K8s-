import hashlib
import hmac
import os
import secrets
import time
from pathlib import Path

import psycopg
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field

app = FastAPI(title="204 Kubernetes 学习任务系统")
requests = Counter("learning_http_requests_total", "HTTP requests", ["method", "status"])
dsn = os.environ["DATABASE_URL"]


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class Task(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    done: bool = False


@app.middleware("http")
async def measure(request: Request, call_next):
    started = time.monotonic()
    response = await call_next(request)
    requests.labels(request.method, str(response.status_code)).inc()
    print({"path": request.url.path, "method": request.method, "status": response.status_code, "seconds": round(time.monotonic()-started, 4), "pod": os.environ.get("HOSTNAME")}, flush=True)
    response.headers["X-Pod-Name"] = os.environ.get("HOSTNAME", "local")
    return response


@app.on_event("startup")
def initialize():
    salt = os.environ["ADMIN_SALT"]
    digest = hashlib.pbkdf2_hmac("sha256", os.environ["ADMIN_PASSWORD"].encode(), salt.encode(), 200000).hex()
    with psycopg.connect(dsn) as db:
        db.execute("SELECT pg_advisory_xact_lock(204001)")
        db.execute("CREATE TABLE IF NOT EXISTS users (username text PRIMARY KEY, salt text NOT NULL, digest text NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS sessions (token text PRIMARY KEY, username text REFERENCES users(username), expires timestamptz NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS tasks (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, title text NOT NULL, done boolean NOT NULL DEFAULT false, username text REFERENCES users(username))")
        db.execute("INSERT INTO users VALUES (%s,%s,%s) ON CONFLICT DO NOTHING", ("learner", salt, digest))


def user(request):
    token = request.cookies.get("session")
    with psycopg.connect(dsn) as db:
        row = db.execute("SELECT username FROM sessions WHERE token=%s AND expires>now()", (token,)).fetchone()
    if row is None:
        raise HTTPException(401, "请先登录")
    return row[0]


@app.get("/")
def index():
    return FileResponse(Path(__file__).with_name("index.html"))


@app.get("/livez")
def live():
    return {"status": "alive"}


@app.get("/readyz")
def ready():
    with psycopg.connect(dsn, connect_timeout=2) as db:
        db.execute("SELECT 1")
    return {"status": "ready"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/login")
def login(body: Login, response: Response):
    with psycopg.connect(dsn) as db:
        row = db.execute("SELECT salt,digest FROM users WHERE username=%s", (body.username,)).fetchone()
        if row is None:
            raise HTTPException(401, "账号或密码错误")
        digest = hashlib.pbkdf2_hmac("sha256", body.password.encode(), row[0].encode(), 200000).hex()
        if not hmac.compare_digest(digest, row[1]):
            raise HTTPException(401, "账号或密码错误")
        token = secrets.token_urlsafe(32)
        db.execute("INSERT INTO sessions VALUES (%s,%s,now()+interval '8 hours')", (token, body.username))
    response.set_cookie("session", token, httponly=True, samesite="strict", max_age=28800)
    return {"username": body.username}


@app.get("/api/tasks")
def tasks(request: Request):
    username = user(request)
    with psycopg.connect(dsn) as db:
        rows = db.execute("SELECT id,title,done FROM tasks WHERE username=%s ORDER BY id", (username,)).fetchall()
    return [{"id": row[0], "title": row[1], "done": row[2]} for row in rows]


@app.post("/api/tasks", status_code=201)
def create(body: Task, request: Request):
    username = user(request)
    with psycopg.connect(dsn) as db:
        row = db.execute("INSERT INTO tasks(title,done,username) VALUES(%s,%s,%s) RETURNING id", (body.title, body.done, username)).fetchone()
    return {"id": row[0], **body.model_dump()}


@app.put("/api/tasks/{task_id}")
def update(task_id: int, body: Task, request: Request):
    username = user(request)
    with psycopg.connect(dsn) as db:
        row = db.execute("UPDATE tasks SET title=%s,done=%s WHERE id=%s AND username=%s RETURNING id", (body.title, body.done, task_id, username)).fetchone()
    if row is None:
        raise HTTPException(404, "任务不存在")
    return {"id": row[0], **body.model_dump()}


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete(task_id: int, request: Request):
    username = user(request)
    with psycopg.connect(dsn) as db:
        row = db.execute("DELETE FROM tasks WHERE id=%s AND username=%s RETURNING id", (task_id, username)).fetchone()
    if row is None:
        raise HTTPException(404, "任务不存在")
    return Response(status_code=204)
