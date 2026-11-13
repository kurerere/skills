---
name: sylixos
description: SylixOS 及 ECS、JSRE、VSOA、RealEvo-Stream、Armory 相关任务：查询手册、移植程序、操作板卡、远程调试、工程构建与制品管理；按任务加载对应参考。
---

# SylixOS

先确定用户要查询、修改、构建、部署还是调试，读取当前项目约定。目标、架构、SDK、工具链、构建入口和操作范围来自当前任务与项目配置；缺少必需信息时再询问。具体流程按下表读取，不将各分支串成固定流水线。

## 按任务读取

| 任务 | 参考 |
| --- | --- |
| SylixOS 编程/API/Shell、系统配置，ECS、JSRE、VSOA 或 Armory 手册 | [在线优先的文档查询](references/docs.md) |
| C/C++ 库、命令行工具和运行时移植，平台差异与兼容性审查 | [移植](references/porting.md)，再按问题读取其中专项 |
| 发送目标命令、传输文件、部署或运行程序 | [板卡操作](references/board-operations.md) |
| 编写目标命令、startup.sh、shfile 或 system/popen 命令字符串 | [目标 Shell](references/shell.md)，操作板卡时也必须读取 |
| 远程 GDB、符号匹配、线程与崩溃诊断 | [调试](references/gdb.md)，目标侧命令另读板卡与 Shell 参考 |
| 板子启动失败、SD 启动盘与启动分区文件系统排查修复 | [启动介质](references/boot-media.md) |
| RealEvo-Stream 工作空间、工程、设备、构建与部署 | [RealEvo-Stream](references/realevo-stream.md) |
| Armory 制品打包、安装验证或发布 | [Armory](references/armory.md) |

查询手册只执行查询。跨分支任务读取涉及的参考，复用已确定的目标配置。对虚拟机内的目标命令也按板卡与 Shell 参考执行；虚拟机生命周期与网络配置以当前项目提供的工具和约定为准。

## 共同约束

- 当前源码、SDK、配置和目标结果用于判定适用性；历史经验与手册版本不能替代当前证据。
- 操作限于用户任务和已有授权范围，不因读取此技能自行部署、发布、安装 SDK 或修改全局配置。
- 不默认切换目标、套用另一项目的构建命令或持久化凭据。超时代表结果未知，先检查状态再判断是否可重试。
- 区分传输完成、构建通过、目标运行和回归覆盖。报告实际结果及未验证项，阶段结论只对实测过的范围成立。

## 本地资源

`<SKILL_DIR>` 为本文件所在目录；本技能的 FTP/Telnet 工具和 FAT32 启动分区检查脚本位于 `scripts/`，使用前读对应参考和 `--help`。

产品手册和 RealEvo 原适配器留在技能之外。`<DATA_ROOT>` 使用 `AGENTS_SKILL_DATA_DIR`，未设置时为 `~/.agents/skill-data`。既有数据目录保持原名；技能安装和更新不迁移或覆盖这些资料。安装此技能不会安装 IDE、SDK、调试器或手册。
