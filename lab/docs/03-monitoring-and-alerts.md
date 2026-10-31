# Prometheus、Grafana 和告警：从数值到判断

## 先分清三类问题

| 想知道什么 | 应查看什么 | 典型工具 |
|---|---|---|
| 现在网页能不能打开 | 真实 HTTP 请求 | 浏览器、curl、黑盒探测。|
| 节点资源是否紧张 | CPU、内存、磁盘等指标 | node-exporter、Prometheus、Grafana。|
| 应用是否保持了期望副本 | Deployment、Pod 的状态指标 | kube-state-metrics、Prometheus。|

Prometheus 并不自动知道所有事情。有人必须先提供数据，它才能采集。node-exporter 提供节点信息；kube-state-metrics 将 Kubernetes 对象状态变成指标；应用也可以直接提供自己的 `/metrics` 接口。

## 安装监控组件

本项目使用 `kube-prometheus-stack`，它会安装 Prometheus、Grafana、Alertmanager、node-exporter 和 kube-state-metrics 等组件。执行：

```bash
bash scripts/install-monitoring.sh
kubectl -n monitoring get pods
```

Grafana 首次登录密码由 Helm chart 写入 Secret。仅在自己终端中读取：

```bash
kubectl -n monitoring get secret monitoring-grafana \
  -o jsonpath='{.data.admin-password}' | base64 --decode
```

请将这个输出视为密码，不要提交到 Git 或发到公开渠道。

## 验证 Prometheus 采集

使用端口转发打开 Prometheus：

```bash
kubectl -n monitoring port-forward service/monitoring-kube-prometheus-prometheus 9090:9090
```

在浏览器访问 `http://localhost:9090/targets`。`UP` 表示 Prometheus 最近一次成功取得该目标的指标。它说明指标采集成功，不等于网页请求一定成功。

可以从表达式页面执行这些查询：

```promql
kube_deployment_status_replicas_available{namespace="cloud-native-lab",deployment="lab-web"}
```

它返回可用副本数量。为了看过去十分钟的容器重新启动变化，可以使用：

```promql
increase(kube_pod_container_status_restarts_total{namespace="cloud-native-lab",container="web"}[10m])
```

## Grafana 读图方法

读图顺序是：对象是谁、时间范围是什么、数值和单位是什么、变化是否与请求或日志同时发生。比如内存使用量变化不等于内存泄漏；需要再看进程、容器重启和服务响应。

## 告警规则的工作过程

`monitoring/prometheus-rule.yaml` 定义两条规则：

1. `LabWebUnavailable`：两分钟内没有可用副本。
2. `LabWebRestarting`：十分钟内重新启动超过两次。

Prometheus 定期计算规则。条件刚出现时会进入 Pending；持续满足指定时间后，状态成为 Firing，并发送给 Alertmanager。Alertmanager 负责分组、去重、静默和路由通知。

验证规则前，先确认它已被 Prometheus 接受：

```bash
kubectl -n monitoring get prometheusrule lab-web-alerts
```

在学习环境中删除 Deployment 的两个 Pod，可以观察可用副本下降，再从 Prometheus 的 Alerts 页面观察状态变化。实验结束后使用 `kubectl -n cloud-native-lab rollout status deployment/lab-web` 确认副本恢复。

## 面试表达

可以说：我通过 node-exporter 和 kube-state-metrics 提供指标，Prometheus 周期性采集并保存时间序列，Grafana 用于查看节点和应用状态，PrometheusRule 用于检查持续异常，Alertmanager 负责通知。接着补充一次自己执行过的验证或故障实验。
