# 来源与整理说明

当前版本整理自个人全局技能，以及 `_mksh`、`ecsd++`、`ecsd2`、`sbase`、`cmd_relic`、Node 等工作区中的自定义技能。

- 全局已维护的个人技能作为基线，保留自写脚本与个人移植经验；底层产品手册在本地单独存放。
- 项目 `jsre-api` 与全局版本的主要差异是旧链接格式；采用全局修正过的版本。
- 中文提交技能采用全局 `commit`，补充尊重用户已选暂存范围的规则。旧 `git-commit` 的自动暂存所有改动、模型署名，以及 `ecsd-commit` 的固定正文要求不再复制。
- sbase/cmd_relic 的命令行工具流程单独命名为 `sylixos-porting`。
- `sylixos-socket-porting` 保留原移植记录，补充适用条件，禁止仅凭数值把内核错误当成连接拒绝。
- Armory 和 GDB 的目标选择以当前项目配置为准，避免全局技能中的 QEMU 示例覆盖实板默认值。

Matt 技能的不同版本、标点或排版差异不作为个人技能重复发布。飞书、Impeccable、Archify、shadcn 等第三方技能继续保留其安装来源。

`*-docs`、`jsre-api` 只发布个人检索入口，原 SylixOS、ECS、Armory、VSOA、JSRE 手册切片不进入 Git 仓库。运行示例使用文档地址，不发布原有内网端点。

RealEvo-Stream 的完整接口说明与原工具适配器也留在本机，公开仓库只维护个人任务路由入口。

Armory 使用技能改名为 `armory-usage`；CLI 规划与实现技能合并到 `sylixos-porting`，保留兼容层、构建、目标验证和交付约定。

Armory 手册检索入口并入 `armory-usage`；SylixOS 编程与系统使用手册入口合并为 `sylixos-usage`，本机资料保持原有章节和索引。

`rag-smart-qa` 是第三方技能，来源为本地 Hermes（AcoPilot 内置）技能库，不在本仓库维护；已安装的全局版本保留。

需求完善技能 `features-full` 改名为 `refine-requirements`，用于创建或补全需求，保留用户手动调用方式。
