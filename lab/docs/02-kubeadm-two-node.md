# 两台 Linux 虚拟机建立 Kubernetes：kubeadm 学习路线

这部分适合想理解原项目双节点结构的人。准备两台 Linux 虚拟机：一台作为控制平面，一台作为工作节点。两台机器需要能够互相访问，具有固定或可识别的地址，并且具备管理员权限。

生产环境安装前，请先阅读 Kubernetes 当前版本的 [kubeadm 官方说明](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)。版本、容器运行工具和网络插件要求会变化。

## 1. 每台机器的准备工作

在两台机器上完成：关闭 swap，加载容器网络需要的内核模块，安装 containerd、kubeadm、kubelet 和 kubectl。下面命令展示 Ubuntu/Debian 方向，执行前请按当前官方安装文档确认仓库地址和版本。

```bash
sudo swapoff -a
sudo modprobe overlay
sudo modprobe br_netfilter
sudo install -m 0644 bootstrap/kubeadm/sysctl-k8s.conf /etc/sysctl.d/k8s.conf
sudo sysctl --system
```

containerd 是节点上真正运行容器的工具。kubelet 是 Kubernetes 放在每个节点上的代理，负责让 Pod 按要求运行。kubeadm 用于创建控制平面和加入工作节点。

```bash
sudo apt-get update
sudo apt-get install -y containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml >/dev/null
sudo systemctl restart containerd
sudo systemctl enable containerd
```

安装 Kubernetes 组件时，请使用同一小版本。官方文档会给出当前适用的软件源和安装命令。安装后验证：

```bash
kubeadm version
kubelet --version
kubectl version --client
```

## 2. 控制平面初始化

在控制平面节点执行。`POD_CIDR` 必须与后续网络插件匹配；原项目使用 Flannel 时采用 `10.244.0.0/16`。

```bash
export POD_CIDR=10.244.0.0/16
sudo kubeadm init --pod-network-cidr="$POD_CIDR"
```

成功后，kubeadm 会输出一条 `kubeadm join` 命令。它含有短期凭据，直接在工作节点执行，不要把完整内容提交到仓库或公开文档。

为当前用户配置 kubectl：

```bash
mkdir -p "$HOME/.kube"
sudo cp -i /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
kubectl get nodes
```

初始化阶段控制平面显示 `NotReady` 是正常现象，因为 Pod 网络尚未安装。

## 3. 安装 Pod 网络并加入工作节点

网络插件为不同节点的 Pod 提供互相通信的能力。原项目使用 Flannel。使用时请从 Flannel 官方发布页选择与 Kubernetes 版本相配的清单，然后执行 `kubectl apply -f <网络插件清单>`。

在工作节点执行 kubeadm 输出的 join 命令。回到控制平面验证：

```bash
kubectl get nodes -o wide
kubectl get pods -A
```

预期两台节点最终均为 `Ready`。如果节点不就绪，先看系统 Pod 和 `kubectl describe node <节点名>` 的 Events。

## 4. 把本项目部署到双节点集群

双节点集群不能直接使用本地 Kind 镜像。需要把 `lab/app` 构建为可被节点下载的镜像，例如发布到你拥有权限的 GHCR 仓库。然后把 Deployment 的 `image` 改为该镜像，并把 `imagePullPolicy` 改为 `IfNotPresent`。

```bash
kubectl apply -k k8s/base
kubectl -n cloud-native-lab get pods -o wide
kubectl -n cloud-native-lab get service lab-web
```

`kubectl get service` 会显示 NodePort。使用 `节点地址:NodePort` 访问。NodePort 只是将节点端口转交给 Service；Service 再选择符合标签且通过就绪检查的 Pod。

## 5. 这条路线可以验证什么

1. 删除一个 Pod，观察 Deployment 创建新的 Pod。
2. 调整副本数从 2 变为 3，观察实际副本变化。
3. 故意指定不存在的镜像，观察 ImagePullBackOff 和 Events。
4. 修改网页、构建新镜像、更新 Deployment，观察滚动更新和新页面。

每次实验结束后，记录“现象、检查、原因、处理、验证”。这五项就是面试讲述项目经历最可靠的材料。
