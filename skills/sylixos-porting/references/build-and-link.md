# Build and link recipes

## Cross-build recognition without cache churn

**Signature:** GYP does not recognize `sylixos`, host and target generated rules
overwrite each other, or every incremental build recompiles because a macro
containing `#` is truncated in a Make dependency record.

**Recipe:**

- Route the target through explicit `sylixos` branches in `configure.py`,
  `common.gypi`, and `node.gypi`.
- Import the SylixOS Base SDK include roots through the target configuration.
- Keep generated intermediates separate as `obj.host/gen` and `obj.target/gen`.
- Escape `#` when the GYP Make generator writes command dependencies; this is
  required for definitions such as `__CONST64(x)=x##ULL`.
- Scope the GCC 10 `gnu++2a` spelling to the SylixOS configuration while using
  it consistently for host generators and target objects in that configuration.
- Configure only when the target, toolchain, build options, or GYP inputs change;
  preserve each per-target build tree for ordinary incremental builds. Use
  `scripts/sylixos/build.sh build <platform>` or configure explicitly with
  `./sylixos-configure --platform <platform> --output-dir out.<suffix>`
  (`ARM64_GENERIC` -> `out.arm64`, `X86_64` -> `out.x64`); the trees are
  independent, so switching targets never recompiles the other one. Renaming or
  moving a build tree rewrites the directory strings embedded in every GYP
  command and forces one full (ccache-mitigated) rebuild.

**Protected behavior:** Maglev, Sparkplug, and TurboFan remain enabled. Other
targets keep their existing generated-directory and language-standard choices.

**Validation:** A no-change ARM64 Release rebuild must reuse prior objects, emit
no host/target recipe-overwrite storm, and preserve the expected JIT feature
configuration. The recorded Make baseline was 8.66–9.604 seconds versus about
25.5 seconds before the dependency fixes; use timing only as supporting evidence,
not as the correctness gate.

## Make `frexp` self-contained in the ELF

**Signature:** A binary linked against a newer SDK starts on an older board with
`can not find symbol: frexp` because `libstdc++.a(math_stubs_long_double.o)` adds
the reference after `libm.a` has been scanned and the newer `libvpmpdm.so`
silently satisfied it at link time.

**Recipe:**

- Keep SylixOS system dynamic libraries in the final `libraries` list rather
  than duplicating their paths and names in global `ldflags`.
- Provide a narrow SylixOS `frexp` ABI bridge in the main-entry adaptation and
  delegate it to the already-linked `frexpl` implementation.
- Preserve the ordinary implementation on other platforms.

Whole-archiving `libm.a` is outside this recipe: some long-double objects are not
PIC. Hard-coding an SDK archive member also makes the binary SDK-version-specific.

**Validation:** Run the repository ELF symbol gate on both unstripped and deploy
artifacts. `frexp` must be a defined `GLOBAL FUNC`, not `UND`. Then run `node -v`
on QEMU and the intended board and require a valid version with no loader symbol
diagnostic. The executable gate is
the current project’s ELF gate (`docs/agents/sylixos-build-verification.md` when provided).
