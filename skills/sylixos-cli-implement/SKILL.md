---
name: sylixos-cli-implement
description: Implement approved work for the current Unix command-line SylixOS port with focused tests, target validation, review, and handoff.
---

# SylixOS CLI Implement

按用户已确认的规格、任务或明确请求实现当前 Unix 命令行工具→SylixOS 工作。没有清晰的验收条件或测试 seam 时，先补齐边界再修改代码。

## 修改前

1. 阅读当前 `AGENTS.md`、适用规则、源码、公共头文件、对应 man 手册、Makefile 和已有测试。
2. 若存在 `.codegraph/`，先用 CodeGraph 探索相关符号；同步失败时再按仓库规则处理索引。
3. 识别最小可独立验证的垂直切片，记录不应改变的命令行为、错误语义和退出状态。
4. 检查当前工作区，保留无关改动，不创建或依赖其他项目的参考工作区。

## 实现规则

- 优先复用现有兼容头文件和公共工具函数，保持平台特例集中。
- 遵循项目的 C/C++ 规范，测试外部行为和最高可用 seam。
- 不引入未经用户确认的外部依赖，不用装饰性或步骤性注释掩盖代码结构。
- 多个并行任务按文件范围隔离；集成、冲突处理、构建和同一板卡上的操作保持串行。

## 构建和验证

通过项目 Makefile 执行：

```text
make format
make config
make build
```

按任务需要执行 `make install`、`make upload` 或 `make clean`。不要绕过 Makefile 直接调用 CMake、Ninja 或编译器。构建失败时保留原始错误，先分析原因。

对受影响工具执行聚焦验证；涉及 SylixOS 系统行为时使用 `$sylixos-ext-skill` 在目标板上复核；崩溃、挂起和线程问题使用 `$sylixos-gdb`。报告每条命令、目标平台、证据和未验证项。

## 审查与交付

完成每个切片后检查差异、运行聚焦验证，并检查规范和回归风险。未获用户明确授权，不执行 Git 提交或推送。最终交付包含修改摘要、实际 Makefile/板卡命令、结果、限制和用户自测步骤。
