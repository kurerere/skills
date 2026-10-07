# QEMU SylixOS ECS 存储与容器运行时参考

## 1. 磁盘与镜像组织

虚拟机目录包含两个核心镜像文件：

- `sdcard.img`：原始 6 GB SD 卡基础镜像（只读归档用途，请勿直接修改）。
- `sdcard-runtime.img`：8 GB 稀疏运行镜像（Sparse File）。
  - **容量扩展原理**：为满足当前 QEMU 模拟 SD 卡的特定容量几何约束，从原始 6 GB 扩展至 8 GB，未重新分区。
  - **分区结构**：包含两个标准分区，开机自动挂载到根文件系统及数据卷。
  - **持久化语义**：客户机运行时的所有文件更改、日志、配置、新部署的容器均写入此运行副本。

---

## 2. 系统启动与 ECS 初始化流程

SylixOS 系统启动时的关键启动链路：

1. **内核引导与根文件系统挂载**：
   - QEMU 加载内核 `bspzynqmpsoc_simulator_zcu102_x64.elf`。
   - 挂载 SD 卡分区至 `/`。
2. **启动脚本执行 (`/etc/startup.sh`)**：
   - 自动调用 `/etc/cloudnative.sh` 脚本。
   - `cloudnative.sh` 加载 ECS 容器模块（内核 cgroup、命名空间驱动支持，初始化 `/var/run/ecs` 等工作目录）。
   - 解析 `/etc/ifparam.ini` 设置双网卡 IP 与默认路由。
   - 自动配置 DNS 域名解析（指向 `192.0.2.10`）。

---

## 3. ECS 容器环境验证与使用

登录客户机终端后（通过串口 `./console.sh` 或 Telnet `192.0.2.10`），可通过 `ecs` 命令行工具管理容器：

### 验证 ECS 运行时状态
```bash
[root@sylixos:/root]# ecs list
NAME   IMAGE   COMMAND   CREATED   STATUS   PORTS
```
- 正常情况下开机容器数量为 0。
- 若 `ecs list` 返回表格头且无报错，表明 ECS 内核支持与守护进程正常就绪。

### 常用容器命令
- **拉取/导入镜像**：`ecs pull <image>` 或通过本地 Bundle 导入
- **运行容器**：`ecs run -d --name <container_name> <image>`
- **查看容器状态**：`ecs list -a`
- **执行容器内命令**：`ecs exec -it <container_name> <cmd>`
- **停止并删除容器**：`ecs kill <container_name>`，`ecs rm <container_name>`

> [!NOTE]
> 默认开机并未自启任何 CRI JavaScript 服务、ECSM 管理平台或业务容器，需根据业务需求手动启动或脚本拉起。
