import hashlib
import html
import json
from pathlib import Path

import markdown
from bs4 import BeautifulSoup

root = Path(__file__).resolve().parent
names = ["Kubernetes入门到项目学习教程", "从零搭建Kubernetes与项目实战", "204节点RKE2集群搭建流程", "204集群监控部署与使用文档", "Pod项目实操学习手册", "Kubernetes平台部署与学习流程", "项目验收与学习任务"]
sections = []
links = []
manifest = {}
for number, name in enumerate(names, 1):
    source = (root / "docs" / (name + ".md")).read_text()
    manifest[name] = hashlib.sha256(source.encode()).hexdigest()
    renderer = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])
    soup = BeautifulSoup(renderer.convert(source), "html.parser")
    mapping = {}
    for heading in soup.select("h1,h2,h3,h4"):
        previous = heading.get("id")
        current = f"chapter-{number}-{len(mapping)}"
        if previous:
            mapping[previous] = current
        heading["id"] = current
    for anchor in soup.select('a[href^="#"]'):
        target = anchor["href"][1:]
        if target in mapping:
            anchor["href"] = "#" + mapping[target]
    for code in soup.select("code.language-mermaid"):
        diagram = soup.new_tag("pre", attrs={"class": "mermaid"})
        diagram.string = code.get_text()
        code.parent.replace_with(diagram)
    sections.append(f'<section id="chapter-{number}" class="chapter">{soup}</section>')
    links.append(f'<a href="#chapter-{number}">{number:02d} {html.escape(name)}</a>')
template = (root / "tutorial-template.html").read_text()
result = template.replace("{{NAVIGATION}}", "\n".join(links)).replace("{{CONTENT}}", "\n".join(sections))
assert "{{" not in result
(root / "index.html").write_text(result)
(root / "source-hashes.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
print(f"已生成 {len(names)} 篇教程，{len(result)} 个字符")
