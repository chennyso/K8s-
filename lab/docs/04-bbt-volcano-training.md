# BBT 与 Volcano：从网页服务扩展到计算任务

这部分只适用于已经获得 BBT 集群账号和 Namespace 权限的用户。它不替代管理员开通权限、分配队列或配置 GPU 的流程。

## BBT 中的资源结构

BBT 使用 Kubernetes 管理节点和 Pod，Volcano 管理批量计算，SLURM 面向传统 HPC 脚本。GPU 训练、PyTorch、数据处理等容器化任务适合 Volcano；已有 VASP、LAMMPS、MPI 和 Slurm 脚本的计算适合按集群规定使用 SLURM。

| 对象 | 你需要知道的事 |
|---|---|
| Namespace | 你的资源隔离范围，例如管理员分配的个人或课题组空间。|
| Queue | Volcano 为任务分配资源的队列，名称由管理员分配。|
| PVC | 持久化工作区；BBT 默认建议 NFS 用于代码、环境、checkpoint 和小文件。|
| GPU | 通过 `nvidia.com/gpu` 申请，任务仅在获得对应设备后运行。|
| Volcano Job | 描述一次批量任务、worker 数量、资源、队列和重试策略。|

## 1. 先检查自己的权限和队列

假设管理员告诉你 Namespace 是 `advisor-yourname`，GPU Queue 是 `advisor-yourname-gpu`：

```bash
bash scripts/verify-bbt-access.sh advisor-yourname advisor-yourname-gpu
```

这个脚本验证 Namespace、创建 Volcano Job/PVC 的权限、队列和节点 GPU 资源。任何一步失败时，应根据输出联系管理员或检查自己的 kubeconfig 上下文。

## 2. 创建 NFS 工作区

NFS PVC 适合代码、Python 环境、小文件 checkpoint 和结果。申请 PVC：

```bash
kubectl -n advisor-yourname apply -f volcano/bbt/workspace-pvc.yaml
kubectl -n advisor-yourname get pvc workspace-pvc
```

PVC 变成 `Bound` 后，Pod 可以挂载它。工作区建议分开保存：

```text
/workspace/
├── repos/          代码
├── data/           数据集
├── venvs/          Python 环境
├── checkpoints/    可恢复训练状态
└── runs/           日志和结果
```

不要把 kubeconfig、私钥、Token 或私密数据放在共享目录中。TB 级顺序读取的巨大数据可以根据管理员提供的 StorageClass 使用 JuiceFS；不要把 venv、代码 checkout 和大量小 checkpoint 放在 JuiceFS。

## 3. 运行 GPU Smoke Test

先打开 `volcano/bbt/gpu-smoke-job.yaml`，将 `REPLACE_WITH_YOUR_GPU_QUEUE` 改成管理员分配的队列。然后执行：

```bash
kubectl -n advisor-yourname apply -f volcano/bbt/gpu-smoke-job.yaml
kubectl -n advisor-yourname get vcjob,pods
```

任务开始后查看日志：

```bash
kubectl -n advisor-yourname logs -f -l volcano.sh/job-name=gpu-smoke --prefix
```

预期日志会显示 GPU 信息、PyTorch 能否使用 CUDA，以及 `/workspace/runs/gpu-smoke/completed-at.txt` 的完成记录。

## 4. 任务为什么会 Pending

Pending 说明任务已提交，但还没有满足运行条件。常见原因包括 Queue 无可用资源、GPU 已被其他任务使用、镜像无法拉取、PVC 未绑定、节点选择条件不满足，或者成组调度尚未达到 `minAvailable`。

按以下顺序检查：

```bash
kubectl -n advisor-yourname describe vcjob gpu-smoke
kubectl -n advisor-yourname get pods
kubectl -n advisor-yourname describe pod <pod-name>
kubectl get queue advisor-yourname-gpu
```

Events 记录了调度和启动失败原因。先读 Events，再针对具体原因处理。

## 5. checkpoint 和自动重试

容器重新运行以后，内存中的训练状态会消失。训练程序应定期把模型、优化器和当前轮次写入 `/workspace/checkpoints/<实验名>`。重启后读取最新 checkpoint 继续训练。

Volcano 的 `maxRetry` 处理 Pod 级重试，容器的 `restartPolicy` 处理容器级失败，checkpoint 处理程序状态恢复。三部分需要一起设计。

## 6. 训练与网页服务怎样在一套项目中共存

网页服务使用 Deployment，因为它要长期存在并持续响应请求；训练使用 Volcano Job，因为训练完成后应该退出并释放 GPU。Prometheus 可以分别观察节点、GPU、Pod 和任务状态。把服务、监控、训练和数据恢复放进同一套项目，能展示你理解不同工作负载的运行方式。
