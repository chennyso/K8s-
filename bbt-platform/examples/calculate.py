import argparse
import json
import os
import socket
from pathlib import Path

parser = argparse.ArgumentParser(description="计算连续整数之和并保存结果")
parser.add_argument("--count", type=int, default=1000000)
parser.add_argument("--output-dir", type=Path, required=True)
args = parser.parse_args()
if args.count < 1:
    parser.error("count 必须大于零")

total = sum(range(1, args.count + 1))
hostname = socket.gethostname()
result = {"count": args.count, "total": total, "hostname": hostname}
args.output_dir.mkdir(parents=True, exist_ok=True)
destination = args.output_dir / f"{hostname}.json"
partial = destination.with_suffix(".partial")
with partial.open("w") as stream:
    json.dump(result, stream, ensure_ascii=False)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
os.replace(partial, destination)
print(json.dumps(result, ensure_ascii=False), flush=True)
