# 云原生学习实验室：从网页服务到 Volcano 计算任务

这个目录把原始 `K8s.Prometheus.Grafana` 项目扩展为一套可实践的学习代码。它包含两个场景：

1. **在线网页服务**：Nginx 页面通过 Deployment、Service、健康检查和 Prometheus 告警运行。
2. **离线计算任务**：Volcano Job 通过队列和成组调度运行 CPU 或 GPU 任务。

它们共享 Kubernetes：Linux 节点提供资源，容器提供统一运行环境，Kubernetes 管理长期服务，Prometheus 记录状态和告警，Volcano 管理完成后会退出的计算任务。

## 三种实践路径

| 路径 | 适合谁 | 完成什么 |
|---|---|---|
| `kind` 本地路径 | 第一次学习 Kubernetes | 在一台电脑上创建集群、部署网页、安装监控、提交 CPU Volcano Job。|
| `kubeadm` 双节点路径 | 想理解真实 Linux 集群 | 在两台 Linux 虚拟机上建立控制平面和工作节点。|
| BBT 路径 | 已获得 BBT 集群权限 | 使用自己的 Namespace、PVC 和 Volcano 队列提交 CPU/GPU 任务。|

从 [`QUICKSTART.md`](QUICKSTART.md) 开始。它给出最短操作路径。完整说明见 `docs/`。

## 目录

```text
lab/
├── app/                    网页与 Dockerfile
├── kind/                   本地 Kubernetes 集群配置
├── k8s/base/               Nginx Deployment、Service 与命名空间
├── monitoring/             PrometheusRule 告警规则
├── volcano/local/          本地 CPU 成组计算示例
├── volcano/bbt/            BBT PVC 和 GPU 任务模板
├── scripts/                创建、部署、验证和排障脚本
├── docs/                   从原理到操作的完整学习说明
└── QUICKSTART.md           最短实践路线
```

## 原项目与本项目的关系

原项目使用两台 Linux 虚拟机，通过 kubeadm、Flannel、Nginx、NodePort、Prometheus 和 Grafana 完成云原生监控和故障排查。本项目保留这些核心目标，补充以下内容：

- 可在 Kind 上重复运行的本地实验路径；
- 统一的验证脚本与故障检查顺序；
- PrometheusRule 示例；
- Volcano CPU 成组调度示例；
- BBT Namespace、NFS PVC、GPU 队列和 checkpoint 的接入方式；
- 从基础概念到面试表达的文档。

BBT 配置只使用变量和模板，不包含内部地址、账号、证书、队列名称或 kubeconfig。使用 BBT 时，以管理员分配的 Namespace、Queue 和 StorageClass 为准。

## 先理解，再执行

命令会创建容器、Kubernetes 对象和任务。每一步都提供验证命令。请在自己控制的本地集群或已获授权的 BBT Namespace 中执行，不要把 kubeconfig、Token、密码或内部地址提交到 Git 仓库。
