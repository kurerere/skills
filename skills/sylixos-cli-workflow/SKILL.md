---
name: sylixos-cli-workflow
description: Coordinate feature, bug, refactor, SylixOS board validation, and delivery work for the current Unix command-line port.
---

# SylixOS CLI Development Workflow

本技能用于当前 Unix 命令行工具 移植任务的规划、实现、验证和交付。保留用户改动，按证据推进，每个阶段都必须有可检查的完成条件。

## 任务分流

- 新功能或行为变更：先明确目标、边界、不应改变的行为和验收条件，再拆分为可独立验证的垂直切片。
- Bug、崩溃、挂起或性能回退：先复现并收集证据，定位根因，提出修复方案和回归测试，再实现修复。
- 接口、模块或重构：先明确职责边界、依赖方向和外部行为测试 seam，再修改实现。
- 纯文档或机械改动：说明跳过的分析与测试，并验证引用和格式。

## 代码与平台

1. 阅读当前仓库的 `AGENTS.md`、受影响工具的源码、对应 `.1` 手册、公共头文件和 Makefile。
2. 如果根目录存在 `.codegraph/`，先用 CodeGraph 定位符号和调用关系；否则使用仓库布局和构建文件。
3. 保持 Unix/POSIX 行为和 SylixOS 适配分层；平台差异集中在兼容边界，不散落到每个命令。
4. C/C++ 修改遵循项目的 C/C++ 规范；测试外部行为，不为测试暴露内部实现。

## 构建与板卡验证

构建只使用仓库 Makefile：

```text
make format
make config
make build
```

需要安装或部署时，再按任务执行 `make install` 或 `make upload`。板卡传输和命令执行遵循 `$sylixos-ext-skill`，崩溃和线程诊断遵循 `$sylixos-gdb`。目标地址、端口、设备路径和凭据只从当前任务上下文读取。

验证至少覆盖受影响命令的正常、错误、边界行为；涉及系统调用、文件系统、信号、进程、网络或终端时，在 SylixOS 目标上复核。完成条件是实际命令、目标平台、结果和未验证部分均已记录。

## 交付

- 检查变更范围和文档一致性，报告已完成项、风险、限制和回滚方式。
- 未经用户明确同意，不执行 `git add`、`git commit` 或 `git push`。
- 用户自测需要时，给出准备条件、命令、预期结果和失败时应收集的日志。
