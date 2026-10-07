---
name: ecsd-implement
description: "Implement approved ECSD++ specs and tickets on the SylixOS project, including TDD, C++ quality practices, focused validation, board verification, code review, staged commits, and final user self-test handoff."
---

# ECSD Implement

Implement the work described by the user in the approved spec or tickets.

Write focused tests at the agreed external behavior seams.

Run typechecking regularly when applicable, run single test files regularly, and run the full test suite once at the end.

Once done, review the diff for correctness and regression risks.

Create commits only when authorized by the user; follow `$commit` for scope and messages.

## Before editing

1. Confirm that the spec, tickets, blocking edges, acceptance criteria, and test seams have been approved.
2. Inspect the current branch and working tree. Create or use a dedicated `feat_<short-name>` branch and preserve unrelated user changes.
3. Read the applicable `AGENTS.md`, project context, domain glossary, ADRs, and original behavior references.
4. Use the existing CodeGraph index when the repository has `.codegraph/`; follow its AGENTS.md for synchronization. Use a full `codegraph index .` only when sync cannot provide a valid index.
5. Identify the smallest vertical slice that can be implemented and verified independently.

## Implementation rules

- Follow the current project’s C++ design, implementation, and debugging rules.
- Use the highest existing external behavior seam for tests; do not expose internal details only to make tests easier.
- Keep VSOA and CRI private interfaces isolated, keep `common` stateless, and follow the project's SylixOS-only constraint.
- Use `apply_patch` for local edits and avoid unrelated formatting or mechanical churn.
- Keep parallel work disjoint by file scope. Serialize integration, conflict resolution, builds, and operations on the same board.
- Do not introduce a dependency without first presenting its source, tradeoffs, and use case for user approval.

## Build and validation

Use only the project Makefile for build operations:

```text
make format
make config
make build
```

Analyze Makefile failures before considering any alternative; do not bypass the Makefile with direct CMake, Ninja, compiler, or cleanup commands.

Run focused tests after each vertical slice, then run the full test suite once all approved tickets are implemented. For SylixOS integration and runtime behavior, use `sylixos-ext-skill`; for crashes, hangs, thread state, or remote debugging, use `sylixos-gdb`; for code coverage, follow `docs/agents/sylixos-coverage.md`. Follow those guides for transport, symbol, endpoint, timeout, and evidence rules.

When comparing the JS v1 implementation, verify the same request sequence against the original and the C++ implementation. Record response shape, error behavior, state transitions, persistence, and notifications. Do not treat an unexplained difference as passing.

## Review and staged commits

Before each milestone commit:

1. Check the diff and confirm that only the intended files changed.
2. Run the milestone's focused tests and required board checks.
3. Review the diff and address actionable findings.
4. Stage only the files belonging to the milestone; never use `git add .` for convenience.
5. Commit to the current `feat_<short-name>` task branch.

Follow `$commit` for the authorized commit scope and concise Chinese Conventional Commit message. Project-specific requirements in AGENTS.md take precedence.

Do not push or publish a branch unless the user explicitly requests that action.

## Documentation consistency

If implementation, runtime behavior, or test evidence differs from `AGENTS.md`, `README.md`, `PROJECT.md`, `CONTEXT.md`, or `.agents/` documentation:

1. Record the document rule, observed behavior, reproduction, and evidence.
2. Determine whether the document is stale, the implementation is incomplete, the code is defective, the environment differs, or the divergence is intentional.
3. Do not silently edit the document or code to hide the difference.
4. Report the confirmed fact and proposed document change to the user and wait for agreement before updating project documentation.

## Final handoff

After all approved work is implemented, tested, reviewed, and committed:

- Report the completed behavior, remaining limitations, actual Makefile commands, board commands, test results, commits, and unresolved differences.
- Give the user a manual self-test procedure with prerequisites, order, expected results, log locations, and failure evidence to collect.
- Ask the user to perform the self-test. Even when no issue is found, request the complete self-test log so the observed behavior can be confirmed.
- Keep the task in `automated validation complete, waiting for user self-test` until the user returns the self-test evidence.
