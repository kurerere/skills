---
name: sylixos-porting
description: 将 C/C++ 库、命令行工具或运行时移植到 SylixOS，处理平台基线、API 差异、构建链接和运行行为；按当前项目和 SDK 选择适用的移植经验。
---

# SylixOS 移植

先读取当前项目约定、相关源码、构建配置和测试，确认目标架构、SDK、系统版本与运行环境。构建命令、板卡地址、路径和验收条件来自当前项目或用户配置。

## 通用要求

- 明确需要保持的上游行为和允许的平台差异。命令行工具保持参数、输出、错误语义与退出状态；库保持接口契约和资源生命周期。
- 根据当前 SDK 头文件、实现和目标行为选择 FreeBSD、Linux、POSIX 或 RTOS 基线，不仅凭接口名称判定兼容。
- 平台差异集中到既有兼容层或最小平台分支，复用公共函数，保留其他平台行为。
- 故障先复现并定位失败接口。历史方案只有在失败特征和适用前提一致时才能使用。
- 使用项目已有构建入口。链接与部署时检查架构、ABI、动态依赖和未解析符号，执行项目已有的 ELF 检查。
- 验证正常、错误和边界行为。系统调用、文件系统、信号、进程、网络和终端行为须在指定 SylixOS 目标复核；主机测试不能替代目标验证。

板卡传输和命令执行使用 `$sylixos-ext-skill`；远程调试使用 `$sylixos-gdb`，先确认架构和工具链适用。交付时报告实际验证结果、未验证项和环境限制。

## 专项经验

按问题选择以下参考。Node、GYP、V8、libuv 的记录只用于相应组件，其构建命令、路径和验证要求不套用到其他项目。

- Baseline selection (FreeBSD/Linux/POSIX/RTOS) or platform API diffs (`epoll`, `kqueue`, `optarg`, `SCHED_OTHER`, file locks, memory mapping): read
  [references/platform-baseline.md](references/platform-baseline.md).
- Build configuration, incremental rebuilds, or loader/link symbols: read
  [references/build-and-link.md](references/build-and-link.md).
- V8 platform memory, CodeRange, or ARM64 JIT addressability: read
  [references/v8.md](references/v8.md).
- libuv socket nonblocking or connect completion: read
  [references/libuv-network.md](references/libuv-network.md).
- Node startup, background-thread teardown, or exit-code preservation: read
  [references/runtime-lifecycle.md](references/runtime-lifecycle.md).

## 使用和维护经验

应用方案前复现记录中的失败特征，核对当前源码、SDK 和目标满足其前提。执行方案对应的验证及当前项目的回归检查；不满足前提时重新诊断。

新增经验须记录修复前的复现条件、改动范围、目标验证结果、相关回归结果和适用版本。未解决故障和临时绕过留在当前项目的诊断文档，不能作为已验证方案。

## Current exclusions

The accelerated OpenSSL/TLS crash, no-assembly workaround, TTY read cancellation,
spawn/`cwd`, cluster/IPC convergence, debugger residual processes, intermittent
heap aborts, UDP `SO_REUSEPORT` selection, and TCP/HTTP vector-write CPU behavior
are unresolved evidence. Use the current project’s diagnostic guide for them rather than treating
them as recipes.
