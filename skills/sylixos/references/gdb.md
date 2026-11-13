# SylixOS 远程 GDB

## 环境与符号

读取当前项目的目标配置和调试指南，确认架构、SDK、交叉 GDB、目标调试服务及端口。选择匹配架构与 ABI 的调试器，不默认 ARM64，不把普通主机 GDB 当作替代。

区分目标可执行文件与主机符号 ELF。优先使用用户或构建记录明确对应的产物；同名不算匹配依据，strip 后文件与未剥离 ELF 的哈希也可能不同，需结合构建记录、Build ID（可用时）或可对齐的代码段核对。匹配不足时说明证据范围，源码行级定位以匹配产物为前提。

sysroot、库搜索路径和共享库符号来自实际目标库版本及当前工程，不能借用另一个工作区的默认目录。没有调试信息可做有限指令/寄存器检查，但要说明限制。

## 目标服务

先读 [board-operations.md](board-operations.md) 与 [shell.md](shell.md)。核对 help debug、目标文件权限、进程身份和监听状态。下列为历史 debug 命令示意，只有目标实际支持时使用：

```text
debug <BIND_ADDRESS>:<PORT> <TARGET_EXEC> [arguments...]
debug --attach <BIND_ADDRESS>:<PORT> <PID>
```

启动与附加按用户调试任务选择，不另起无关进程。目标绑定地址与主机连接地址分别选择，不连接通配地址。保持服务会话存活；连接失败先查同一目标的服务与网络状态，不猜地址或扫描候选板卡。

避免为探测端口先建立测试 TCP 连接：单连接调试服务可能被它占用。优先查目标监听状态，再用实际 GDB 连接。

## 主机连接与检查

以下变量为当前任务选择的值，不是固定路径：

```text
GDB=<matching cross debugger>
PROGRAM=<matching host symbol ELF>
SYSROOT=<matching target sysroot>
SOLIB_PATH=<matching library directories>
```

用 file 等工具检查输入，运行选定的 GDB 加载 PROGRAM，再按当前服务类型选择 target remote 或 target extended-remote，不能无条件混用。GDB 命令示意：

```gdb
set pagination off
set sysroot <SYSROOT>
set solib-search-path <SOLIB_PATH>
set remotetimeout 5
target remote <TARGET_ADDRESS>:<PORT>
info threads
thread apply all bt full
info sharedlibrary
info registers
```

符号和共享库加载不完整时记录缺口。回溯或寄存器现象只提供当前停点证据，原因判断还要检查对应实现和执行顺序。需要协议日志时临时开启 set debug remote 1，查完关闭。

连接和中断可能暂停目标，附加后的查看操作也会改变运行状态；继续执行、断点、写内存和信号均按当前调试任务范围操作。

非交互调用设置合理等待上限。超时后检查本地 GDB、远端会话和目标状态，不创建重复调试服务。正常结束按实际连接模式 detach/断开并检查目标状态；不把 kill 当成清理命令。重建按项目入口执行。
