# 204 Kubernetes 学习项目

[打开 HTML 教程](index.html)

## 公开内容与复现准备

本目录包含学习文档、应用源码、部署配置和实验脚本。私有地址用于解释实验拓扑，执行前需要调整为自己的网络。应用是隔离实验环境中的学习项目；外部访问需要自行配置 HTTPS、访问限制和凭据管理。故障脚本会修改资源，只能在专用实验环境执行。

实际 SSH 公钥、接入配置、密码、令牌、CA 私钥、kubeconfig、运行日志和业务数据保存在私有环境。首次使用时复制 `rke2-lab/user-data.example` 为 `user-data`，在 `ssh_authorized_keys` 中填写自己生成的公钥；复制 `interview/ssh-config.example` 为 `ssh-config`，配置自己获得授权的接入方式。RKE2 加入令牌和其他认证信息按教程在自己的环境生成。

公开目录通过 requirements 文件和镜像清单声明依赖。Dockerfile 使用的 wheels 目录需要依照平台文档准备 Python 3.13、linux/amd64 的依赖；Helm chart 需要取得文档指定版本，Helm 客户端按照当前电脑架构安装。完整私有环境的离线依赖包单独保存。

在 Python 3.13 的 linux/amd64 环境中进入 `interview/app/`，执行 `python -m pip download -r requirements.txt -d wheels` 准备 Dockerfile 使用的依赖。构建前检查每个二进制依赖的架构与目标容器相符。

教程正文、代码和表格可直接打开 HTML 阅读。Mermaid 图解使用固定版本的 CDN 脚本，绘制图解需要联网；图解源代码保留在 Markdown 和 HTML 中。

重新生成教程：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-docs.txt
python build_tutorial.py
```

## 教程入口

1. `docs/从零搭建Kubernetes与项目实战.md`：按操作位置、依赖和顺序执行。
2. `docs/204节点RKE2集群搭建流程.md`：虚拟机、cloud-init、网络、RKE2 安装和集群验收。
3. `docs/204集群监控部署与使用文档.md`：Prometheus、Grafana、Alertmanager 和持久化。
4. `docs/Pod项目实操学习手册.md`：进程、探针、网络、权限、存储和故障定位。
5. `docs/Kubernetes平台部署与学习流程.md`：任务系统、存储、TLS、日志、CI、GitOps 和备份。
6. `docs/项目验收与学习任务.md`：实际验收结果和自主学习任务。

## 源码目录

- `rke2-lab/`：四台虚拟机与 RKE2 配置和安装脚本。
- `monitoring/`：监控 chart、values、持久卷、指标端点与验收脚本。
- `pod-lab/`：可以直接执行的 Pod 实验与故障清单。
- `interview/app/`：任务系统源码、Dockerfile、离线依赖、CI 和 GitOps 配置。
- `interview/k8s/`：应用、证书、存储、Runner、备份、恢复和负载清单。
- `interview/host/`：94 宿主机服务、镜像导入和节点仓库信任。
- `interview/charts/`：Helm values。
- `build_tutorial.py`：通过 Python-Markdown 生成 HTML 教程。
- `requirements-docs.txt`：教程生成所需依赖。

## 执行前设置

安装 Helm 3.19.0 和 kubectl，再按照教程建立自己的 SSH 转发、取回 kubeconfig，设置 `KUBECONFIG`。Python 工具依赖在 `interview/requirements-tools.txt`。

首次安装会创建资源；当前集群的学习练习以教程中的查看、业务请求和指定故障演练为入口。安装目录、命名空间、节点和端口均已在教程中明确标注。

当前环境私有凭据单独交付。源码包包含认证文件的生成方法，密码、Token、私钥和管理员 kubeconfig 保存在用户自己的私有目录。
