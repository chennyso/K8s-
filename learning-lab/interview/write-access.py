import argparse
import base64
import json
import pathlib

root = pathlib.Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--output", type=pathlib.Path, default=root / "secrets/access.txt")
args = parser.parse_args()
values = json.loads((root / "secrets/platform.json").read_text())
argo = json.loads((root / "secrets/argocd-admin.json").read_text())
grafana = json.loads((root / "secrets/grafana-admin.json").read_text())
text = f'''204 实验环境私有访问凭据
本文件包含密码，请仅在自己的设备保存。

任务系统：http://127.0.0.1:18083
账号：learner
密码：{values["admin"]}

Pod 学习页面：http://127.0.0.1:18084

Grafana：http://127.0.0.1:3000
账号：admin
密码：{base64.b64decode(grafana["data"]["admin-password"]).decode()}

Argo CD：http://127.0.0.1:18085
账号：admin
密码：{base64.b64decode(argo["data"]["password"]).decode()}

GitLab：http://127.0.0.1:18080
账号：root
密码：{values["gitlabpassword"]}

Prometheus：http://127.0.0.1:9090
Alertmanager：http://127.0.0.1:9093

页面依赖 NetBird、SSH 和端口转发保持连接。
'''
output = args.output
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(text)
output.chmod(0o600)
print("私有访问凭据文件已生成")
