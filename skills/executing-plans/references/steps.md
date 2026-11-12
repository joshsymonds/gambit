# Steps

A role may run as an orrery step instead of through the dispatch operation. This reference says when a step applies, what each `step_start` argument carries, what a done implementer end gives the gate, and what to record. Orchestrators are never steps; they always use the dispatch operation, while implementers run as writing steps where steps apply and dispatch elsewhere.

## When steps apply

Steps apply when the session has the `step_start` and `step_wait` tools that `orrery mcp` serves and the repository carries no context stamp. A context stamp is a `.claude/settings.json` that git does not track (`git ls-files --error-unmatch .claude/settings.json` fails) and that sets `env.ANTHROPIC_BASE_URL`. Run the stamp test in the primary checkout, which is the parent directory of `git rev-parse --path-format=absolute --git-common-dir`, even when the session runs in a linked worktree: the untracked stamp exists only in the primary checkout. Pi has no step tools, so Pi keeps the dispatch operation.

Step roles are `scout`, `steelman`, `task-reviewer`, `conformance-reviewer`, `integration-reviewer`, `finding-verifier`, and `test-runner`. The implementer is the writing step role. A role whose entry profile is `{"model": ...}` names no agent and uses the dispatch operation.

## step_start arguments

The keys follow `startSchema` in orrery v0.14.0's `internal/stepmcp/tools.go`, which refuses unknown keys. There is no model or effort field. The field rules are in orrery v0.14.0 docs/contract.md under "StartStep checks each field".

### Read-only steps

- `agent`: the entry profile's `readonly_agent`, except that the test runner uses the profile's writing `agent`.
- `schema`: the JSON object in `contracts/schemas/<role>.json` of the current installation.
- `prompt`: the role's contract by absolute path plus its complete brief, as the dispatch operation passes them.
- `workspace`: the absolute git workspace the role inspects.
- `revision`: the base revision it inspects: the task base for task-gate roles, the frozen or corrected candidate in review, and repository HEAD in brainstorming.
- `readOnly`: true for every step role, the test runner included.

Omit `doneValue`, `ownedPaths`, `gate`, and `gateLimitSeconds`; the schemas' done status is `done`, the default.

### Implementer steps

An implementer step is a writing step. Its `workspace` is the task's own linked worktree, which the orchestrator creates from the effort's current base before the start. Run `scripts/validate_dispatch.py` on the brief and record before `step_start`, as the build step requires before any implementer dispatch: dispatch only on exit 0, and append exit 1 defects to `conduct.brief_defects`. Its arguments:

- `agent`: the entry profile's writing `agent`.
- `schema`: the JSON object in `contracts/schemas/implementer.json` of the current installation.
- `prompt`: `contracts/implementer.md` by absolute path plus the complete brief with its `Brief:`, `Workspace:`, `Record:` and `Task:` lines, as the dispatch operation passes them.
- `workspace`: the task's own linked worktree; orrery refuses a main working tree.
- `revision`: the task base, the task's `dispatch.revision`, for every step of the task.
- `readOnly`: false.
- `ownedPaths`: exactly the brief's Files owned.
- `doneValue`: `done`.
- `gateName`: the name on the brief's `Gate:` line; orrery's named-gates release (L1b) takes it with `gatesFile`.
- `gatesFile`: the absolute path of `gates.toml` in the epic's record directory.

The effort brief carries, for each gate, its name and the absolute path of the epic's `gates.toml`; the effort orchestrator fills `gateName` and `gatesFile` from it.

The name comes from the contract's `Steps:` checks line (`skills/brainstorming/TEMPLATES.md`), resolved in `gates.toml`, then in `.orrery/project.toml` at the top of the step's `workspace`. An epic accepted before 2.11.0 has no `gates.toml`: the Director logs one Decision Log line naming the gate and writes `gates.toml` from its `Steps:` line's argv and limit.

## Workspace and revision

A read-only step runs in a detached worktree at `revision`, without the task's uncommitted change. Brief each task-gate reviewer and verifier with the task workspace's absolute path to inspect. The test runner is a step only at a committed revision; a command that must run against uncommitted work uses the dispatch operation.

An implementer step writes in its own linked worktree, not a detached one, and its `revision` is the task base.

## Implementer done ends

A `done` end of an implementer step gives the gate its evidence. The engine runs four commit checks in order: `head`, `ancestry`, `clean`, and `owned`. `owned` checks the paths changed from the task base to the return's `commit` against `ownedPaths`. The gate then runs. These checks, the gate result, and the return's `commit` supply the gate record's Owned-files result and named check, and inspection of the commit and task review continue: the orchestrator reads the commit's complete change set as the build step requires, and the commit integrates as the manifest entry's `commit`, as `skills/executing-plans/references/wave-dispatch.md` describes.

## Commits

An implementer's commit follows its route: a dispatched implementer leaves its changes uncommitted, and a step commits once in its own workspace before it returns `done`, naming that commit as `commit`; only the orchestrator commits to the effort branch.

## Recording and waiting

`step_start` returns `{"id": ...}`. Record each id where its dispatch is recorded before waiting: the gate record's Task review row in executing-plans, the review ledger record in review, the Decision Log in brainstorming. An implementer's id goes in the task's `dispatch.child` before waiting, per `skills/executing-plans/references/record.md`.

`step_wait` takes `ids` and returns `{"ended": <step or null>, "steps": [...]}`. A null `ended` means the 1500-second clamp passed; wait again. Name only ids still running, and drop an id once its step ends. Every end and every refused start or call is handled by `skills/executing-plans/references/step-ends.md`, which this reference does not restate.
