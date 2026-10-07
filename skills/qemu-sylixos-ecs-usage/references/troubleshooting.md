# QEMU SylixOS ECS 故障排查与诊断参考

## 1. 端口冲突与启动失败

### 现象
执行 `./start.sh` 提示端口绑定失败或退出代码非零。

### 原因与排查
启动时脚本会预检以下端口：
- `2323`：QEMU 串口 TCP 监听端口。
- `2324`：QEMU Telnet 本地兼容端口。
- `2121`：`ftp_proxy.py` 监听端口。
- `2122`：QEMU 内部 FTP 转发端口。
- `1234`：QEMU GDB 本地兼容端口。
- `2340` / `2341`：Windows 端 QEMU 网络辅助进程的网卡 Socket 与 QMP 控制端口。

### 检查与清理命令
```bash
# 检查占用进程
ss -tulpn | grep -E ':(2121|2122|2323|2324|1234|2340|2341)'

# 若有遗留死进程，确认后终止
pkill -f 'qemu-system-aarch64.*sylixos-ecs'
pkill -f 'ftp_proxy.py'
```

---

## 2. 虚拟机停止挂起（磁盘同步未确认）

### 现象
执行 `./stop.sh` 提示：
`错误：磁盘同步未确认，保留运行状态。可修复连接后重试；--force 将跳过同步。`

### 原因
为了防止文件系统损坏和数据丢失，`vm.py stop` 会先通过客户机 Telnet 端口（`127.0.0.1:2324`）执行 `sync` 命令。若客户机处于严重卡死、网络未就绪或未响应状态，将主动保留运行中的 QEMU 进程。

### 处理方案
1. **优先排查网络连接**：通过 `./console.sh` 登录控制台，检查客户机系统是否仍在正常运行，并在控制台手动执行 `sync`。
2. **强制终止（数据丢失风险）**：
   ```bash
   ./stop.sh --force
   ```
   该操作跳过客户机 `sync`，直接通过 QMP 接口向 QEMU 发送 `quit` 终止信号并清理网络辅助进程。

---

## 3. 串口控制台无法脱出或显示异常

### 现象
进入 `./console.sh` 后不知道如何退出，或按 `Ctrl + C` / `Ctrl + D` 无法断开。

### 解决办法
- **脱出快捷键**：按下 `Ctrl + ]`（即 ASCII `0x1d`）。
- **脱出后状态**：断开 `socat` 连接仅退出当前串口查看，虚拟机在后台继续持续运行。
- **重新接入**：再次执行 `./console.sh` 即可回到终端。
- **无交互式查看日志**：直接查看日志文件 `run/serial.log`（最新轮次）或 `run/serial.previous.log`（上一轮次）。

---

## 4. FTP 传输超时或被拒绝

### 现象
使用第三方客户端连接 FTP 报连接超时、无法获取目录列表或传输失败。

### 关键排查点
1. **连接模式确认**：
   - **Host-only 直连模式**：目标为 `192.0.2.10:21`，**必须开启被动模式 (PASV)**，普通明文 FTP（非 FTPS/TLS）。
   - **兼容代理模式**：目标为 `127.0.0.1:2121`，底层由 `ftp_proxy.py` 转发。
2. **推荐方式**：优先使用内置的 `ftp.py` 脚本：
   ```bash
   python3 ftp.py upload <local_file> <remote_path>
   python3 ftp.py download <local_file> <remote_path>
   ```
   该脚本会自动读取当前的 `network-mode` 选择对应的目标 IP、端口并正确配置被动模式。
3. **代理日志分析**：若经由 `127.0.0.1:2121` 传输异常，查看 `run/ftp-proxy.log` 排查 QMP 端口映射建立失败原因。

---

## 5. Windows 网络辅助进程无响应

### 现象
启动时报告：`Windows network helper did not become ready`。

### 原因与排查
- 宿主机缺少 Windows TAP 网卡 `acoinfo_host`。可在 Windows PowerShell 中执行 `Get-NetAdapter -Name acoinfo_host` 确认网卡存在。
- 检查 Windows 任务管理器中是否存在挂起的 `qemu-system-aarch64.exe` 进程（命令行带有 `-name sylixos-ecs-network`）。
- 如需重置辅助进程，可在 Windows PowerShell 中执行：
  ```powershell
  Stop-Process -Name qemu-system-aarch64 -Force
  ```
