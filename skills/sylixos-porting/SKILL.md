---
name: sylixos-porting
description: Apply verified SylixOS porting recipes and platform baseline selection (FreeBSD/Linux/POSIX/RTOS) when adapting C/C++ libraries, Node.js, V8, libuv, build/link behavior, or target runtime lifecycle. Use for implementation or review of a SylixOS compatibility change; route unresolved crashes and temporary workarounds to diagnosis instead.
---

# SylixOS porting

Use this as a **verified-recipes** manual. A recipe is a narrow change whose
original failure, target-side success, and relevant regression boundary are all
recorded. Match the current symptom to one branch and read only that reference:

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

## Apply a recipe

1. Reproduce the same observable signature named by the recipe. A nearby
   symptom is a new diagnosis, not permission to broaden the patch.
2. Confirm the current source and SylixOS SDK still satisfy the recipe's
   assumptions; prefer current headers and call paths over cached prose.
3. Apply the smallest platform-scoped change. Preserve other operating-system
   branches and Node features explicitly protected by the recipe.
4. Run every validation gate listed by the recipe, then the repository's
   SylixOS ELF gate and target testing guide when a binary is linked or run.
5. Report the reproduced signature, changed seam, target evidence, regression
   evidence, and any assumption that remains target-specific.

Completion requires all recipe gates to pass. A successful compile alone is
build evidence, not a verified port.

## Promote a new recipe

Add a solution here only when all of the following evidence exists:

- a pre-fix reproducer identifies the failing seam;
- the intended SylixOS target passes after the change;
- focused regression tests cover the affected behavior and adjacent paths;
- the change is scoped so unaffected targets retain their prior implementation;
- no current test result contradicts the claimed completion boundary.

Keep one authoritative recipe in this skill and link to detailed diagnostic
history elsewhere. Record an unresolved defect in
`docs/agents/sylixos-test-debugging.md` or `sylixos_adaptation.md`; promote it
only after its validation boundary turns green.

## Current exclusions

The accelerated OpenSSL/TLS crash, no-assembly workaround, TTY read cancellation,
spawn/`cwd`, cluster/IPC convergence, debugger residual processes, intermittent
heap aborts, UDP `SO_REUSEPORT` selection, and TCP/HTTP vector-write CPU behavior
are unresolved evidence. Use the diagnostic guide for them rather than treating
them as recipes.
