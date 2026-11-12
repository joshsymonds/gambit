# Read-only steps

A read-only role may run as an orrery step instead of through the dispatch operation. This reference says when a step applies, what each `step_start` argument carries, and what to record. Implementers and orchestrators are never steps; they always use the dispatch operation.

## When steps apply

Steps apply when the session has the `step_start` and `step_wait` tools that `orrery mcp` serves and the repository carries no context stamp. A context stamp is a `.claude/settings.json` that git does not track (`git ls-files --error-unmatch .claude/settings.json` fails) and that sets `env.ANTHROPIC_BASE_URL`. Run the stamp test in the primary checkout, which is the parent directory of `git rev-parse --path-format=absolute --git-common-dir`, even when the session runs in a linked worktree: the untracked stamp exists only in the primary checkout. Pi has no step tools, so Pi keeps the dispatch operation.

Step roles are `scout`, `steelman`, `task-reviewer`, `conformance-reviewer`, `integration-reviewer`, `finding-verifier`, and `test-runner`. A role whose entry profile is `{"model": ...}` names no agent and uses the dispatch operation.

## step_start arguments

The keys follow `startSchema` in orrery v0.14.0's `internal/stepmcp/tools.go`, which refuses unknown keys. There is no model or effort field.

- `agent`: the entry profile's `readonly_agent`, except that the test runner uses the profile's writing `agent`.
- `schema`: the JSON object in `contracts/schemas/<role>.json` of the current installation.
- `prompt`: the role's contract by absolute path plus its complete brief, as the dispatch operation passes them.
- `workspace`: the absolute git workspace the role inspects.
- `revision`: the base revision it inspects: the task base for task-gate roles, the frozen or corrected candidate in review, and repository HEAD in brainstorming.
- `readOnly`: true for every step role, the test runner included.

Omit `doneValue`, `ownedPaths`, `gate`, and `gateLimitSeconds`; the schemas' done status is `done`, the default.

## Workspace and revision

A read-only step runs in a detached worktree at `revision`, without the task's uncommitted change. Brief each task-gate reviewer and verifier with the task workspace's absolute path to inspect. The test runner is a step only at a committed revision; a command that must run against uncommitted work uses the dispatch operation.

## Recording and waiting

`step_start` returns `{"id": ...}`. Record each id where its dispatch is recorded before waiting: the gate record's Task review row in executing-plans, the review ledger record in review, the Decision Log in brainstorming.

`step_wait` takes `ids` and returns `{"ended": <step or null>, "steps": [...]}`. A null `ended` means the 1500-second clamp passed; wait again. Name only ids still running, and drop an id once its step ends. Every end and every refused start or call is handled by `skills/executing-plans/references/step-ends.md`, which this reference does not restate.
