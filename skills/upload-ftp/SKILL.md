---
name: upload-ftp
description: 将当前项目的已编译文件通过 FTP 部署到用户或项目配置指定的测试设备；用于 mksh 等嵌入式命令行工具的单文件上传。
---

# FTP 上传

从当前任务或项目配置读取目标 IP、端口、远端路径和本地构建产物，不复用其他项目的 Windows 路径。缺少目标或产物时先确认，上传前检查本地文件确实存在。

脚本位于本技能目录（`<SKILL_DIR>`）下：

```text
python3 <SKILL_DIR>/ftp_upload.py --ip <IP> --user <USER> --password <PASSWORD> --local <LOCAL_PATH> --remote <REMOTE_PATH>
```

脚本兼容原测试设备的默认 `root`/`root` 账号。其他凭据按当前任务提供，不写入技能文档或日志。该脚本只上传文件，不创建远端目录，也不确认执行权限或程序运行成功。

SylixOS 目标优先使用全局 `$sylixos-ext-skill` 的 FTP 包装器；有配置端口时通过其 `--port` 传入。上传后按目标平台检查文件路径、大小和权限；只有任务已包含运行验证时才启动程序。报告传输结果和仍未验证的部分。
