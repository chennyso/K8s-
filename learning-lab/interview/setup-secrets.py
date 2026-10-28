import json
import os
import pathlib
import secrets
import subprocess

import bcrypt

root = pathlib.Path(__file__).resolve().parent
folder = root / "secrets"
folder.mkdir(exist_ok=True)
path = folder / "platform.json"
if path.exists():
    values = json.loads(path.read_text())
else:
    values = {name: secrets.token_urlsafe(24) for name in ["database", "admin", "salt", "registry", "s3key", "s3secret", "gitlabtoken", "gitlabpassword"]}
if "gitlabpassword" not in values:
    values["gitlabpassword"] = os.environ["GITLAB_ROOT_PASSWORD"]
path.write_text(json.dumps(values))
path.chmod(0o600)
(folder / "gitlab.env").write_text("GITLAB_ROOT_PASSWORD=" + values["gitlabpassword"] + "\n")
(folder / "htpasswd").write_text("learning:" + bcrypt.hashpw(values["registry"].encode(), bcrypt.gensalt()).decode() + "\n")
(folder / "s3.json").write_text(json.dumps({"identities": [{"name": "velero", "credentials": [{"accessKey": values["s3key"], "secretKey": values["s3secret"]}], "actions": ["Admin", "Read", "Write", "List", "Tagging"]}]}))
(folder / "cloud").write_text(f'[default]\naws_access_key_id={values["s3key"]}\naws_secret_access_key={values["s3secret"]}\n')
app = {"POSTGRES_PASSWORD": values["database"], "DATABASE_URL": f'postgresql://learning:{values["database"]}@postgres:5432/learning', "ADMIN_PASSWORD": values["admin"], "ADMIN_SALT": values["salt"]}
(folder / "application.env").write_text("".join(f"{key}={value}\n" for key,value in app.items()))
for entry in folder.iterdir():
    if entry.is_file():
        entry.chmod(0o600)
print("平台认证文件已生成")
