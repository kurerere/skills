# 板卡命令与文件传输

所有目标命令先读 [shell.md](shell.md)。目标和服务端口来自当前项目或用户；若项目提供目标测试指南，先读其目标选择部分。配置缺失时询问，不扫描网络或因失败换板。

## 选择执行入口

使用当前任务适用的已配置工具。随技能提供的 scripts/ftp_client.py 和 scripts/telnet_runner.py 仅用于 Telnet/FTP：固定 root/root 登录，每次新建连接。其他认证或服务应使用已有且适用的工具，不把额外凭据放进命令和日志。

`<SKILL_DIR>` 始终指主 SKILL.md 所在目录，而非 references 目录。先看 --help 核对选项；工具选项放在 IP 之前。

```text
python3 <SKILL_DIR>/scripts/ftp_client.py --help
python3 <SKILL_DIR>/scripts/telnet_runner.py --help
python3 <SKILL_DIR>/scripts/ftp_client.py --port <FTP_PORT> --timeout 60 <IP> upload <LOCAL_FILE> <REMOTE_FILE>
python3 <SKILL_DIR>/scripts/ftp_client.py --port <FTP_PORT> <IP> download <LOCAL_FILE> <REMOTE_FILE>
python3 <SKILL_DIR>/scripts/telnet_runner.py --port <TELNET_PORT> --timeout 90 <IP> "<COMMAND>"
```

本包装器默认 FTP 超时 10 秒；Telnet 连接、登录和提示符各 10 秒，命令输出等待 30 秒。以实际脚本和 --help 为准。FTP 失败会在内部尝试最多三次，包括上传；仅在重复同一路径传输可接受时使用，失败后检查远端是否留下部分文件。

## 执行与验证

- 一个 Telnet 调用发送一条命令。使用目标绝对路径，前一次连接的 cd 和会话状态不能当成后续连接的前提。
- FTP 不创建远端目录，上传前确认目标目录和覆盖范围。执行权限需按项目要求单独设置，并以目标 help 确认 chmod 语法，不机械修改数据文件权限。
- 上传、权限检查、运行与结果检查分开执行。传输成功还须核对目标文件大小或哈希；无目标校验工具时可下载同一文件在本地比较。
- Telnet 返回 0 仅表示包装器等到了提示符，不代表远端命令退出码为 0。输出会去除回显和提示符；为空时仍须根据预期效果判断。
- --timeout 只限制本地等待，不停止远端程序。长程序按目标支持的服务或后台机制运行，再通过新连接检查状态。
- kill、gzip、env、ll 等行为来自实际目标 help 与观察。不要把某板卡的默认信号、PID 数制或参数写法当成所有目标的规则。

加载器提示缺库时先查路径、依赖、符号、部署完整性和版本，不能据此默认删文件重新上传。覆盖、删除或重启前确认操作对象属于本任务，保留所需诊断与回滚资料。

## 失败与超时

超时、认证失败或连接中断须报告阶段。一次超时可能发生在远端已经写入或启动之后，先用只读检查确认状态，不盲目重复变更。文件传输失败时不运行部分产物。

报告选定目标、执行的传输与命令、实际输出及后续检查，分别说明传输、目标行为和产物结果。
