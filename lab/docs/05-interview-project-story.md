# 面试时怎样讲这个项目

## 30 秒版本

我搭建了一个云原生学习实验室。基础部分用 Linux 节点和 Kubernetes 运行两个 Nginx 网页副本，通过 Service 对外提供访问；使用 Prometheus、Grafana 和告警规则观察节点资源、Deployment 副本和容器重启。进阶部分用 Volcano 管理 CPU/GPU 批量任务，结合 PVC 保存训练结果和 checkpoint。项目通过 Kind 在本地重复验证，双节点 kubeadm 和 BBT 作为真实集群实践路线。

## 追问时的展开顺序

### 为什么使用 Docker

网页文件和 Nginx 打包为镜像，换节点时使用同一份镜像启动容器，避免手动安装和配置差异。镜像是初始运行内容，容器才是实际运行实例。

### 为什么使用 Deployment 和 Service

Deployment 表达“保持两个副本”的期望；一个 Pod 消失后控制器尝试补足数量。Pod 地址会变化，Service 提供稳定入口，通过标签选择当前可用实例。Readiness 决定实例何时参与接收请求，Liveness 用于发现持续失效的容器。

### Prometheus 怎样工作

指标提供方暴露数值，Prometheus 定期拉取并保存为时间序列。Grafana 用于读图。PrometheusRule 根据指标判断持续异常，Alertmanager 处理通知。Targets 为 UP 说明最近的指标采集成功，需要和真实网页请求分别验证。

### Volcano 为什么适合训练

训练是完成后退出的批量任务，可能需要多个 worker、GPU、队列和最低成员数量。Volcano 可以按 Queue、资源和 `minAvailable` 做成组调度，避免只启动部分强依赖成员后长时间等待。

### 你做过哪些验证

只说亲自做过的操作。可选实验包括：删除一个 Pod 观察替代副本、部署错误镜像观察 Events、修改网页构建新镜像观察滚动更新、安装监控查询可用副本、提交 CPU Gang Job 观察两个 worker 一起启动。每项实验都按现象、检查、原因、处理、验证讲述。

## 项目边界

Kind 用于本地学习，不等同于生产集群。双节点 kubeadm 与单控制平面适合学习部署、网络和应用恢复，控制平面故障、持久化存储、跨可用区容灾等问题需要额外设计。BBT GPU 任务依赖管理员提供的 Namespace、Queue、PVC 和硬件权限，模板不能替代这些前置条件。
