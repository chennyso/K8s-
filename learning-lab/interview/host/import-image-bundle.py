import argparse
import json
import pathlib
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("archive")
parser.add_argument("folder")
parser.add_argument("--host-only", action="store_true")
args = parser.parse_args()
root = pathlib.Path("/var/lib/interview-lab")
archive = root / args.archive
folder = root / args.folder
subprocess.run(["tar", "-xzf", str(archive), "-C", str(root)], check=True)
images = json.loads((folder / "images.json").read_text())
for index, image in enumerate(images):
    image_file = folder / f"{index:03d}.tar"
    subprocess.run(["docker", "load", "-i", str(image_file)], check=True)
normalized = root / (folder.name + "-normalized.tar.gz")
with normalized.open("wb") as output:
    save = subprocess.Popen(["docker", "save", *images], stdout=subprocess.PIPE)
    subprocess.run(["gzip", "-1"], stdin=save.stdout, stdout=output, check=True)
    save.stdout.close()
    if save.wait() != 0:
        raise RuntimeError("单平台镜像导出失败")
if not args.host_only:
    subprocess.run(["bash", str(root / "host/import-platform-images.sh"), normalized.name], check=True)
