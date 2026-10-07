# 来源与整理说明

当前版本整理自个人全局技能，以及 `_mksh`、`ecsd++`、`ecsd2`、`sbase`、`cmd_relic`、Node 等工作区中的自定义技能。

- 全局已维护的个人技能作为基线，保留自写脚本与个人移植经验；底层产品手册在本地单独存放。
- 项目 `jsre-api` 与全局版本的主要差异是旧链接格式；采用全局修正过的版本。
- 中文提交技能采用全局 `commit`，补充尊重用户已选暂存范围的规则。旧 `git-commit` 的自动暂存所有改动、模型署名，以及 `ecsd-commit` 的固定正文要求不再复制。
- `win-host-build` 采用 sbase/cmd_relic 中读取当前连接配置的版本。旧 ECSD 固定路径不再用作跨项目默认值。
- ECSD 保留 VSOA/CRI 基线、Makefile 构建和板卡验证约定。依赖已停用的 Matt 编码技能的地方，改为直接描述所需行为。
- sbase/cmd_relic 的命令行工具流程单独命名为 `sylixos-cli-workflow`、`sylixos-cli-implement`。
- `codex-teamwork` 保留用户明确调用、协调者分工和计划批准要求；移除不可用的固定模型名称，使用当前环境可用模型。
- `deep-consensus` 合并多个项目中的同一份自定义讨论流程，使用当前环境的代理工具与模型，保留独立分析、综合、审查和验证要求，移除“零 Bug”的保证。
- `sylixos-socket-porting` 保留原移植记录，补充适用条件，禁止仅凭数值把内核错误当成连接拒绝。
- `upload-ftp` 保留上传脚本，移除某个 mksh 工程的固定 Windows 产物路径。
- Armory 和 GDB 的目标选择以当前项目配置为准，避免全局技能中的 QEMU 示例覆盖实板默认值。

Matt 技能的不同版本、标点或排版差异不作为个人技能重复发布。飞书、Impeccable、Archify、shadcn 等第三方技能继续保留其安装来源。

`*-docs`、`jsre-api` 只发布个人检索入口，原 SylixOS、ECS、Armory、VSOA、JSRE 手册切片不进入 Git 仓库。运行示例使用文档地址，不发布原有内网端点。

RealEvo-Stream 的完整接口说明与原工具适配器也留在本机，公开仓库只维护个人任务路由入口。
