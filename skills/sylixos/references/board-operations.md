# 板卡命令与文件传输

发送目标命令前先读 [shell.md](shell.md)。纯 FTP 操作只需本页。目标和服务端口来自当前项目或用户；若项目提供目标测试指南，先读其目标选择部分。配置缺失时询问，不扫描网络或因失败换板。

## 选择执行入口

使用当前任务适用的已配置工具。随技能提供的 scripts/ftp_client.py 和 scripts/telnet_runner.py 仅用于 Telnet/FTP，每次新建连接。默认以 root/root 登录；目标改过账号时用 `--user <USER>` 或环境变量 `SYLIXOS_USER` 指定用户，密码只从环境变量 `SYLIXOS_PASSWORD` 读取，不写进命令行、日志或报告。其他认证方式或服务使用已有且适用的工具。

`<SKILL_DIR>` 指主 SKILL.md 所在目录。下例是参数形状：用主机可用的 Python 3，替换占位符，按主机 Shell 规则引用路径和目标命令，有参数列表接口时优先用它。全局选项放在 IP 之前；已确认脚本版本和参数后直接复用，有疑问时查看相应 `--help`。FTP 在 IP 后只选一个子命令。

```text
python3 <SKILL_DIR>/scripts/ftp_client.py --port <FTP_PORT> --timeout 60 <IP> upload <LOCAL_FILE> <REMOTE_FILE>
python3 <SKILL_DIR>/scripts/ftp_client.py <IP> upload --verify <LOCAL_FILE> <REMOTE_FILE>
python3 <SKILL_DIR>/scripts/ftp_client.py <IP> upload --progress --verify <LOCAL_FILE> <REMOTE_FILE>
python3 <SKILL_DIR>/scripts/ftp_client.py --port <FTP_PORT> <IP> download <LOCAL_FILE> <REMOTE_FILE>
python3 <SKILL_DIR>/scripts/ftp_client.py <IP> download --progress <LOCAL_FILE> <REMOTE_FILE>
python3 <SKILL_DIR>/scripts/ftp_client.py <IP> list <REMOTE_PATH>
python3 <SKILL_DIR>/scripts/ftp_client.py <IP> rmtree [--contents-only] <REMOTE_DIR>
python3 <SKILL_DIR>/scripts/ftp_client.py <IP> rmtree --dry-run [--contents-only] <REMOTE_DIR>
python3 <SKILL_DIR>/scripts/telnet_runner.py --ttinyshell --port <TELNET_PORT> --timeout 90 <IP> "<COMMAND>"
python3 <SKILL_DIR>/scripts/telnet_runner.py --ttinyshell --log-only --output <LOCAL_LOG> --timeout 90 <IP> "<COMMAND>"
```

其他 FTP 子命令 `size`、`mkdir`、`delete`、`rmdir` 同样各取一个远端路径。FTP 默认超时 10 秒；Telnet 连接、每个登录提示和 Shell 提示各 10 秒，命令输出等待 30 秒。FTP 的 upload、download、list、size、mkdir 仅对暂时性网络错误、连接中断和 FTP 4xx 最多尝试三次，每次使用新连接，间隔 1 秒；认证失败、FTP 5xx、本地文件错误和校验不一致直接失败。upload 可能重传同一路径，仅在允许覆盖时使用，失败后检查远端是否留下部分文件。delete、rmdir、rmtree 只尝试一次；rmtree 中途失败后可检查剩余内容，再决定是否重新执行。

## 执行与验证

- 一个 Telnet 调用发送一条物理单行命令，作为一个主机参数传递，以保留供目标解析的引号。每次调用独立成会话，命令内使用目标绝对路径。空命令和实际控制字符在打开连接和日志文件前拒绝；`--ttinyshell` 额外拦截常见 Bash 写法，不验证目标命令是否存在或适用。
- upload 不创建远端目录，上传前用 mkdir 准备目录（自动创建缺失的父目录），并确认覆盖范围。执行权限需按项目要求单独设置，并以目标 help 确认 chmod 语法，不机械修改数据文件权限。
- 上传、权限检查、运行与结果检查分开执行。传输成功后核对目标文件大小或哈希：已知文件路径时用 `size` 直接查字节数，无需列目录；复用 `upload --verify` 的回读结果，或下载后在主机比较已有文件。
- upload --verify 在同一连接中回读远端文件，比较上传字节与回读字节的 SHA-256；无需板卡哈希命令，会增加一次完整下载流量。校验不一致直接失败；回读错误按上述分类决定是否重新上传。失败不自动删除远端文件，可能留下已上传但未验证的文件。
- upload/download 的 --progress 将字节数、耗时和平均 MiB/s 写到 stderr，传输期间最多每 0.5 秒刷新一次，结束或失败时再报告一次；stdout 保留操作结果。可与 --verify 组合，分别显示上传和校验回读进度。下载端不支持 SIZE 时仅报告已传字节，不显示百分比。默认不开启进度，两种模式均使用 64 KiB 传输块。
- Telnet 返回 0 只表示包装器识别到了提示符；远端命令成败按输出另行判断。登录后学习完整提示符；`[用户@主机:路径]#` 格式允许路径变化，其他格式按登录时的完整文本识别。普通输出末尾的 `#` 或 `=>` 不算结束标志；程序原样输出与完整提示符相同的内容时，文本上与真实提示符无法区分。
- Telnet 移除识别出的首行回显和末尾提示符，保留输出空白与无换行尾部，CRLF 规范化为 LF。默认收完再打印，超过 1 MiB 的暂存输出写入本机临时文件；`--stream` 边收边打印并刷新。`--output` 同时保存到指定本地 UTF-8 文件（覆盖已有文件）。长日志用 `--log-only --output <LOCAL_LOG>`，在主机只查所需片段；该模式不把命令输出写到 stdout，不能与 `--stream` 合用，错误仍写 stderr。输出文件不含登录信息和本机错误诊断。
- --timeout 是命令输出的总等待上限，持续有输出也不会延长；它不停止远端程序。Telnet 真正超时返回 2，连接关闭或接收错误返回 1，诊断指出发生阶段；已收到的输出仍打印和保存，远端命令结果标记为未知。
- 需要断线后仍保留完整日志时，按目标支持的服务或后台机制运行，并在命令末尾加 `8>/绝对路径/out.txt` 合并 stdout/stderr 写入板卡文件，再用 FTP 下载。--output 只能保存本机已收到的内容。`8>` 在 3.6.5、3.9.0 板实测可用，`2>&1` 报 `can not process redirect`。
- 目标 Shell 没有递归删除命令时用 rmtree；--contents-only 清空目录但保留目录本身。--dry-run 遍历并列出计划删除的文件和目录，不发送 DELE/RMD；可与 --contents-only 组合。预览和实际删除分属两次调用，目录内容可能在其间变化。
- 远端路径必须是绝对路径，重复斜杠和 `..` 先规范化；仅 list 允许 `/`，其他命令拒绝根目录及其等价写法。list / 可浏览根目录。
- 目录不存在或读取失败须报错；NLST 返回 550 时，仅在目录可进入且 LIST 成功返回零行后按空目录处理，不把任意 550 当成空目录。
- SylixOS FTP 对 DELE 回复 257 而非标准的 250，脚本接受任意 2xx 回复，自行写 ftplib 时不要用 delete()/rmd()。
- kill、gzip、env、ll 等行为来自实际目标 help 与观察。不要把某板卡的默认信号、PID 数制或参数写法当成所有目标的规则。

加载器提示缺库时先查路径、依赖、符号、部署完整性和版本，定位原因再处理，不默认删文件重传。覆盖、删除或重启前确认操作对象属于本任务，保留所需诊断与回滚资料。

## 失败与超时

超时、认证失败或连接中断须报告阶段。一次超时可能发生在远端已经写入或启动之后，先用只读检查确认状态，不盲目重复变更。文件传输失败时不运行部分产物。

报告选定目标、执行的传输与命令、实际输出及后续检查，分别说明传输、目标行为和产物结果。
