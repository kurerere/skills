# QEMU SylixOS ECS 网络架构与模式参考

## 1. 双网卡拓扑设计

当前实例配置双网卡互补拓扑：

```text
宿主机 (Windows / WSL)               QEMU SylixOS ECS 虚拟机 (ZCU102)
192.0.2.10 (TAP)  <=== Host-only ===>  en4: 192.0.2.10/24 (无默认网关)
宿主机公网出口       <=== QEMU NAT  ===>  en3: 192.0.2.10/24 (网关 192.0.2.10, DNS 192.0.2.10)
```

### 网卡分配与职责
| 网卡名 | 模式 | 客户机 IP | 宿主机端对应 | 职责与特性 |
| --- | --- | --- | --- | --- |
| `en4` | Host-only | `192.0.2.10/24` | `192.0.2.10/24` (Windows TAP `acoinfo_host`) | 供 Windows / WSL 直连 Telnet、FTP、GDB 等开发服务；不配默认网关，避免路由冲突。 |
| `en3` | QEMU User NAT (SLiRP) | `192.0.2.10/24` | QEMU 内置 SLiRP 栈 | 负责出站访问公网（ping、镜像拉取等），默认网关 `192.0.2.10`，DNS `192.0.2.10`；同时暴露旧本地兼容端口映射。 |

---

## 2. 宿主机网络影响与隔离性

1. **Windows TAP 辅助进程机制**：
   - 宿主机复用闲置的 Windows TAP 网卡 `acoinfo_host`。原始静态地址备份于 `network-original.json`（原通常为 `192.0.2.10/24`）。
   - Windows 端仅运行一个极轻量 QEMU 进程（`-name sylixos-ecs-network -m 16M`），仅桥接 TAP 与本地 TCP `2340`，不跑客户机内核或磁盘。
   - Linux 端主 QEMU 通过 `-nic socket,model=cadence_gem,connect=127.0.0.1:2340` 接入。
   - Windows 辅助进程由 PowerShell 通过 WMI 脱离 WSL 会话创建，避免互操作进程等待导致超时。
2. **WSL2 路由同步**：
   - 在 WSL2 mirrored 网络模式下，宿主机 TAP 网卡的 `192.0.2.10/24` 直连路由会自动同步至 WSL。WSL 内可直接 ping/telnet/ftp `192.0.2.10`。
3. **无系统级 NAT 污染**：
   - 客户机上网完全由 QEMU 用户态 SLiRP 完成，无需开启 Windows ICS、无需 `New-NetNat`、无需 Linux 内核 `ip_forward` 或 iptables 规则。
   - 不修改宿主机默认网关、DNS、Clash 代理或 Tailscale 配置。局域网其他设备不会自动路由至该虚拟机。

---

## 3. 端口与连接端点一览

### 主流连接端点 (Host-only 模式，默认)
- **串口 Console**：`127.0.0.1:2323`（主 QEMU 字符设备，不走网络协议栈；使用 `./console.sh` 接入）
- **Telnet 终端**：`192.0.2.10:23`（用户/密码：`root` / `root`）
- **FTP 服务**：`192.0.2.10:21`（标准被动模式 PASV，普通 FTP，用户/密码：`root` / `root`）
- **GDB 远程调试**：`192.0.2.10:1234`（取决于客户机内 gdbserver 是否启动）

### 兼容端口 (Loopback 模式或旧脚本兼容)
- **兼容 Telnet**：`127.0.0.1:2324` -> 客户机 `23`
- **兼容 FTP 代理**：`127.0.0.1:2121`（由后台 `ftp_proxy.py` 转发至内部 `2122`，动态重写 PASV 端口并使用 QMP 转发数据端口）
- **兼容 GDB**：`127.0.0.1:1234` -> 客户机 `1234`

---

## 4. 网络模式切换流程

虚拟机支持在 Host-only 与纯 Loopback 两种模式间切换。

### 切换至 Host-only 模式
```bash
./enable-host-only.sh
```
底层执行：
1. 启动实例（若未运行）。
2. 通过 FTP 将 `ifparam.hostonly.ini` 上传为客户机 `/etc/ifparam.ini` 并回读严格校验。
3. 安全同步停止客户机。
4. 将 `network-mode` 文件写入 `host-only`。
5. 配置 Windows TAP 网卡 IP 为 `192.0.2.10/24`。
6. 重启 QEMU，使双网卡生效。

### 切换至纯 Loopback 模式
```bash
./restore-loopback.sh
```
底层执行：
1. 启动实例并上传 `loopback-backup/ifparam.local.ini` 至客户机 `/etc/ifparam.ini` 并校验。
2. 安全同步停止。
3. 移除 Windows TAP 上的 `192.0.2.10`，恢复原始静态 IP。
4. 记录 `network-mode` 为 `loopback`。
5. 仅以 SLiRP 端口映射形式启动，仅能使用 `127.0.0.1:2324` / `2121` 连接。
