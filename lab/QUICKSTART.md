# 最短动手路径：本地网页、监控和 Volcano

这条路线使用 Kind 在本机 Docker 中创建 Kubernetes 集群。完成后，你将看到网页、Prometheus 数据、Grafana 和一个需要两个成员一起运行的 Volcano 任务。

## 0. 准备工具

需要 Docker、kubectl、kind 和 Helm。macOS 可以安装：

```bash
brew install docker kubectl kind helm
```

启动 Docker Desktop，确认下面三个命令都能输出版本：

```bash
docker version
kubectl version --client
kind version
```

## 1. 克隆项目并进入实验目录

```bash
git clone https://github.com/chennyso/K8s-.git
cd K8s-/lab
```

## 2. 创建本地 Kubernetes 集群

```bash
bash scripts/create-kind-cluster.sh
kubectl get nodes
```

预期看到一个 control-plane 节点和两个 worker 节点，状态为 `Ready`。

## 3. 构建网页镜像并部署应用

```bash
bash scripts/deploy-local-web.sh
kubectl -n cloud-native-lab get pods,svc
```

浏览器打开 `http://localhost:8080`。页面出现“Cloud Native Learning Lab”说明浏览器、Service、Pod 和 Nginx 已经连通。

## 4. 验证应用

```bash
bash scripts/verify-web.sh
```

脚本会检查 Deployment 是否有两个可用副本、Service 是否存在、网页是否包含预期标题。

## 5. 安装 Prometheus 与 Grafana

```bash
bash scripts/install-monitoring.sh
kubectl -n monitoring get pods
```

等待监控组件进入 `Running`。打开 Grafana：

```bash
kubectl -n monitoring port-forward service/monitoring-grafana 3000:80
```

在浏览器访问 `http://localhost:3000`。登录密码由 Helm chart 创建在 Kubernetes Secret 中；按 `docs/03-monitoring.md` 的命令从自己的集群读取。请不要把密码复制到仓库、聊天记录或截图中。

## 6. 安装 Volcano 并运行成组 CPU 任务

```bash
bash scripts/install-volcano.sh
bash scripts/run-local-volcano-job.sh
kubectl -n cloud-native-lab get vcjob,pods
```

这个示例要求两个 worker 一起运行。查看日志：

```bash
kubectl -n cloud-native-lab logs -l volcano.sh/job-name=cpu-gang-demo --prefix
```

## 7. 清理本地集群

```bash
kind delete cluster --name cloud-native-lab
```

完整解释、kubeadm 双节点路线、BBT GPU 路线、监控查询和排障过程见 `docs/`。
