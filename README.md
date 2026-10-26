# Linux、Docker、Kubernetes、Prometheus 与 Volcano 图文教程

[在线阅读](https://chennyso.github.io/K8s-/)

从“写好一个网页以后，怎样让别人访问”开始，逐步理解 Linux 运行程序、Docker 制作镜像、Kubernetes 管理应用、Prometheus 采集指标的过程。Volcano 部分通过四成员计算任务，解释成组调度和队列。

正文包含 10 个学习主题、14 张图片和 30 道复习题。

## 阅读内容

1. Linux 怎样运行程序，文件权限为什么影响网页访问。
2. CPU、内存、磁盘、网络和日志怎样帮助检查问题。
3. 浏览器怎样查询地址、连接端口并取得网页。
4. Nginx 怎样读取文件、转交请求和分配请求。
5. Dockerfile、镜像和容器怎样配合，端口和数据怎样保存。
6. Kubernetes 怎样管理 Pod、副本、节点和 Service。
7. Prometheus 怎样采集、保存、查询数据，以及怎样与 Grafana、Alertmanager 配合。
8. Volcano 怎样处理成组任务、队列、资源等待和失败恢复。
9. 怎样根据状态、事件和日志寻找故障原因。
10. 网页修改以后，怎样构建、发布和验证新版本。

## 离线阅读

[下载离线资料包](kubernetes-interview-guide.zip)，解压后用浏览器打开 `index.html`。保持 `figures` 目录与正文的相对位置。

页面支持搜索、图文学习与问答复习切换、隐藏答案、学习勾选和打印。正文与图片可以离线查看，外部资料链接需要联网访问。

## 文件说明

- `index.html`：完整教程。
- `figures/`：正文使用的图片和 Mermaid 图解源文件。
- `阅读说明.md`：阅读与使用说明。
- `figure-sources.json`：所附 PDF 原图来源。
- `validation.json`：正文、图片及页面功能检查记录。
- `kubernetes-interview-guide.zip`：完整离线资料包。

## 资料来源

网页与集群监控部分结合 [Roccse/K8s.Prometheus.Grafana](https://github.com/Roccse/K8s.Prometheus.Grafana) 项目，核对代码版本为 `0822eaa`。Volcano 使用官方资料与计算任务例子展开讲解。技术参考链接见教程末尾。

三张原图来自所附《1456页Linux学习笔记（从入门到进阶）》第 304、424、1278 页；原图来源记录在 `figure-sources.json`。其余十一张图解使用 Mermaid 编写。

整理日期：2026-10-26。
