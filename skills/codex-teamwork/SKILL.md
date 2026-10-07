---
name: codex-teamwork
description: Coordinate multiple explicitly requested subagents as an explicitly requested development team while the primary agent remains a plan-only coordinator. Use only when the user invokes codex-teamwork to parallelize research, implementation, testing, review, integration, or other composable work, including alongside other explicitly invoked skills.
---

# Codex Teamwork

Act as the team's plan-only coordinator. Delegate all execution to the user-selected model, or an available model inherited from the coordinator workers and keep responsibility for planning, approval, coordination, review, and reporting in the primary agent.

## Hold the hard approval gate

Before the user approves the displayed teamwork plan, call only tools and commands that are provably read-only. In particular, do not:

- create any worker;
- run `codegraph sync`, `codegraph index`, or another index or cache refresh;
- install dependencies or run generators;
- format, configure, build, test, deploy, or touch hardware;
- create or update the planned deliverables.

Using an existing read-only code index is allowed. If an instruction requires a mutation before reliable investigation can continue, stop and put that mutation in a prerequisite worker task for user approval. Never perform it in the primary agent or claim the plan has already authorized it.

## Preserve instruction and skill composition

- Follow all higher-priority instructions, workspace `AGENTS.md` files, and task-specific safety or approval rules.
- Treat this skill as an orchestration layer. Do not replace or weaken companion skills.
- Read every explicitly invoked companion skill completely before planning.
- Assign each worker only the companion skills relevant to its role. Require the worker to read each assigned skill itself from the supplied path before acting.
- Surface irreconcilable conflicts between instructions or skills before requesting plan approval.

## Enforce the coordinator boundary

The primary agent may:

- clarify requirements and assumptions;
- perform read-only repository investigation;
- design the solution and task dependency graph;
- assign roles, skills, reasoning effort, ownership, and acceptance criteria;
- create, coordinate, interrupt, and redirect workers;
- inspect worker reports and workspace diffs read-only;
- report progress, risks, evidence, and final status.

The primary agent must not:

- create, edit, delete, format, or generate project files;
- refresh or regenerate code indexes, caches, build trees, or other workspace metadata;
- implement fixes or finish incomplete worker code;
- run builds, tests, deployment, board operations, or other task execution;
- stage, commit, push, merge, or perform any Git write operation;
- perform an external mutation that belongs to the requested work.

Delegate every execution action and every rework action to a worker. If delegation becomes impossible, stop and ask the user instead of silently leaving teamwork mode.

## Decide whether teamwork fits

Use this skill only after explicit user invocation. Determine whether the request has at least two meaningful work units, useful role separation, or enough research and verification work to benefit from a team.

If the work cannot be divided safely or usefully:

1. Explain why teamwork is unsuitable.
2. Offer a revised team-shaped scope when one is reasonable.
3. Wait for the user's decision.
4. Do not let the primary agent become the implementer.

Sequential dependencies do not disqualify a task. Represent them as execution waves.

## Build an approval plan

Perform only the read-only investigation needed to make the plan reliable. Treat index synchronization, dependency installation, code generation, configuration, formatting, builds, and tests as execution even when their purpose is investigation. If reliable planning requires such an action, present it as a prerequisite worker task and wait for approval instead of running it in the primary agent.

Before creating any worker, present a plan containing:

- objective, scope, assumptions, and known constraints;
- task dependency graph and execution waves;
- one task packet per worker role;
- model and reasoning effort for each role;
- companion skills assigned to each role;
- exclusive file or resource ownership for concurrent writers;
- acceptance criteria and verification method;
- integration strategy, risks, and conditions requiring renewed approval.

Use an explicit task table with these columns:

| Wave | Task and role | Model and effort | Companion skills and paths | Dependencies | Exclusive ownership | Acceptance and verification |
| --- | --- | --- | --- | --- | --- | --- |

Write companion skills as a skill name followed by its absolute `SKILL.md` path, for example `$research (/absolute/path/to/research/SKILL.md)`. Every explicitly invoked companion skill must appear in at least one task row, or the plan must explain why it is inapplicable or conflicts with another instruction.

Use exact paths or bounded resource scopes wherever they are knowable. Resolve planned output paths before approval. Do not use placeholders such as "a new report file," "a private helper," or "the usual documentation location" when read-only investigation can determine a path. Do not replace the table with a vague role summary. Treat a plan that omits a required column value, companion skill path, or resolvable ownership path as incomplete and do not ask the user to approve it.

Wait for explicit user approval. Invocation of the skill alone is not approval to execute the plan.

After approval, advance through the approved waves without pausing after each one. Request approval again before proceeding when scope expands, risk materially increases, the approved design fails, a destructive action becomes necessary, an external dependency would be introduced, or a higher-priority instruction requires it.

## Select worker reasoning effort

Use the user-selected model, or an available model inherited from the coordinator for every worker. Choose effort by task risk:

| Effort | Use for |
| --- | --- |
| `low` | Mechanical, isolated work with an established solution |
| `medium` | Normal bounded implementation or research |
| `high` | Cross-file behavior, interfaces, or complex tests |
| `xhigh` | Integration, concurrency, or difficult debugging |
| `max` | Architectural, high-risk, or root-cause-heavy work |
| `ultra` | Only when the user explicitly requests it |

Prefer the lowest level that can reliably satisfy the task. State the selected effort in the approval plan.

## Create self-contained task packets

Use clean or narrowly forked context when selecting a custom worker model. Never assume a worker received the full conversation. Give every worker a self-contained packet with:

1. role and objective;
2. relevant background and approved decisions;
3. inputs and completed dependencies;
4. exact file or resource ownership;
5. required companion skills and their paths;
6. acceptance criteria and verification commands;
7. applicable constraints and prohibited actions;
8. required final report: changes, evidence, risks, and remaining work.

Tell workers that the workspace is shared, unrelated changes belong to others, and they must not revert or overwrite them.

## Dispatch dependency waves

- Use only the currently available concurrency slots; do not create agents merely to fill capacity.
- Dynamically choose research, implementation, testing, review, integration, or other roles from the approved plan.
- Run all currently unblocked tasks with mutually exclusive ownership in parallel.
- Wait for their results, inspect them, then unlock the next dependency wave.
- Keep scheduling centralized in the primary agent. Workers must not create nested subagents unless the approved plan explicitly authorizes it.

When model override rules prevent full-history inheritance, spawn workers with no history or a small bounded fork and rely on the task packet.

## Protect the shared workspace

- Give concurrent writers mutually exclusive file and resource scopes.
- Assign overlapping files to one worker or schedule their changes in separate waves.
- Require a worker to stop and report before crossing its ownership boundary.
- Serialize global formatting, integration fixes, builds, shared hardware or board access, and Git operations.
- Preserve user changes and other workers' changes. Never instruct a worker to discard unfamiliar work.

## Verify and integrate

Require each implementation worker to perform the validation allowed by its ownership and report exact commands and results.

For significant work, schedule an independent independent verification or integration worker in a later wave. Grant it explicit ownership before allowing fixes. Use independent verification for cross-module changes, interface changes, bug fixes, risky behavior, or any task whose acceptance evidence is not otherwise convincing. Low-risk localized work may be self-verified by its implementer.

Keep repository-wide formatting, builds, tests, integration repair, and environment-specific verification with a serialized worker. The primary agent reviews the resulting evidence but does not execute these actions.

## Recover and replan

For an omission or localized failure:

1. Send one focused rework request to the original worker.
2. Replace or stop that worker if it fails again, becomes unavailable, or followed a fundamentally invalid approach.
3. Reassign the work to a new worker with a corrected self-contained packet.

Never repair the work in the primary agent.

If the user changes direction during execution:

1. Interrupt affected workers promptly.
2. Preserve completed results that remain compatible.
3. Recompute dependencies, ownership, risks, and acceptance criteria.
4. Present the revised plan and wait for approval when the change is material.

## Complete the teamwork run

Declare completion only when:

- every approved task is complete;
- the primary agent has inspected the resulting diff or artifacts read-only;
- acceptance evidence is present;
- required verification has passed or every unverified item is explicit;
- no worker has unresolved risks hidden in its report.

Report the outcome, worker contributions, changed scope, validation commands and results, remaining risks, and any user action still required. Never stage, commit, push, publish, deploy, or perform another protected external write without explicit authorization.
