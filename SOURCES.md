# 来源与整理说明

个人技能整理自全局安装，以及 `_mksh`、`ecsd++`、`ecsd2`、`sbase`、`cmd_relic`、Node 等工作区中的自定义内容。

- `sylixos` 合并原 `ecs-docs`、`jsre-api`、`sylixos-usage`、`vsoa-docs`、`realevo-stream`、`sylixos-ext-skill`、`sylixos-gdb`、`sylixos-porting`、`armory-usage`。主入口路由到专项参考，FTP/Telnet 自写脚本原样迁移。
- 底层 SylixOS、ECS、JSRE、VSOA、Armory 手册，以及 RealEvo 原适配器不进入公开仓库，原本地资料目录和许可信息保留。
- Node/V8/libuv 和 sbase/cmd_relic 的移植记录缺少随包发布的完整版本与原始验证资料，作为历史调查线索维护；不能据此声称当前方案已验证。
- GDB、Shell 和 Armory 的项目特例改为有条件的参考。当前项目负责目标地址、架构、构建命令、产物布局与验收标准。
- `qemu-sylixos-ecs-usage` 保持独立，虚拟机管理内容和资源未改动。
- 中文提交技能采用个人 `commit`，尊重用户已选暂存范围；不保留旧技能的模型署名或固定正文要求。
- 需求完善技能 `features-full` 改名为 `refine-requirements`，用于创建或补全需求，保持手动调用。

Matt、飞书、Impeccable、Archify、shadcn 等第三方原版继续从原来源安装，不重复发布。`rag-smart-qa` 来源为本地 Hermes（AcoPilot 内置）技能库，不在本仓库维护，已安装的全局版本保留。
