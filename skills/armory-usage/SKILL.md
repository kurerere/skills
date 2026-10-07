---
name: armory-usage
description: Guide packaging, sandbox verification, QEMU deployment, and release workflow for Node.js SylixOS Armory packages. Use when preparing, building, packaging, verifying, or publishing SylixOS release artifacts.
---

# Node.js SylixOS Armory 打包与发布流水线

先读取当前仓库的 `.armoryrc.json`、Makefile、发布脚本和目标配置。下面的包名、目录和脚本是 Node.js 项目的流程；只有当前仓库采用该布局时才使用。其他 SylixOS 项目按自己的发布入口执行，保留版本、ELF、根目录解包、目标运行和发布验证要求。

---

## 核心流程与门禁 (Pipeline Gates)

### Gate 1: 版本校验与元数据 (`release-check-version.sh`)
在准备发布前，校验版本号与配置元数据：
1. **语义化版本格式**：必须符合 SemVer 规范 `X.Y.Z[-pre][+build]`。移植发版推荐使用构建元数据标识日期，例如 `24.20.1+20260911`。
2. **Git Tag 碰撞校验**：检查本地与远程 `origin` 是否已存在相同 `v<version>` 标签。
3. **元数据配置**：以根目录 `.armoryrc.json` 为单一真理来源，校验 `name` 为 `@cloudnative/nodejs`，`platforms` 列出 `ARM64_GENERIC -> arm64-generic` 与 `X86_64 -> x86_64-generic`，`minSupportedVersion` 为 `SylixOS 3.6.3`。

*完成准则*：`./scripts/armory/release-check-version.sh <version>` 执行退出码为 0，无 Tag 冲突。

---

### Gate 2: 二进制剥离与 ELF 门禁 (ELF Gate)
Node.js 编译产物按平台分布在独立构建树（`scripts/sylixos/build.sh build <平台>` 产出）：
ARM64_GENERIC -> `out.arm64/Release/node`，X86_64 -> `out.x64/Release/node`：
1. **符号剥离**：使用对应架构工具链 strip 处理二进制（ARM64 候选 `aarch64-linux-gnu-strip`、`aarch64-sylixos-elf-strip`；x86-64 使用 `x86_64-sylixos-elf-strip`），将体积从约 2.0GB 未剥离体积缩减至约 88MB。
2. **架构与格式**：执行 `file` 命令验证产物架构与构建平台匹配（ARM64 为 `ELF 64-bit LSB shared object, ARM aarch64`；x86-64 为 `ELF 64-bit LSB shared object, x86-64`）且为 `stripped`。
3. **动态依赖门禁**：通过 `readelf -d` 确认 `DT_NEEDED` 仅依赖系统级库（`libvpmpdm.so`, `libcextern.so`），无未定义的宿主依赖；未定义符号集应与已实机验证产物一致（详见 `docs/agents/sylixos-build-verification.md`）。

*完成准则*：剥离后二进制位于独立 staging 目录，通过 ELF 架构与符号剥离校验。

---

### Gate 3: 制品打包与根提取沙箱校验 (`armory-package.sh`)
运行 `./scripts/armory/armory-package.sh [--platform <buildPlatform>]` 构建制品包并做根目录提取沙箱校验；不带 `--platform` 时打包 `.armoryrc.json` 列出的全部平台（每个平台须已构建）：
1. **安装路径结构**：遵循 SylixOS 标准直接解压到根目录（`untar xxx.tar.gz /`）的结构：
   - `usr/bin/node`：权限必须为 `0755` (`-rwxr-xr-x`)。
   - `usr/bin/nodejs`：软链接，指向同级 `node`。
   - 严禁包含绝对路径前缀（`/usr/...`）或当前目录点号（`./usr/...`）。
2. **沙箱解包自检**：脚本自动解压生成的 tarball 到临时沙箱目录，检查文件存在性、权限及符号链接完整性。
3. **目录归档规范**：产物统一存放在 `.armory_output/@cloudnative/nodejs/<version_branch>/`（如 `24.20`），并创建兼容软链接 `.armory_output/@cloudnative/nodejs@<version>`。
4. **规范配置生成**：同步生成包内 `armory.json`、根目录 `armory.json` 及 `README.md`；`armory.json` 的 `platforms` 数组自动聚合目标目录中当前版本的全部架构归档（重复运行向全量收敛）。
5. **CLI 规则验证**：对每个已打包架构执行 `armory platform validate SylixOS` 与 `armory arch validate <arch>`。

*完成准则*：生成 `nodejs-sylixos-arm64-generic-v<version>.tar.gz` 与 `nodejs-sylixos-x86_64-generic-v<version>.tar.gz`（各约 33MB/按架构实际体积），沙箱解包校验通过，CLI 平台与架构校验通过。

---

### Gate 4: 项目指定目标的离线安装验证 (Target Verification)
在正式发布前，先读取项目目标配置（如 `docs/agents/sylixos-test-debugging.md#1-select-the-target`），在指定的权威测试目标上完成离线安装实测。下例中的 `qemu` 只是一种远端配置名，应替换为本次选定目标：
1. **安装离线包**：
   ```bash
   armory install --from-local .armory_output/@cloudnative/nodejs/24.20/nodejs-sylixos-arm64-generic-v<version>.tar.gz -r qemu -f
   ```
2. **查看已安装清单**：
   ```bash
   armory list -r qemu
   ```
3. **运行加载测试**：
   通过 `$sylixos-ext-skill` 连接已选定目标，执行 `node -v`，确认输出预期的 Node.js 版本号，且无动态链接器符号未找到报错。

*完成准则*：选定目标上 `armory list` 列出包名，`node -v` 成功返回版本号。

---

### Gate 5: 发布门禁与进度条控制 (`armory-publish.sh`)
运行 `./scripts/armory/armory-publish.sh` 发布制品：
1. **安全确认硬规则 (Hard Guardrail)**：
   - 检查 `.armoryrc.json` 中的 `autoPublish` 字段。若为 `false`，Agent 严禁在未经用户明确指令下执行自动发布；必须由用户显式触发或传递 `--force` 参数。
2. **无头终端进度条管理**：
   - 发布前设置 `armory config set disableProgressBar=true`，避免无头/非交互终端中光标定位超时。
   - 使用 `trap ... EXIT` 保证在命令结束（无论成功或异常）后恢复 `disableProgressBar=false`。
3. **进入制品目录发布**：在 `.armory_output/@cloudnative/nodejs/<version_branch>/` 目录下执行 `armory publish`。

*完成准则*：Armory 远端报告发布成功，终端进度条配置恢复。

---

### Gate 6: 端到端流水线与回滚机制 (`release.sh`)
`./scripts/armory/release.sh <version>` 编排完整流水线，执行 **Publish-First, Commit-Last** 顺序：
1. **前置环境检查**：检查 Git 工作区无未提交改动（忽略 `.armory_output/`、`.temp/` 与 `out`、`out.*` 构建树）。
2. **版本更新与打包**：执行 `release-check-version.sh`、`release-bump-version.sh` 与 `armory-package.sh`（默认打包 `.armoryrc.json` 列出的全部平台）。
3. **自动回滚 (Rollback)**：若打包或发布环节中途失败，trap 自动还原 `.armoryrc.json` 与 `armory.json`，清理临时生成目录，保持 Git 干净。
4. **发布成功后提交**：仅当发布完全成功后，自动执行 `git commit`（提交版本更新）并创建带注释的 Git Tag `v<version>`。

*完成准则*：发布成功，Git 提交生成且工作区干净，输出后续推送到远端的命令指引。

---

## 脚本速查表

| 脚本 | 职责 | 调用示例 |
|---|---|---|
| `scripts/sylixos/build.sh` | 多架构构建树配置与增量编译（build/package/all/status/clean） | `./scripts/sylixos/build.sh all ARM64_GENERIC` |
| `scripts/armory/release-check-version.sh` | 校验 SemVer 规范与 Git Tag 是否冲突 | `./scripts/armory/release-check-version.sh 24.20.1+20260911` |
| `scripts/armory/release-bump-version.sh` | 更新 `.armoryrc.json` 中的版本号 | `./scripts/armory/release-bump-version.sh 24.20.1+20260911` |
| `scripts/armory/armory-config.sh` | 配置校验与辅助函数库 | `source scripts/armory/armory-config.sh` |
| `scripts/armory/armory-package.sh` | 二进制剥离、打包、沙箱提取自检与元数据生成（支持 `--platform`） | `./scripts/armory/armory-package.sh` |
| `scripts/armory/armory-publish.sh` | 无头环境进度条管控与发布 | `./scripts/armory/armory-publish.sh [--force]` |
| `scripts/armory/release.sh` | 全流程串联与失败回滚 | `./scripts/armory/release.sh 24.20.1+20260911` |

