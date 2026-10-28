import json
import os
import pathlib
import subprocess
import time

root = pathlib.Path(__file__).resolve().parent
values = json.loads((root / "secrets/platform.json").read_text())
k = ["kubectl", "--kubeconfig", os.environ["KUBECONFIG"]]


def run(args):
    subprocess.run(k + args, check=True)


def phase(kind, name, expected, seconds=600):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        resource = json.loads(subprocess.check_output(k + ["-n", "velero", "get", kind, name, "-o", "json"]))
        state = resource.get("status", {}).get("phase")
        if state == expected:
            print(kind, name, state, flush=True)
            return
        if state in {"Failed", "PartiallyFailed", "FailedValidation"}:
            raise RuntimeError(json.dumps(resource["status"]))
        time.sleep(5)
    raise RuntimeError("备份恢复等待超时")


run(["apply", "-f", str(root / "k8s/database-backup.yaml")])
run(["-n", "backup-lab", "create", "secret", "generic", "database-password", "--from-literal=password=" + values["database"]])
run(["-n", "backup-lab", "create", "job", "database-backup-initial", "--from=cronjob/database-backup"])
run(["-n", "backup-lab", "wait", "--for=condition=Complete", "job/database-backup-initial", "--timeout=180s"])
run(["-n", "backup-lab", "wait", "--for=condition=Ready", "pod/dump-reader", "--timeout=180s"])
source = subprocess.check_output(k + ["-n", "backup-lab", "exec", "dump-reader", "--", "sha256sum", "/backup/learning.dump"], text=True).split()[0]
run(["apply", "-f", str(root / "k8s/backup-test.yaml")])
phase("backup", "learning-drill", "Completed")
run(["apply", "-f", str(root / "k8s/restore-test.yaml")])
phase("restore", "learning-drill-restore", "Completed")
run(["-n", "backup-restored", "wait", "--for=condition=Ready", "pod/dump-reader", "--timeout=180s"])
target = subprocess.check_output(k + ["-n", "backup-restored", "exec", "dump-reader", "--", "sha256sum", "/backup/learning.dump"], text=True).split()[0]
assert source == target
source_pv = subprocess.check_output(k + ["-n", "backup-lab", "get", "pvc", "database-dumps", "-o", "jsonpath={.spec.volumeName}"], text=True)
target_pv = subprocess.check_output(k + ["-n", "backup-restored", "get", "pvc", "database-dumps", "-o", "jsonpath={.spec.volumeName}"], text=True)
assert source_pv != target_pv
print("备份文件 SHA256 一致，恢复使用不同 PV", source_pv, target_pv, flush=True)
run(["apply", "-f", str(root / "k8s/restore-database.yaml")])
run(["-n", "backup-restored", "rollout", "status", "deployment/restored-postgres", "--timeout=180s"])
pod = subprocess.check_output(k + ["-n", "backup-restored", "get", "pod", "-l", "app=restored-postgres", "-o", "jsonpath={.items[0].metadata.name}"], text=True)
run(["-n", "backup-restored", "exec", pod, "--", "pg_restore", "-U", "learning", "-d", "learning", "/backup/learning.dump"])
count = subprocess.check_output(k + ["-n", "backup-restored", "exec", pod, "--", "psql", "-U", "learning", "-d", "learning", "-Atc", "SELECT count(*) FROM tasks WHERE title='持久化恢复验收记录'"], text=True).strip()
assert int(count) >= 1
print("全新 PostgreSQL 数据卷恢复业务记录成功，记录数量", count, flush=True)
