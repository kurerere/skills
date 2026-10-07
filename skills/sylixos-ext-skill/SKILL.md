---
name: sylixos-ext-skill
description: Use when the user wants to execute commands, transfer files (upload/download), or run programs on a SylixOS target, including QEMU, or when writing any command string for SylixOS (Telnet/serial, /etc/startup.sh, scripts, system()/popen()). Covers the ttinyShell command grammar. Mentions of 'run on board', 'telnet', 'upload to board', 'sylixos shell', 'startup.sh'.
---

# SylixOS board operations

Use this skill for SylixOS targets, including the project's ECS QEMU. The bundled wrappers use Telnet and FTP; SSH and SCP are not part of this workflow.

The wrappers authenticate as `root`/`root` and create a new connection for every invocation. Telnet and FTP use conservative defaults, with explicit timeout overrides for slow commands or large transfers. Do not describe them as a secure or persistent remote shell. Do not put additional credentials in command arguments or logs. If the board uses different credentials, stop and ask before changing the wrapper or choosing another transport.

## Operating rules

- Never guess an address or silently target another board. Reuse an IP explicitly provided in the current task or repository configuration; otherwise ask the user for the target IP.
- Run wrapper commands from the repository root, or resolve the wrapper path to an absolute path first.
- Use absolute paths on the board whenever possible. A `cd` or process started by one Telnet invocation is not available to the next invocation. Treat environment settings the same way unless the target shell has been verified to retain them.
- Issue one board command per Telnet invocation. Treat pipes, command chaining, command substitution, and shell scripts as unsupported unless the board has been explicitly verified to support them. Fetch unfiltered output and process it locally.
- Do not assume a local wrapper exit code proves that the remote command succeeded. `telnet_runner.py` does not receive the remote exit status; verify the expected effect with a separate, preferably read-only, command.
- Treat a connection or read timeout as an unknown result. Do not blindly repeat a state-changing command unless it is idempotent or the user has approved the retry.
- For a foreground command that may run longer than the default Telnet read timeout, pass `--timeout` explicitly. For a genuinely long-running program, use the board's known background/service mechanism and verify it separately with a new command.

## ttinyShell command grammar (mandatory)

Every command string sent to a SylixOS target — Telnet invocations, `/etc/startup.sh`, any `.sh` executed with `shfile`, and `system()`/`popen()` arguments in code — is parsed by ttinyShell, a kernel-resident command module, not a POSIX shell. Formulate every command with the rules below; do not borrow bash syntax.

- One command per line; arguments are separated by spaces. Quote arguments containing spaces with double quotes (`cmd "arg with space"`); the quotes are removed by the shell.
- `${VAR}` expands an environment variable (`echo ${PATH}`); `NAME=value` sets or modifies the system environment-variable table. There is no `$?`, `$!`, positional parameters, or arithmetic expansion.
- A first effective character `#` comments out the whole line. A trailing `\` continues the line; only `\r`, `\n`, `\\`, `\"` are recognized escapes, and inside double quotes `\n` still expands to a real newline.
- A trailing `&` runs the command asynchronously in a new thread; a trailing `^` runs it synchronously in a new thread. There is no job control (`jobs`/`fg`/`bg`).
- Command lookup order: exact file path, then `PATH` directories, then built-in commands. An application masks a same-named built-in.
- Confirm every command on the actual target with `help` (list) or `help <cmd>` (usage); the command set is trimmed by kernel configuration and varies per board. `Ctrl+C` aborts the current task; `Ctrl+X` resets the target.

Never use these bash/POSIX constructs — ttinyShell rejects or misparses them:

| Never write | Use instead |
|---|---|
| Pipe `cmd1 \| cmd2` | Redirect to a file, then run a second command; filter locally per "Verify locally and report" |
| Globs `*.txt`, `file?` | List file names explicitly |
| `if`/`for`/`while`/`case`, functions, `$(...)`, backticks, `$?` | Split into separate commands; put logic in a program |
| `2>&1` or other fd duplication | `8>file` merges stdout and stderr; `8>>` appends |
| Single quotes, `export`, `source`, `sh -c` | Double quotes; `NAME=value`; the target has no `/bin/sh` |

Redirection is limited to `>file`, `1>file`, `2>file`, `8>file`, the `>>`/`1>>`/`2>>`/`8>>` append forms, and `0<file` for stdin. The redirection must be the last token of the command with no spaces around `>` or `<` (write `cmd >file`, not `cmd > file`); arguments after it are ignored; with multiple redirections only the last one takes effect (earlier files are created empty).

Shell scripts are line-by-line batches executed by `shfile <file>` (suffix is irrelevant): no conditions, loops, functions, or variable scope. `/etc/startup.sh` follows the same rules; put logic in a program instead of a script.

## Workflow

### 1. Establish the target

Read the current project's target configuration in `AGENTS.md` or `CLAUDE.md`.
When it provides `docs/agents/sylixos-test-debugging.md#1-select-the-target`,
read that section before connecting. Follow its default target, authoritative
test target, and restrictions on secondary targets. Keep endpoint values in
the project configuration. If no target is supplied by the project or user,
ask for the endpoint before any network action.

Confirm the selected target from that context before connecting. Do not scan
the network or infer another target from a failed connection. The wrappers
default to Telnet port 23 and FTP port 21; use the configured ports when supplied.

### 2. Transfer files only when needed

Use the bundled FTP client for both directions:

```text
python3 <SKILL_DIR>/scripts/ftp_client.py <IP> upload <local_path> <remote_path>
python3 <SKILL_DIR>/scripts/ftp_client.py <IP> download <local_path> <remote_path>
```

For a slow board or large artifact, override the FTP timeout before the IP:

```text
python3 <SKILL_DIR>/scripts/ftp_client.py --timeout 60 <IP> upload <local_path> <remote_path>
```

If the board exposes FTP on a non-default port, override it before the IP:

```text
python3 <SKILL_DIR>/scripts/ftp_client.py --port <PORT> <IP> upload <local_path> <remote_path>
```

Before uploading, check that the local file exists and that the remote directory is the intended one. After the wrapper reports success, verify the remote file with a separate Telnet command such as `ll <remote_path>` and, when available, a size or checksum comparison. Downloads use a temporary sibling file and rename it into place only after the transfer completes.

The FTP client does not create remote directories and does not preserve executable permissions reliably. If the uploaded file must be executed, grant permissions explicitly before running it:

```text
python3 <SKILL_DIR>/scripts/telnet_runner.py <IP> "chmod 0775 <remote_path>"
```

Use octal permissions. Do not use `chmod +x`.

### Loader recovery

If a just-uploaded executable reports `[ld]Can not find dependent library:` followed by
`Load file "<remote_path>" error Can not find module!`, the remote target can be stale or
incompletely replaced. Confirm that the exact target belongs to this deployment and is not
running, then delete only that file with a separate `rm <remote_path>` invocation. Verify that
the target is absent before uploading the artifact again. Restore `chmod 0775`, verify the file,
and rerun the program. Do not delete its containing directory or retry an upload over the existing
target for this recovery path.

### Observed SylixOS shell differences

Use these only after confirming the target exposes the same behavior:

- Prefer `ll <remote_path>` for file inspection. On the tested board, `ls -l` only reports that `ll` should be used.
- Decompress an uploaded artifact with `gzip -d <remote_path>.gz`. The tested `gzip` treats a combined `-df` argument as a filename; verify the decompressed target with `ll` before continuing.
- `kill` sends **SIGKILL by default** on the tested board — a bare `kill <id>` is a hard kill, not SIGTERM. There is no `kill -15` form (it fails with `option error`); the accepted syntax is `kill -n <signum> <id>` for any explicit signal. The id is parsed as hex, so copy it verbatim from `ps` (the process line shows the same value twice, e.g. `vmprobe2 <orphan> R 37 37 ...`; use the first). Always verify termination with a separate `ps`.

  ```text
  python3 <SKILL_DIR>/scripts/telnet_runner.py <IP> "kill -n 15 37"
  ```

  Note that a Go program built with the SylixOS Go toolchain may not act on SIGTERM gracefully:
  that toolchain's runtime signal table routes SIGTERM away from `os/signal`. ("Fork" here means
  the patched Go source tree used to build SylixOS binaries, not the Unix `fork()` call.) For
  such programs a plain `kill` (SIGKILL) plus the program's own periodic flush is the reliable
  stop, and data safety must not rely on signal handlers running.
- On the tested board, use `env NAME=value <command>` to launch one program with a process-specific environment variable. The value applies to that program and its children only; it does not modify the system environment-variable table or affect later Telnet invocations. For example:

  ```text
  python3 <SKILL_DIR>/scripts/telnet_runner.py <IP> "env ECSD_DEF_PATH=/tmp/ecsd-runtime ECSD_VSOA_PORT=1112 /tmp/ecsd-vsoa++"
  ```

  Use the executable's absolute path. If the variable must remain available after the program exits or across independent Telnet connections, set it separately with `NAME=value` or `env NAME=value`, then verify with `env`; persist it across reboots only with the appropriate SylixOS environment configuration workflow.
- Do not assume `md5sum` or `ldd` is installed. If either is absent, download the exact remote artifact with the FTP wrapper and compare its checksum locally.

### 3. Execute one command

Formulate the exact SylixOS command before invoking the wrapper, and validate the command string against the ttinyShell grammar rules above — Linux intuition does not transfer to ttinyShell. Quote the command for the local shell; the wrapper joins its command arguments and sends the resulting string to the board:

```text
python3 <SKILL_DIR>/scripts/telnet_runner.py <IP> "<COMMAND>"
```

The default Telnet command-output timeout is 10 seconds. Put timeout options before the board IP when a foreground command is expected to run longer:

```text
python3 <SKILL_DIR>/scripts/telnet_runner.py --timeout 90 <IP> "<COMMAND>"
```

`--timeout` is an alias for `--command-timeout` and only controls how long the local wrapper waits for the next shell prompt; it does not terminate the remote command. Use `--connect-timeout`, `--login-timeout`, or `--prompt-timeout` only when the corresponding connection phase is known to be slow. Options after the IP are treated as part of the board command, so place wrapper options before the IP.

The Telnet wrapper logs in, waits for a SylixOS prompt (`#` or `=>`), sends one line, removes the echoed command and trailing prompt, then prints the remaining text. Its output is cleaned command output, not a byte-for-byte transcript. An empty output is not automatically success or failure.

For executable deployment, use separate invocations in this order:

1. Upload the file with FTP.
2. Set `chmod 0775` if execution is required.
3. Verify the path and permissions.
4. Run the program with its exact arguments.
5. Verify the observable result, process state, or generated files with a new command.

Do not upload a helper shell script merely to combine these operations. If a command contains spaces or special characters in a path, quote the path for the board command and quote the complete command for the local shell.

### 4. Verify locally and report

Read every wrapper result before proceeding. Separate:

- transport result: whether FTP/Telnet connected and the wrapper completed;
- board result: what the returned output and follow-up inspection show;
- artifact result: whether the expected file, permissions, process, or output exists.

If output needs filtering, save or inspect it locally with local tools rather than adding board-side `grep`, `awk`, or pipes. Report the target IP, each transfer, each board command, verification evidence, and any result that remains unknown.

## Timeout and failure handling

The default limits are: FTP connection/operation timeout 10 seconds; Telnet connection timeout 5 seconds; login waits 3 seconds per prompt; shell-prompt waits 3 seconds; command-output read 10 seconds. Each can be overridden explicitly as described above. A timeout can occur after the board has already performed a write or started a process.

- Connection failure: report the stage and error; retry only after checking that the target and service are correct.
- FTP failure: do not run or distribute the remote file; retry only if the operation is safe to repeat, then verify it.
- Telnet output timeout: the wrapper returns exit code 2, preserves any partial output, marks the remote result unknown, and the agent must inspect the board with a read-only command before retrying a mutating command.
- Authentication or prompt failure: do not loop indefinitely; report that the wrapper's `root`/`root` login or prompt detection did not match the board.
- Program failure: capture the program output, then use a separate inspection command to distinguish an absent binary, permission problem, missing dependency, bad arguments, and runtime failure.

Never claim success from an attempted invocation alone. Success requires wrapper completion plus evidence appropriate to the operation.
