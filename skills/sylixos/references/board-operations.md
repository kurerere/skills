# 板卡命令与文件传输

所有目标命令先读 [shell.md](shell.md)。目标和服务端口来自当前项目或用户；若项目提供目标测试指南，先读其目标选择部分。配置缺失时询问，不扫描网络或因失败换板。

## 选择执行入口

使用当前任务适用的已配置工具。随技能提供的 scripts/ftp_client.py 和 scripts/telnet_runner.py 仅用于 Telnet/FTP：固定 root/root 登录，每次新建连接。其他认证或服务应使用已有且适用的工具，不把额外凭据放进命令和日志。

`<SKILL_DIR>` 始终指主 SKILL.md 所在目录，而非 references 目录。先看 --help 核对选项；工具选项放在 IP 之前。

```text
python3 <SKILL_DIR>/scripts/ftp_client.py --help
python3 <SKILL_DIR>/scripts/telnet_runner.py --help
python3 <SKILL_DIR>/scripts/ftp_client.py --port <FTP_PORT> --timeout 60 <IP> upload <LOCAL_FILE> <REMOTE_FILE>
python3 <SKILL_DIR>/scripts/ftp_client.py <IP> upload --verify <LOCAL_FILE> <REMOTE_FILE>
python3 <SKILL_DIR>/scripts/ftp_client.py --port <FTP_PORT> <IP> download <LOCAL_FILE> <REMOTE_FILE>
python3 <SKILL_DIR>/scripts/ftp_client.py <IP> list|size|mkdir|delete|rmdir <REMOTE_PATH>
python3 <SKILL_DIR>/scripts/ftp_client.py <IP> rmtree [--contents-only] <REMOTE_DIR>
python3 <SKILL_DIR>/scripts/ftp_client.py <IP> rmtree --dry-run [--contents-only] <REMOTE_DIR>
python3 <SKILL_DIR>/scripts/telnet_runner.py --port <TELNET_PORT> --timeout 90 <IP> "<COMMAND>"
```

本包装器默认 FTP 超时 10 秒；Telnet 连接、登录和提示符各 10 秒，命令输出等待 30 秒。以实际脚本和 --help 为准。upload、download、list、size、mkdir 失败会在内部尝试最多三次，包括上传；仅在重复同一路径传输可接受时使用，失败后检查远端是否留下部分文件。delete、rmdir、rmtree 只尝试一次；rmtree 中途失败后可重新执行，会按剩余内容继续删除。

## 执行与验证

- 一个 Telnet 调用发送一条命令。使用目标绝对路径，前一次连接的 cd 和会话状态不能当成后续连接的前提。
- upload 不创建远端目录，上传前用 mkdir 准备目录（自动创建缺失的父目录），并确认覆盖范围。执行权限需按项目要求单独设置，并以目标 help 确认 chmod 语法，不机械修改数据文件权限。
- 上传、权限检查、运行与结果检查分开执行。传输成功还须核对目标文件大小或哈希：size 输出远端字节数；无目标校验工具时可下载同一文件在本地比较。
- upload --verify 在同一连接中回读远端文件，比较上传字节与回读字节的 SHA-256；无需板卡哈希命令，会增加一次完整下载流量。回读失败或哈希不一致按上传失败处理，遵循现有最多三次尝试规则；失败不自动删除远端文件，可能留下已上传但未验证的文件。
- Telnet 返回 0 仅表示包装器等到了提示符，不代表远端命令退出码为 0。输出会去除回显和提示符；为空时仍须根据预期效果判断。
- --timeout 只限制本地等待，不停止远端程序。长程序按目标支持的服务或后台机制运行，再通过新连接检查状态。需要其输出时在命令末尾加 `8>/绝对路径/out.txt` 合并 stdout/stderr 写文件，再用 FTP 下载读取，否则包装器超时后输出丢失（3.6.5、3.9.0 板实测；`2>&1` 报 `can not process redirect`）。
- 目标 Shell 没有递归删除命令时用 rmtree；--contents-only 清空目录但保留目录本身。--dry-run 遍历并列出计划删除的文件和目录，不发送 DELE/RMD；可与 --contents-only 组合。预览和实际删除分属两次调用，目录内容可能在其间变化。
- 远端路径必须是绝对路径，重复斜杠和 `..` 先规范化；仅 list 允许 `/`，其他命令拒绝根目录及其等价写法。list / 可浏览根目录。
- 目录不存在或读取失败须报错；NLST 返回 550 时，仅在目录可进入且 LIST 成功返回零行后按空目录处理，不把任意 550 当成空目录。
- SylixOS FTP 对 DELE 回复 257 而非标准的 250，脚本接受任意 2xx 回复，自行写 ftplib 时不要用 delete()/rmd()。
- kill、gzip、env、ll 等行为来自实际目标 help 与观察。不要把某板卡的默认信号、PID 数制或参数写法当成所有目标的规则。

加载器提示缺库时先查路径、依赖、符号、部署完整性和版本，不能据此默认删文件重新上传。覆盖、删除或重启前确认操作对象属于本任务，保留所需诊断与回滚资料。

## 失败与超时

超时、认证失败或连接中断须报告阶段。一次超时可能发生在远端已经写入或启动之后，先用只读检查确认状态，不盲目重复变更。文件传输失败时不运行部分产物。

报告选定目标、执行的传输与命令、实际输出及后续检查，分别说明传输、目标行为和产物结果。
