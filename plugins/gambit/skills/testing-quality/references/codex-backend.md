# Codex Backend Operations

Use these mappings whenever a generated skill names a Gambit operation. The
skill's workflow and stop conditions remain authoritative; this file defines
how its conceptual task language maps onto Codex session state.

## Ownership and source of truth

The root Codex task owns exactly one Gambit plan. That plan is the native plan
attached to the root task, and native `update_plan` is its only mutation
mechanism. Do not create another task store, plan file, service, environment
namespace, or active-epic selector.

The complete approved epic contract and full worker briefs live in the same
root session's transcript and checkpoint messages. They never live in plan
step text or a repository orchestration file. The native plan records only
wave summaries and native statuses.

Only the root orchestrator reads or writes this state. A worker thread receives
a self-contained brief and must not discover, adopt, enumerate, or mutate the
root plan.

## Session operations

- `SessionPlanRead` means inspect the current root session's native plan as exposed
  in the session. It is read-only; it never scans Git, repository files,
  worktrees, another session, or worker threads for orchestration state.
- `SessionPlanWrite` means call native `update_plan` with the complete current
  list of wave steps. Each call preserves completed waves, changes the current
  wave status as needed, and adds or revises only wave summaries justified by
  the approved contract or latest checkpoint.
- `SessionContextRead` means reread the approved contract, worker briefs, and
  latest checkpoint from the same root session's transcript. It never selects
  an epic from repository state or another task's history.

Apply these invariants to every `SessionPlanWrite`:

- One plan step represents one Gambit wave.
- A parallel wave is one in-progress step; its individual workers are native
  subagent threads, not additional plan steps.
- There is at most one active wave and therefore at most one `in_progress`
  step.
- Step text is a concise wave summary. Do not persist IDs, full task
  descriptions, worker briefs, dependency edges, or an epic selector in it.
- Order is the only plan representation of prerequisites: later work goes in a
  later wave. Never construct dependency edges.

Canonical skills are shared with Claude and may retain structured task
examples after operation names are transformed. Treat those examples as
conceptual input, not a storage schema:

- An epic example supplies the contract to present for approval and retain in
  the root transcript; it does not become an epic plan step.
- A task example supplies a full worker brief to retain in the transcript or
  latest checkpoint. Put only its concise wave summary in the plan.
- Multiple independent task examples for the same cycle become workers inside
  one wave step. Dependent work becomes a later wave step.
- A create or update example rewrites the native wave list through
  `SessionPlanWrite`; it never creates a persisted task record.

## Resume, new tasks, and forks

- Resuming the same root task continues its existing plan and same-session
  contract/checkpoints.
- `/new` starts a new root task with no Gambit plan or inherited contract.
- `/fork` is copy-on-fork: the new root begins with the plan and transcript
  context visible at the fork point, then its plan and checkpoints evolve
  independently. Neither branch may mutate the other's state.

Never infer ownership from the repository, branch, worktree, current directory,
or a persisted identifier. The root task boundary is the ownership boundary.

## Recovery and fail-closed behavior

If native plan state is absent in an existing root task, reconstruct it only
from that same root session's approved contract and latest checkpoint via
`SessionContextRead`, then write the recovered wave list with
`SessionPlanWrite`. If those messages do not contain enough information, ask
the user rather than guessing.

If `update_plan` is unavailable, fail closed: explain that native plan mutation
is required and ask the user how to proceed. Never fall back to disk, Git,
another service, a goal, or mental tracking. Legacy Git-local Gambit state is
ignored and left untouched; there is no migration path.

## Goals are separate

A user-created goal may authorize a stop hook to invoke another execution
cycle. It does not own or store Gambit task state, and Gambit never creates a
goal automatically. The root session's native plan and transcript remain the
only orchestration sources of truth.

## Skill invocation and user input

- `$gambit:<name>` means explicitly invoke that installed plugin skill now.
- `GambitAskUser` means ask the user directly in prose, or use Codex's
  structured user-input mechanism when it is available and appropriate.

## Subagents

`SpawnAgent` examples specify a role and prompt, not literal API syntax. Use
Codex's subagent controls:

- Read-only exploration → `explorer`.
- Implementation or fixes → `worker`.
- Review, verification, or a fully specified contract → `default`, unless an
  installed custom agent matches the named role.

Dispatch independent agents concurrently. Keep dependent work sequential.
When a skill specifies an agent contract, pass its path and require the agent
to read it first. Pass every worker its complete brief; never ask it to inspect
the root plan. Codex agent profiles own concrete model selection, so do not
pass foreign model aliases from pseudocode.

## Worktrees

- `GambitEnterWorktree` means create or enter an isolated epic worktree using
  the repository's convention, falling back to `git worktree add`.
- `GambitExitWorktree` means leave and, when authorized by the workflow, remove
  it with `git worktree remove` and prune stale metadata.

Never execute epic implementation on the default branch. For parallel write
waves, give each worker an isolated worktree and integrate results serially as
the skill directs. Worktrees isolate code changes; they do not own or recover
orchestration state.

## Tool vocabulary

References to reading, searching, shell execution, or applying edits describe
capabilities rather than fixed tool names. Use the corresponding Codex tools,
preferring `rg` for search and patch-based edits for manual file changes.
