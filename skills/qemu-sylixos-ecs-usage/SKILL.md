---
name: qemu-sylixos-ecs-usage
description: 操作和排查 SylixOS ECS QEMU 虚拟机（Zynq UltraScale+ ZCU102，Cortex-A53）。启动、停止、查询虚拟机状态，通过串口、Telnet 或 FTP 连接，切换 host-only 与 loopback 网络模式，或检查 ECS 容器运行时时使用。
metadata:
  internal: true
---

# SylixOS ECS QEMU 虚拟机使用指南

先从当前 VM 配置读取虚拟机目录、网络模式和端点。本文中的 `192.0.2.10` 是文档示例地址，不能用于连接；所有目标地址必须替换为当前配置。

## 环境与路径

- **工作目录**（下文记作 `<VM_DIR>`）：取环境变量 `SYLIXOS_ECS_VM_DIR`；未设置时查找 `~/.local/share/realevo-simulator2/vm/zcu102-ecs`，仍找不到再询问用户
- **目标硬件与系统**：Xilinx Zynq UltraScale+ MPSoC (ZCU102) / 4 核 Cortex-A53 / 2 GB RAM / SylixOS GJB 3.3.1 (Professional)
- **镜像介质**：内核 `bspzynqmpsoc_simulator_zcu102_x64.elf`，运行磁盘 `sdcard-runtime.img`（8 GB 稀疏镜像）

---

## 核心运维指令

所有脚本位于 `<VM_DIR>` 下，执行前需切换至该目录或使用绝对路径：

| 操作 | 命令 | 完成判定准则 (Completion Criteria) |
| --- | --- | --- |
| **查询状态** | `./status.sh` | 输出包含 `ECS QEMU 运行中，PID <PID>` 或 `ECS QEMU 未运行` |
| **启动虚拟机** | `./start.sh` | 输出 `ECS QEMU 已启动` 且打印连接地址与日志路径；检查 `run/serial.log` 见内核启动并进入提示符 `[root@sylixos:/root]#` |
| **安全停止** | `./stop.sh` | 输出 `ECS QEMU 已停止（已同步磁盘）` 且 `run/qemu.pid` 不再存在 |
| **强制停止** | `./stop.sh --force` | 仅在客户机卡死、常规 stop 报 sync 超时时使用；输出 `ECS QEMU 已停止（跳过客户机同步）` |
| **接入串口** | `./console.sh` | 终端连接至串口，输入回车显示 Shell 提示符；脱出按快捷键 `Ctrl + ]`（虚拟机保持运行） |
| **上传文件** | `python3 ftp.py upload <local> <remote>` | 提示 `FTP 传输完成`，文件校验成功 |
| **下载文件** | `python3 ftp.py download <local> <remote>` | 提示 `FTP 传输完成`，本地生成目标文件 |
| **切换Host-only** | `./enable-host-only.sh` | 输出 `Network mode: host-only`，IP `192.0.2.10` 可通信 |
| **切换Loopback** | `./restore-loopback.sh` | 输出 `Network mode: loopback`，端口映射回退至 `127.0.0.1` |

---

## 访问与连接方式

### 凭据
- **账号**：`root`
- **密码**：`root`

### 连接协议与地址
- **串口控制台 (Console)**：
  - 接入命令：`./console.sh`（端口 `127.0.0.1:2323`，脱出快捷键：`Ctrl + ]`）
  - 日志文件：`run/serial.log`（当前），`run/serial.previous.log`（上一轮）
- **Telnet**：
  - Host-only 模式（默认）：`telnet 192.0.2.10 23`
  - 兼容回环模式：`telnet 127.0.0.1 2324`
- **FTP 传输**：
  - 推荐工具：`python3 ftp.py <upload|download> <local_path> <remote_path>`（自动匹配当前网络模式）
  - 需要上传回读校验（`--verify`）、进度、`rmtree` 或重试时，改用 `sylixos` 技能的 `scripts/ftp_client.py`，传入当前模式的地址和端口；用法见该技能的板卡操作参考
  - Host-only 直连：`192.0.2.10:21`（标准被动模式 PASV）
  - 兼容回环代理：`127.0.0.1:2121`（`ftp_proxy.py` 后台转发至内部 `2122`）
- **GDB 远程调试**：
  - 端点：`192.0.2.10:1234` 或 `127.0.0.1:1234`（需客户机预先启动 `gdbserver`）

---

## 规范操作工作流

### 1. 虚拟机生命周期工作流
1. **状态检查**：运行 `./status.sh`。若已运行则无需重复启动。
2. **启动**：运行 `./start.sh`。
   - **就绪判定**：QEMU 启动输出成功后，系统需要数秒启动。通过 `tail -n 20 run/serial.log` 确认看到 `[root@sylixos:/root]#` 提示符，或执行 `./status.sh` 确认进程存在。
3. **日常运维/开发**：通过 `./console.sh`、Telnet 或 `ftp.py` 部署程序并调试。
4. **安全关机**：
   - 优先确保客户机内正在写盘的业务进程已正常退出。
   - 执行 `./stop.sh`。底层通过 Telnet 执行 `sync` 同步磁盘并由 QMP 发送 `quit` 退出。
   - 若报 `磁盘同步未确认`，切勿盲目强杀；应先通过串口检查客户机卡死原因，确需放弃未写盘数据时才使用 `./stop.sh --force`。

### 2. ECS 容器环境快速验证
1. 连入客户机终端（串口或 Telnet）。
2. 执行 `ecs list`：
   - 验证 ECS 容器栈模块是否成功加载（由 `/etc/startup.sh` 自动调用 `/etc/cloudnative.sh` 初始化）。
   - 正常状态输出容器表头且容器数为 0。

---

## 专题参考 (Progressive Disclosure)

当涉及深层配置、排障或定制化操作时，请阅读对应的参考文档：

- **网络架构与模式切换**：[`references/networking.md`](references/networking.md)
  - 双网卡拓扑（`en4` Host-only + `en3` QEMU NAT）、Windows TAP 辅助进程交互原理、WSL 路由同步及网络模式切换内部实现。
- **存储与 ECS 运行时**：[`references/storage-and-ecs.md`](references/storage-and-ecs.md)
  - `sdcard-runtime.img` 稀疏镜像扩展原理、启动与模块挂载链路、ECS 常用运维命令。
- **故障排查与诊断**：[`references/troubleshooting.md`](references/troubleshooting.md)
  - 常见端口冲突处理、磁盘同步超时诊断、串口脱出异常处理、FTP 连接与 Windows 辅助进程故障应对。
