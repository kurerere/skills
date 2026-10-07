---
name: sylixos-gdb
description: Current-project SylixOS ARM64 remote GDB workflow for starting or attaching to target processes, selecting matching host symbols, configuring the cross debugger, diagnosing remote connections, and collecting read-only thread and crash information. Use when Codex needs to debug ECSD, JavaScript, or another SylixOS process.
---

# SylixOS GDB

Use the host-side SylixOS cross GDB directly. Do not create helper scripts for the normal workflow.

## Runtime endpoint selection

When the current project provides it, read `docs/agents/sylixos-test-debugging.md#1-select-the-target`
(relative to the repository root) first. Unless the user selects another target,
use its declared default target and configured GDB port as the candidate
endpoint. A physical-board default must not be replaced by the secondary QEMU. The project target configuration is sufficient context; do not ask
for an address already supplied there. A configured port does not prove that
the debug server is running. Confirm the listener on that same target before
connecting, and use an explicitly selected alternative debug port when needed.

Keep concrete addresses in the project target document rather than duplicating
them in this skill. A failed connection is not a reason to switch targets.

Select the target-side bind address and debug port from the user's current command, target shell output, active board session, or the current network context. Prefer the SylixOS wildcard bind form for starting a new process when the target accepts it. Select the board address used by the host separately; never connect the host to the target-side wildcard bind address.

Before attaching, validate the selected board address and port with a bounded TCP check. If no candidate is reachable, report that the target GDB Server is unavailable. If multiple candidates are reachable, prefer the address associated with the active target session and do not choose randomly.

Keep the selected address in runtime variables only. Do not write it into this skill, project documentation, or generated configuration unless the user explicitly requests that persistence.

When a target shell is available, inspect its network state before guessing an address:

```sh
netstat -i
netstat -l -t
```

Use `netstat -i` to identify active interfaces and `netstat -l -t` to verify that the selected debug port is in `LISTEN` state after starting the target-side server.

## Select the debugger and symbols

Use this cross GDB path first:

```text
/opt/acoinfo/realevo-stream/compiler/aarch64-sylixos-toolchain/bin/aarch64-sylixos-elf-gdb
```

If it is missing or not executable, run:

```sh
which aarch64-sylixos-elf-gdb
```

Use the discovered executable only after checking that it is the SylixOS AArch64 toolchain GDB. Never silently substitute the host `/usr/bin/gdb`.

Keep two paths distinct:

```text
TARGET_EXEC      executable path used by SylixOS
HOST_SYMBOL_ELF  matching unstripped ELF used by host GDB
```

Choose `HOST_SYMBOL_ELF` in this order:

1. Use an explicitly supplied matching ELF.
2. Search `build-sylixos/` first for the unstripped target artifact.
3. Search other known unstripped build artifacts.
4. Stop source-level debugging if no trustworthy unstripped match exists.

Treat `install-sylixos/` as the deployment tree. Files uploaded from it are normally stripped and are intended to run on the target, not to provide host-side symbols. Use the deployment file to identify `TARGET_EXEC` and verify the deployed layout, but use the corresponding unstripped file from `build-sylixos/` as `HOST_SYMBOL_ELF`. If only the stripped deployment file is available, allow low-level remote inspection only and report that source symbols are unavailable.

Verify the selected ELF with `file`; require AArch64, SylixOS-compatible ABI, and debug information. Compare size and `sha256sum` when both target and host copies are available. Do not infer a match from the basename alone.

For the JavaScript runtime, use the matching local runtime ELF under the sibling `grpcjs-stream` workspace when it is the target binary. For ECSD, use the matching unstripped artifact from the current project's build output or the user-specified deployment artifact.

## Configure the target-side GDB Server

Start a new target process with the runtime-selected bind address and port:

```sh
debug <BIND_ADDRESS>:<PORT> <TARGET_EXEC> [arguments...]
```

Use the target's wildcard bind address for the normal launch flow when supported. Preserve arguments exactly as supplied by the user; do not invent arguments.

Before starting it, verify that the target file exists and is executable:

```sh
ll <TARGET_EXEC>
```

Require execute permission on the target file. If the file came from `install-sylixos/`, treat it as a deployment artifact and keep using the corresponding unstripped `build-sylixos/` file on the host for symbols.

Attach to an existing target process only when requested:

```sh
debug --attach <BIND_ADDRESS>:<PORT> <PID>
```

Obtain and verify the actual PID from the target shell:

```sh
ps
cat /proc/<PID>/cmdline
ls -l /proc/<PID>/exe
```

Do not assume a sample PID from a manual. Keep the target shell or its background debug task alive until the host GDB connects.

Wait for the target-side GDB Server to report that it is waiting for a connection before starting host GDB. A refused connection normally means that the target command has not started, exited, or is listening on another port.

Use `gdbaddsym` only for the separate JTAG symbol-command workflow. It is not a replacement for the network GDB Server started by `debug`.

## Configure sysroot and shared libraries

Discover the paths from the current project and filesystem before starting GDB. Prefer these known project locations when they exist:

```text
SYSROOT=/home/wangjijie/workspace/.realevo/arch/ARM64_GENERIC/rootfs
JS_SYMBOL_DIR=/home/wangjijie/workspace/grpcjs-stream/.temp
SYSROOT_LIB=/home/wangjijie/workspace/.realevo/arch/ARM64_GENERIC/rootfs/lib
SYSROOT_USR_LIB=/home/wangjijie/workspace/.realevo/arch/ARM64_GENERIC/rootfs/usr/lib
```

Do not use a missing directory silently. If the expected sysroot or library directories are absent, inspect current project configuration and toolchain locations, then report the selected replacements.

## Connect from the host

Set runtime variables before running the checks:

```text
GDB=<selected aarch64-sylixos-elf-gdb>
PROGRAM=<matching HOST_SYMBOL_ELF>
TARGET_ADDRESS=<selected board address>
PORT=<selected debug port>
SYSROOT=<selected sysroot>
SOLIB_PATH=<selected runtime library directories separated by colons>
```

Check the local inputs:

```sh
test -x "$GDB"
file "$PROGRAM"
test -d "$SYSROOT"
```

Check the selected target endpoint without changing target state:

```sh
timeout 3 bash -c 'cat < /dev/null > /dev/tcp/$0/$1' "$TARGET_ADDRESS" "$PORT"
```

Start an interactive session:

```sh
"$GDB" -q "$PROGRAM"
```

Run the following GDB commands, substituting the runtime-selected values:

```gdb
set pagination off
set sysroot <SYSROOT>
set solib-search-path <SOLIB_PATH>
set remotetimeout 5
target remote <TARGET_ADDRESS>:<PORT>
info threads
thread apply all bt
info sharedlibrary
```

Use `set debug remote 1` only to diagnose a remote protocol handshake. Disable it for ordinary sessions to avoid noisy packet logs.

Use a bounded `timeout` for non-interactive checks. Capture GDB output and the exit code; do not allow a failed remote connection to hang the agent indefinitely.

## Perform read-only diagnostics

After a successful connection:

- Use `info threads` and `thread apply all bt full` to inspect all threads.
- Use `bt full`, `info registers`, and `info sharedlibrary` for crashes or abnormal stops.
- Set source breakpoints only after verifying that the host source tree matches the selected ELF.
- Use `info breakpoints` to verify installed breakpoints.
- Use `continue`, memory writes, and other target-mutating actions only after the user explicitly requests them.

When the user explicitly ends an attached session, use `detach` to release the target process. Never use `kill` as normal cleanup.

## Respect project constraints

Use CodeGraph exploration as required by the repository `AGENTS.md`.

If rebuilding is necessary, use only the project Makefile targets `make format`, `make config`, and `make build`. Do not invoke CMake, Ninja, or the compiler directly. Report the actual Makefile commands and results.

Support SylixOS ARM64 only. Do not run the target program or its tests on Linux or another host platform.

Do not commit or push skill, debugger, or configuration changes without explicit user approval.
