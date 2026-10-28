# 从零搭建 Kubernetes 与项目实战

学习概念、理解 YAML 和逐项练习时，先阅读同目录《Kubernetes入门到项目学习教程.md》。该教程参考《K8s 详细入门教程（基于 Docker 背景）》的讲解顺序，结合本环境解释资源关系、操作结果及排查方法。本文件提供从虚拟机到项目部署的执行顺序，配套专题文档提供具体配置和实验细节。

## 01：准备终端、网络和安装目录

操作位置：Mac。需要 NetBird、SSH、kubectl、Docker、Python 3.11 及以上版本。镜像分发工具使用 Skopeo。解压部署源码包后，目录包括 `rke2-lab/`、`monitoring/`、`pod-lab/`、`interview/`。`tools/helm` 为本次使用的 Helm 3.19.0，适用于当前 Mac 的 arm64 架构。

在源码包根目录执行：

```bash
export PATH="$PWD/tools:$PATH"
helm version --short
```

先按《204节点RKE2集群搭建流程》建立 SOCKS 和跳板连接。SSH 密码在终端交互输入。操作之前确认当前主机：

```bash
hostname
whoami
pwd
```

操作位置分工：

| 位置 | 执行的工作 |
|---|---|
| Mac | 准备源码、下载 amd64 镜像、限速传输、打开学习页面 |
| 91 跳板机 | 连接 94，转发 SSH 和管理页面连接 |
| 94 宿主机 | 创建虚拟机、管理 libvirt、运行 NFS 和独立基础服务 |
| server-1 | 管理 Kubernetes，执行 kubectl 与 Helm |
| Pod 容器 | 查看业务进程、日志、网络与数据库状态 |

命令中 `192.168.204.1` 表示 94 宿主机的虚拟网桥地址。浏览器的 `127.0.0.1` 表示当前 Mac，二者通过转发连接起来。

## 02：创建 Ubuntu 虚拟机

按《204节点RKE2集群搭建流程》的顺序完成宿主机依赖、Ubuntu 镜像校验、SSH 密钥、cloud-init 和四台虚拟机创建。源码中的 `rke2-lab/network.xml`、`user-data`、`provision.sh` 和四份 meta-data 是实际使用的配置。

在 94 宿主机验证：

```bash
virsh list --all
virsh net-dhcp-leases rke2-lab
virsh dominfo rke2-server-1
ssh -i /var/lib/rke2-lab/id_ed25519 ubuntu@192.168.204.11 hostname
```

需要理解的原理：libvirt 创建网桥和 NAT 网络；DHCP 根据固定 MAC 分配地址；cloud-init 首次启动时配置用户和 SSH 公钥；qcow2 提供虚拟磁盘文件。虚拟机的 4 GiB 内存是节点容量，Pod requests 和 limits 在这个容量范围内发挥作用。

## 03：安装 RKE2 并验证集群网络

同一版本的 RKE2 二进制、镜像包和校验文件必须配套使用。先安装 server，再让 agent 使用加入令牌访问 server 的 9345 端口。

在 server-1 执行：

```bash
sudo -i
export PATH=/var/lib/rancher/rke2/bin:$PATH
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml
kubectl get --raw='/readyz?verbose'
kubectl get nodes -o wide
kubectl get pods -A
kubectl top nodes
```

四个节点均应为 Ready。随后执行源码中的网络验收脚本，检查 DNS、Service 和跨节点 Pod 访问。现有 `cluster-validation` 命名空间保留网络测试工作负载。

需要理解的原理：API Server 接收资源请求；etcd 保存集群状态；scheduler 为未调度 Pod 选择节点；kubelet 管理容器；containerd 运行容器；Canal 提供 Pod 网络和网络策略；CoreDNS 解析 Service 名称；Service 与 EndpointSlice 关联后端 Pod。

Mac 进入源码包的 `interview/`，在一个独立终端保持以下转发连接运行。执行前确认这些本机端口没有被其他转发进程占用：

```bash
ssh -F ssh-config -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:16443:127.0.0.1:16443 \
  -L 127.0.0.1:18080:127.0.0.1:38080 \
  -L 127.0.0.1:18333:127.0.0.1:38333 \
  -L 127.0.0.1:18443:127.0.0.1:38443 \
  lab-91 \
  'ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:16443:192.168.204.11:6443 -L 127.0.0.1:38080:192.168.204.1:18080 -L 127.0.0.1:38333:192.168.204.1:18333 -L 127.0.0.1:38443:192.168.204.12:443 root@10.100.1.94'
```

Mac 的另一个终端在 `interview/` 执行，安全地取回 kubeconfig：

```bash
mkdir -p secrets
chmod 700 secrets
ssh -F ssh-config lab-91 \
  'ssh root@10.100.1.94 "ssh -i /var/lib/rke2-lab/id_ed25519 ubuntu@192.168.204.11 sudo cat /etc/rancher/rke2/rke2.yaml"' \
  > secrets/kubeconfig
chmod 600 secrets/kubeconfig
nano secrets/kubeconfig
```

使用编辑器把 kubeconfig 的 `server` 修改为 `https://127.0.0.1:16443`，保存后执行：

```bash
export KUBECONFIG="$PWD/secrets/kubeconfig"
kubectl get nodes
```

后续 Mac 终端中的 kubectl、Helm 和 Python 验收脚本都使用这个 KUBECONFIG。

## 04：建立监控和基础检查习惯

按《204集群监控部署与使用文档》安装 kube-prometheus-stack、持久卷和管理入口。每次完成一项部署，都执行以下检查：

```bash
kubectl get pods -A
kubectl get events -A --sort-by=.lastTimestamp
kubectl top nodes
kubectl get pvc -A
```

Grafana 查看资源变化，Prometheus 查看采集目标和指标，Alertmanager 查看告警分组与处理状态。节点指标、Kubernetes 对象状态、应用指标分别来自 node-exporter、kube-state-metrics 和应用 `/metrics`。

## 05：运行 Pod 进程实验

进入 `pod-lab/`，设置管理员 kubeconfig 后执行：

```bash
bash deploy.sh
kubectl apply -f notebook.yaml
bash verify.sh
bash fault-drills.sh
```

Local PV 需要在 worker-3 上预先创建 `/var/lib/pod-lab/notebook`，所有者为 1000:1000，权限为 2770。`notebook.yaml` 明确设置了该节点的亲和性。

按照《Pod项目实操学习手册》完成十组实验。自动验收会产生真实进程退出、探针失败、Pod 重建和调度故障；脚本结束时会恢复副本数量并清理故障 Pod。

## 06：安装存储、证书、发布和日志组件

操作位置：Mac，已经通过 SSH 转发连接集群 API。进入 `interview/`。源码包包含固定版本的 chart 和对应 values。

先把宿主机安装脚本复制到 94：

```bash
ssh -F ssh-config lab-91 \
  'mkdir -p /var/lib/interview-lab/host; ssh root@10.100.1.94 mkdir -p /var/lib/interview-lab/host'
rsync -a --bwlimit=1024 -e 'ssh -F ssh-config' \
  host/ lab-91:/var/lib/interview-lab/host/
ssh -F ssh-config lab-91 \
  'rsync -a /var/lib/interview-lab/host/ root@10.100.1.94:/var/lib/interview-lab/host/'
```

先在 94 宿主机准备存储目录：

```bash
cd /var/lib/interview-lab
bash host/setup-nfs.sh
bash host/prepare-loki-storage.sh
```

回到 Mac，先创建 Loki 的 Local PV，再安装 Helm 组件：

```bash
kubectl apply -f k8s/loki-storage.yaml
helm upgrade --install nfs csi-driver-nfs-4.13.6.tgz \
  -n kube-system -f charts/nfs.yaml
helm upgrade --install cert-manager cert-manager-1.21.3.tgz \
  -n cert-manager --create-namespace -f charts/cert-manager.yaml
helm upgrade --install argocd argo-cd-10.11.6.tgz \
  -n argocd --create-namespace -f charts/argocd.yaml
helm upgrade --install loki loki-7.5.0.tgz \
  -n logging --create-namespace -f charts/loki.yaml
helm upgrade --install alloy alloy-1.14.3.tgz \
  -n logging -f charts/alloy.yaml
kubectl apply -f k8s/loki-datasource.yaml
```

NFS CSI 之前需要先在 94 宿主机运行 `host/setup-nfs.sh` 并确认导出目录。证书组件部署后检查 webhook、cainjector 和 controller。Argo CD 需要 controller、repo-server、server、Redis 等组件完成启动。

```bash
kubectl -n kube-system get pods -l app.kubernetes.io/instance=nfs
kubectl -n cert-manager get pods
kubectl -n argocd get pods
kubectl -n logging get pods,pvc
kubectl get storageclass
```

镜像下载失败时先查看 Pod 事件。实验所用镜像均为 linux/amd64。源码中的镜像分发工具使用标准单平台归档；在 94 导入镜像后，再分发到四个节点的 containerd。归档传输使用 rsync 的 `--bwlimit`，例如 `--bwlimit=1024` 将单个传输限制到约 1 MiB/s。

Mac 在 `interview/` 中准备平台镜像：

```bash
python3 prepare-images.py --inventory platform-images.json --name platform
rsync -a --partial --bwlimit=1024 -e 'ssh -F ssh-config' \
  image-bundle-platform.tar.gz lab-91:/var/lib/interview-lab/
```

在 91 执行：

```bash
scp /var/lib/interview-lab/image-bundle-platform.tar.gz \
  root@10.100.1.94:/var/lib/interview-lab/
ssh root@10.100.1.94 \
  python3 /var/lib/interview-lab/host/import-image-bundle.py \
  image-bundle-platform.tar.gz image-bundle-platform
```

CI 镜像使用 `ci-images.json` 和 `--name ci`，导入方法相同。宿主机服务镜像使用 `host-images.json` 和 `--name host`，在 94 导入时增加 `--host-only`；这些大型宿主机服务镜像保留在宿主机。

## 07：运行宿主机基础服务和任务系统

在 94 宿主机 `/var/lib/interview-lab` 下准备 `host/`、独立认证文件和服务镜像归档。`host/start-services.sh` 创建实验 CA、TLS 仓库及 SeaweedFS。`host/configure-registry.py` 配置节点对仓库 CA 的信任。`host/install-gitlab.sh` 启动独立 GitLab。

生成认证文件前，需要 Python 工具依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-tools.txt
python setup-secrets.py
```

随机密码和 Token 保存在 `secrets/`，保持文件权限 0600。将 `host/` 和 `secrets/` 经 SSH 复制到 94 的 `/var/lib/interview-lab`。CA 创建完成后，将宿主机的 `certs/ca.crt` 和 `certs/ca.key` 经 SSH 取回 Mac 的 `interview/secrets/`，分别用于信任配置和 cert-manager 签发；CA 私钥不进入源码仓库。

Mac 复制认证文件：

```bash
ssh -F ssh-config lab-91 \
  'mkdir -p /var/lib/interview-lab/secrets; ssh root@10.100.1.94 mkdir -p /var/lib/interview-lab/secrets'
rsync -a --bwlimit=1024 -e 'ssh -F ssh-config' \
  secrets/ lab-91:/var/lib/interview-lab/secrets/
ssh -F ssh-config lab-91 \
  'rsync -a /var/lib/interview-lab/secrets/ root@10.100.1.94:/var/lib/interview-lab/secrets/'
```

在 94 使用宿主机镜像包启动基础服务：

```bash
cd /var/lib/interview-lab
python3 host/import-image-bundle.py \
  image-bundle-host.tar.gz image-bundle-host --host-only
bash host/start-services.sh image-bundle-host-normalized.tar.gz
python3 host/configure-registry.py
bash host/install-gitlab.sh image-bundle-host-normalized.tar.gz
bash host/push-base.sh
bash host/push-buildkit.sh
```

私有仓库登录在 `configure-registry.py` 中完成。通过 `create-bucket.py` 验证 S3 创建、写入和读取。GitLab 首次初始化结束后，在 94 执行 `python3 host/bootstrap-gitlab.py` 创建实验 API Token。

Mac 取回本实验 CA，然后执行 S3 校验：

```bash
ssh -F ssh-config lab-91 \
  'scp root@10.100.1.94:/var/lib/interview-lab/certs/ca.crt root@10.100.1.94:/var/lib/interview-lab/certs/ca.key /var/lib/interview-lab/'
scp -F ssh-config lab-91:/var/lib/interview-lab/ca.crt \
  lab-91:/var/lib/interview-lab/ca.key secrets/
chmod 600 secrets/ca.key
python create-bucket.py
```

应用源码在 `app/`。Dockerfile 从内部 Python 基础镜像构建，依赖文件保存在 wheels 目录，应用默认使用非 root 用户运行。

Mac 先把应用源码复制到 94：

```bash
ssh -F ssh-config lab-91 \
  'mkdir -p /var/lib/interview-lab/app; ssh root@10.100.1.94 mkdir -p /var/lib/interview-lab/app'
rsync -a --bwlimit=1024 -e 'ssh -F ssh-config' \
  app/ lab-91:/var/lib/interview-lab/app/
ssh -F ssh-config lab-91 \
  'rsync -a /var/lib/interview-lab/app/ root@10.100.1.94:/var/lib/interview-lab/app/'
```

在 94 构建和推送初始应用镜像：

```bash
cd /var/lib/interview-lab
docker build --platform linux/amd64 -t interview-tasks:1.0.0 app
docker tag interview-tasks:1.0.0 \
  192.168.204.1:15000/learning/tasks:1.0.0
docker push 192.168.204.1:15000/learning/tasks:1.0.0
```

回到 Mac 的 `interview/` 执行部署：

```bash
python deploy-application.py
kubectl apply -f k8s/alerts.yaml
```

94 宿主机已经通过前面的步骤配置仓库 CA 和登录认证。Mac 通过 Kubernetes API 创建应用 Secret、数据库、Deployment、Service、HPA、PDB、指标采集和 Ingress。

验证数据库 PVC 绑定、PostgreSQL Ready、tasks 两副本 Ready、Certificate Ready，再打开任务系统页面。详细原理和接口见《Kubernetes平台部署与学习流程》。

## 08：连接 GitLab CI 和 Argo CD

GitLab 初始化完成后，创建私有项目和 Runner。`setup-gitlab.py` 创建项目、项目 Runner、CI 变量和 Argo CD 仓库认证。执行之前，GitLab 的 API Token 应已经通过宿主机 `host/bootstrap-gitlab.py` 创建。

```bash
python setup-gitlab.py
kubectl -n ci get pods
kubectl -n ci logs deployment/gitlab-runner -c register
python push-source.py
```

在 GitLab 查看 integration 和 build 两个 Job。integration 针对已经运行的任务系统执行真实数据库操作；build 使用 rootless BuildKit 构建并推送镜像。流水线通过后连接 Argo CD：

```bash
kubectl apply -f k8s/argocd-application.yaml
kubectl -n argocd get application learning-tasks
kubectl -n interview-app rollout status deployment/tasks --timeout=180s
```

需要理解的原理：GitLab 保存源码和流水线；Runner 创建 CI Pod；BuildKit 构建镜像；Registry 保存镜像；Git 保存期望的部署配置；Argo CD 将期望配置同步到 Kubernetes。应用业务数据保存在数据库 PVC。

## 09：执行真实负载和故障演练

首先运行 `verify-application.py`，生成用于后续恢复验证的真实业务记录。然后按顺序执行：

1. `release-drill.sh`：验证错误镜像发布时旧副本继续可用，修正配置后恢复。
2. `application-drills.py`：停止数据库，验证 readiness 和实际告警，恢复数据库并检查原有数据，删除应用 Pod 后检查自动重建。
3. 登录负载 Job：通过集群 Service 发出真实请求，观察 HPA 扩容和负载结束后的缩容。
4. PDB 与驱逐：观察可用副本约束和节点恢复调度过程。

这些演练在实验命名空间执行。每次演练后检查 Pods、Deployment、EndpointSlice、HPA、告警状态和真实 HTTP 请求。

## 10：建立备份并恢复到新数据库

先完成 S3 创建、写入、读取校验，创建 Velero 认证 Secret，再安装 Velero：

```bash
kubectl create namespace velero
kubectl -n velero create secret generic velero-cloud \
  --from-file=cloud=secrets/cloud
helm upgrade --install velero velero-12.2.1.tgz \
  -n velero -f charts/velero.yaml
kubectl -n velero get pods,backupstoragelocation
python verify-backup.py
```

恢复验证必须使用新的命名空间、不同的 PV 和新的 PostgreSQL 数据目录。查看备份、恢复状态、备份文件摘要，并在恢复后的数据库查询原业务记录。

## 11：日常学习和排查记录

每完成一个实验，记录以下内容：

- 操作在哪台机器、哪个命名空间执行。
- 修改了哪个对象、配置字段或者进程。
- 观察到哪些状态、日志、事件和指标变化。
- 这些变化由哪个 Kubernetes 组件处理。
- 恢复操作是什么，恢复后如何验证。

配套材料：《204节点RKE2集群搭建流程》《204集群监控部署与使用文档》《Pod项目实操学习手册》《Kubernetes平台部署与学习流程》、部署源码包和实际验收记录。

## 12：打开页面并复查验收

保持第 03 步的 SSH 连接，在 Mac 的 `interview/` 新终端设置 KUBECONFIG，然后执行 `bash open-lab.sh`。脚本会打印任务系统、Pod 项目、Grafana、Prometheus、Alertmanager 和 Argo CD 的本机入口。关闭此终端会关闭这些页面转发。

```bash
export KUBECONFIG="$PWD/secrets/kubeconfig"
bash open-lab.sh
```

在另一个使用相同 KUBECONFIG 和 Python 虚拟环境的终端，读取管理账号并保存到本地私有文件：

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o json \
  > secrets/argocd-admin.json
kubectl -n monitoring get secret grafana-admin -o json \
  > secrets/grafana-admin.json
chmod 600 secrets/argocd-admin.json secrets/grafana-admin.json
python write-access.py
```

访问凭据位于 `secrets/access.txt`。最终验收还需要 Loki API 转发：

```bash
kubectl -n logging port-forward service/loki-gateway 13100:80
```

保持转发运行，在另一个已配置环境的终端执行：

```bash
python gitlab-status.py
python verify-platform.py
```

验收脚本检查节点就绪和调度、全部活动 Pod、管理页面、HTTPS、Prometheus 采集、真实 Loki 日志、Grafana 数据源、CI 成功状态、Argo CD 提交版本、备份恢复状态和 HPA 最小副本数。
