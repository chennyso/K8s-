import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="读取并核对之前计算任务保存的结果")
parser.add_argument("--input-dir", type=Path, required=True)
args = parser.parse_args()
files = sorted(args.input_dir.glob("*.json"))
if not files:
    raise FileNotFoundError(f"没有找到计算结果：{args.input_dir}")
for path in files:
    value = json.loads(path.read_text())
    expected = value["count"] * (value["count"] + 1) // 2
    if value["total"] != expected:
        raise ValueError(f"计算结果核对失败：{path}")
    print(json.dumps({"file": path.name, "result": value, "verified": True}, ensure_ascii=False), flush=True)
