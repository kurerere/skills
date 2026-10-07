---
name: win-host-build
description: Build or deploy the current SylixOS project from a Windows host through an explicitly configured SSH workspace.
disable-model-invocation: true
---

# Windows Host SSH Remote Build

Use this skill when compiling or deploying the project via SSH from a Windows host environment.

## Connection & Directory
- Read the SSH host, port, account, and remote workspace from the current task or local configuration.

先读取远程仓库的 `AGENTS.md` 和构建入口。下列 Make 目标适用于采用这些约定的项目；其他项目使用自己的构建入口，不照搬 ECSD 的命令。远程目录必须对应当前项目。

## Make Targets & Usage
- `make clean`: Clear build cache and artifacts.
- `make config`: Run CMake toolchain configuration.
- `make build`: Compile SylixOS platform binary.
- `make upload`: Deploy compiled binaries to the target board.
- `make`: Default incremental compilation.

## Build Rules

1. **CMake Re-configuration (`make config`)**:
   - Run `make config` followed by `make` (or `make build`) when:
     - `CMakeLists.txt` or CMake configuration files are modified.
     - Source files are added, moved, or deleted.
     - Toolchain settings, macros, or build options change.
     - Build directory is missing or uninitialized.
   - Otherwise, directly execute `make` or `make build`.

2. **Execution Strategy**:
   Always execute remote build tasks as single-line non-interactive SSH commands, substituting the runtime connection and workspace values:
   ```bash
   ssh -p <PORT> <USER>@<HOST> "cd <REMOTE_WORKSPACE> && make config && make"
   ```

3. **Board Upload**:
   ```bash
   ssh -p <PORT> <USER>@<HOST> "cd <REMOTE_WORKSPACE> && make upload"
   ```
