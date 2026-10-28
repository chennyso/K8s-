import json
import os
import secrets
from pathlib import Path

folder = Path("private")
folder.mkdir(mode=0o700)
os.chmod(folder, 0o700)
values = {key: secrets.token_urlsafe(32) for key in ["redis", "s3_access", "s3_secret", "mariadb", "mariadb_root", "grafana", "keycloak_db", "keycloak_admin"]}
files = {
    "backend.env": f'REDIS_PASSWORD={values["redis"]}\n',
    "grafana-password": values["grafana"],
    "identity.env": f'KEYCLOAK_DB_PASSWORD={values["keycloak_db"]}\nKEYCLOAK_ADMIN_PASSWORD={values["keycloak_admin"]}\n',
    "s3.json": json.dumps({"identities": [{"name": "juicefs", "credentials": [{"accessKey": values["s3_access"], "secretKey": values["s3_secret"]}], "actions": ["Admin", "Read", "Write", "List", "Tagging"]}]}),
    "s3-client.json": json.dumps({"endpoint": "http://storage.bbt.example.com:8333", "access": values["s3_access"], "secret": values["s3_secret"]}),
    "juicefs-secret.json": json.dumps({"apiVersion": "v1", "kind": "Secret", "metadata": {"name": "juicefs-backend", "namespace": "kube-system"}, "type": "Opaque", "stringData": {"name": "bbt-learning", "metaurl": f'redis://:{values["redis"]}@storage.bbt.example.com:6379/1', "storage": "s3", "bucket": "http://storage.bbt.example.com:8333/bbt-juicefs", "access-key": values["s3_access"], "secret-key": values["s3_secret"]}}),
    "mariadb-secret.json": json.dumps({"apiVersion": "v1", "kind": "Secret", "metadata": {"name": "mariadb-password", "namespace": "slurm"}, "type": "Opaque", "stringData": {"password": values["mariadb"], "root-password": values["mariadb_root"]}}),
}
for name, content in files.items():
    descriptor = os.open(folder / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(content + "\n")
print("已生成私有配置目录；通过受保护的连接分发这些文件，不要上传仓库")
