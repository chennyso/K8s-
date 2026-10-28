import json
import os
import re
from pathlib import Path

metadata = json.loads(Path("build-metadata.json").read_text())
report = json.loads(Path("test-report.json").read_text())
digest = metadata["containerimage.digest"]
if re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
    raise ValueError("构建结果没有有效的镜像 digest")
if report["passed"] is not True or report["commit"] != os.environ["CI_COMMIT_SHA"]:
    raise ValueError("测试结果与构建提交不一致")
release = {"source_commit": os.environ["CI_COMMIT_SHA"], "image_repository": os.environ["CI_REGISTRY_IMAGE"], "image_digest": digest, "pipeline_url": os.environ["CI_PIPELINE_URL"], "candidate_verified": True}
Path("release.json").write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n")
print("已生成待审核发布记录 release.json")
