# 原项目代码逐项阅读

原项目的当前提交为 `0822eaa`。下面按文件说明它们解决什么问题，以及本实验室如何吸收这些设计。

## `site/index.html` 与 `Dockerfile`

原项目的网站文件是 Nginx 实际返回给浏览器的内容。Dockerfile 使用 `nginx:1.27-alpine` 作为基础镜像，通过 `COPY site/index.html /usr/share/nginx/html/index.html` 将网页复制进 Nginx 默认目录，声明容器使用 80 端口。

这里没有编译复杂应用，目的是把注意力放在容器、部署和访问。`lab/app/Dockerfile` 保留这个思路，网页中放入了可被验证脚本检查的 `web-response-ok` 文本。

## `k8s/app/nginx-demo-deployment.yaml`

原项目的基础 Deployment 有四个重要部分：

| 配置 | 含义 |
|---|---|
| `replicas: 2` | 希望持续运行两个 Nginx Pod。|
| `selector.matchLabels` | Deployment 通过标签识别自己管理哪些 Pod。|
| `image: nginx:latest` | Pod 启动时使用的镜像。|
| `resources.requests/limits` | 调度所需资源与容器使用上限。|

`requests` 影响调度器能否为 Pod 找到节点；`limits` 限制运行时可使用的 CPU 和内存。原项目使用 50m CPU、64Mi 内存作为申请量，200m CPU、128Mi 内存作为限制。

本项目仍然使用两个副本和相近资源，同时加入滚动更新、Readiness、Liveness、最小权限和明确的本地镜像策略。原项目基础清单使用 `nginx:latest` 便于演示；学习与生产场景更适合固定具体版本或镜像摘要，保证每次部署使用相同内容。

## `k8s/app/nginx-demo-service.yaml`

Service 通过 `selector: app: nginx-demo` 找到 Pod，并把 NodePort 31258 上的请求转到容器的 `http` 端口。浏览器访问节点地址和 NodePort，节点网络规则将请求交给 Service 后端。

本项目的 Kind 配置把宿主机 8080 映射到 Kind control-plane 的 30080，再由 NodePort Service 进入 Nginx。这样学习者在一台电脑上就能访问 `http://localhost:8080`。

## Helm Chart：`deploy/helm/nginx-demo`

Helm 将可复用的 Kubernetes YAML 与可修改值分开：

| 文件 | 作用 |
|---|---|
| `Chart.yaml` | Chart 的名称和版本信息。|
| `values.yaml` | 镜像、副本、端口、资源和安全设置的默认值。|
| `templates/deployment.yaml` | 用 Values 渲染 Deployment。|
| `templates/service.yaml` | 用 Values 渲染 Service。|

原项目使用滚动更新策略：`maxUnavailable: 0` 表示更新期间不主动减少可用副本，`maxSurge: 1` 表示最多额外创建一个新副本。Readiness 访问 `/`，通过后 Service 才会把请求交给该 Pod；Liveness 定期访问 `/`，持续失败时 Kubernetes 会尝试重启容器。

`topologySpreadConstraints` 尝试将相同应用分布到不同主机。它有助于降低单台节点故障同时影响多个副本的概率，但实际效果取决于节点数量、标签和资源条件。

## 监控：`monitoring/promql-examples.md` 与告警规则

原项目把监控分成两类：节点资源和 Kubernetes 对象状态。node-exporter 提供节点指标，kube-state-metrics 提供 Deployment、Pod 等状态指标。Prometheus 保存时间序列，Grafana 读取和展示。

告警规则 `NginxDemoUnavailable` 使用可用副本数判断应用是否完全不可用；`NginxDemoPodRestarting` 统计十分钟窗口内的重新启动次数。规则的 `for: 5m` 要求条件持续五分钟，减少短暂波动造成的噪声。

本项目的 `monitoring/prometheus-rule.yaml` 保留相同逻辑，命名空间、Deployment 和阈值换成实验室对象，时间缩短为两分钟以便学习时更快观察。

## GitHub Actions：`.github/workflows/build-image.yml`

原项目的工作流由两个阶段组成：

1. GitHub 托管 runner 构建镜像并推送 GHCR，同时执行 Helm lint。
2. 自建 runner 访问本地 Kubernetes，使用 Helm 安装或更新应用，再等待滚动更新并用 HTTP 请求验证。

工作流将仓库名转换为小写，因为 OCI 镜像仓库名称要求小写。这个细节来自原项目一次 `InvalidImageName` 的真实修复记录。自建 runner 能访问本地集群，是自动部署成立的前提；GitHub 托管 runner 通常无法直接访问你的内网 Kubernetes。

## 故障记录的价值

原项目收集了 Flannel、CoreDNS、NodePort、Prometheus、镜像命名等故障记录。它们表明排障从现象开始，沿着状态、Events、日志、Service 后端、节点网络和运行工具逐层缩小范围。最终必须用原始访问方式再次验证处理效果。
