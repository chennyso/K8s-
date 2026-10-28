import argparse
import json
import os
import pathlib
import subprocess

root = pathlib.Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--inventory", type=pathlib.Path, default=root / "platform-images.json")
parser.add_argument("--name", default="platform")
args = parser.parse_args()
folder = root / ("image-bundle-" + args.name)
folder.mkdir(exist_ok=True)
images = json.loads(args.inventory.read_text())
assert images and all(isinstance(image, str) for image in images)
for index, image in enumerate(images):
    target = folder / f"{index:03d}.tar"
    if target.exists():
        target.unlink()
    print("下载并校验 linux/amd64 镜像", image, flush=True)
    reference = image.split("@")[0]
    subprocess.run(["skopeo", "copy", "--override-os", "linux", "--override-arch", "amd64", "docker://" + image, "docker-archive:" + str(target) + ":" + reference], check=True)
(folder / "images.json").write_text(json.dumps([image.split("@")[0] for image in images], indent=2))
archive = root / (folder.name + ".tar.gz")
subprocess.run(["tar", "--no-xattrs", "--no-acls", "-czf", str(archive), "-C", str(root), folder.name], env={**os.environ, "COPYFILE_DISABLE": "1"}, check=True)
print("标准单平台镜像包", archive, flush=True)
