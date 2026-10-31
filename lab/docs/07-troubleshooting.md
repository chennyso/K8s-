# 排障手册：从现象到验证

## 网页无法访问

```bash
kubectl -n cloud-native-lab get pods -o wide
kubectl -n cloud-native-lab get service lab-web
kubectl -n cloud-native-lab get endpointslices -l kubernetes.io/service-name=lab-web
kubectl -n cloud-native-lab describe pod <pod-name>
kubectl -n cloud-native-lab logs <pod-name> -c web
```

| 看到的现象 | 可能所在环节 | 下一步 |
|---|---|---|
| Pod 为 Pending | 节点资源或调度条件 | 阅读 `describe pod` 的 Events。|
| Pod 为 ImagePullBackOff | 镜像名、仓库权限或网络 | 核对 image 和节点拉取条件。|
| Pod 反复重启 | 程序、探针或资源限制 | 阅读容器日志和上次终止原因。|
| EndpointsSlice 没有后端 | 标签或就绪检查 | 核对 Service selector、Pod labels 和 Ready 状态。|
| Pod 正常但 NodePort 超时 | 节点端口或网络路径 | 从集群内请求 Service，再检查外部入口。|

## Prometheus 没有数据

```bash
kubectl -n monitoring get pods
kubectl -n monitoring get prometheusrule lab-web-alerts
kubectl -n monitoring port-forward service/monitoring-kube-prometheus-prometheus 9090:9090
```

在 Prometheus Targets 页检查目标状态。采集目标为 UP 时，表示指标采集成功；若图表仍空白，检查查询中的指标名称、标签和时间范围。

## Volcano 任务 Pending

```bash
kubectl -n cloud-native-lab get vcjob,pods
kubectl -n cloud-native-lab describe vcjob cpu-gang-demo
kubectl -n cloud-native-lab describe pod <pod-name>
kubectl get queue default
```

本地示例的 `minAvailable: 2` 表示两个 worker 都需要满足条件。BBT GPU 任务还要确认自己的 Queue、GPU 可用量、PVC 和 Namespace 权限。

## 通用原则

记录请求的时间、操作位置、目标地址和原始错误。先查看状态和 Events，再看日志；完成处理后，重新执行原始操作确认恢复。这样你可以解释为什么自己的处理有效。
