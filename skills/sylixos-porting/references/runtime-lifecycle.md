# Runtime lifecycle recipes

## Export the main-module runtime symbol

**Signature:** the SylixOS dynamic loader cannot complete main-module
initialization or destruction because `__dso_handle` is absent.

**Recipe:** Export `__dso_handle` from the SylixOS main-entry adaptation and keep
the change scoped to that target.

**Validation:** Require a clean loader gate, basic JavaScript execution, and
normal main-module teardown.

## Tear down background threads before process return

**Signature:** SylixOS uses `LW_VPROC_EXIT_NORMAL`, waits for process threads
before running ELF destructors, while libuv historically waited until its
destructor to stop workers. Natural exit or `process.exit()` can therefore wait
forever on background workers or the SignalInspector watchdog.

**Recipe:**

- Make the SylixOS SignalInspector watchdog explicitly stoppable and joinable;
  use idempotent state, wake its semaphore, and join it during Environment
  cleanup and the explicit-exit handler.
- Preserve `SIGKILL` and `SIGSTOP` outside the blocked signal set.
- Call `uv_library_shutdown()` in the SylixOS `TearDownOncePerProcess()` path
  before platform destruction and before the main thread returns.
- Keep `LW_VPROC_EXIT_NORMAL` and return `node::Start()`'s real exit code.

Forced process mode and `_exit()` bypass lifecycle correctness and are outside
this recipe.

**Validation:** Run CJS and ESM natural exit plus explicit `process.exit()` with
nonzero status, require exact exit codes, and verify worker/watchdog threads are
gone. The recorded regression passed twice on QEMU.

**Boundary:** This recipe covers ordinary non-interactive shutdown. A TTY read
blocked in `tty_rsync` is a separate unresolved cancellation defect and must use
the target debugging guide rather than being classified as this recipe failing.
