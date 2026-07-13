# Codex Backend Operations

Use these mappings whenever the skill names a Gambit operation. The skill's
workflow and stop conditions remain authoritative; this file only translates
platform mechanics.

## Durable task state

When the skill directory contains `scripts/gambit_tasks.py`, resolve that path
relative to the loaded skill and use it for every task operation. The script
stores state under the repository's Git common directory, so state survives
Codex threads and worktrees without dirtying the worktree.

- `GambitTaskList` → `python3 <skill-dir>/scripts/gambit_tasks.py list`
- `GambitTaskGet taskId: "task-1"` → `python3 <skill-dir>/scripts/gambit_tasks.py get task-1`
- `GambitTaskCreate` → write the full description to a temporary file, then run
  `python3 <skill-dir>/scripts/gambit_tasks.py create --subject "..." --description-file <file> --active-form "..."`.
- `GambitTaskUpdate` → `python3 <skill-dir>/scripts/gambit_tasks.py update <id>` with
  `--status`, `--subject`, `--active-form`, `--description-file`, or repeated
  `--add-blocked-by` / `--remove-blocked-by` arguments as required.

Treat structured `GambitTaskCreate` and `GambitTaskUpdate` examples in a skill
as specifications for these commands. Preserve multiline descriptions exactly
through `--description-file`. The durable store is the source of truth;
Codex's in-turn plan may mirror the active wave but must not replace it.

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
When the skill specifies an agent contract, pass its path and require the
agent to read it first. Codex agent profiles own concrete model selection; do
not pass foreign model aliases from pseudocode.

## Worktrees

- `GambitEnterWorktree` means create or enter an isolated epic worktree using
  the repository's convention, falling back to `git worktree add`.
- `GambitExitWorktree` means leave and, when authorized by the workflow, remove
  it with `git worktree remove` and prune stale metadata.

Never execute epic implementation on the default branch. For parallel write
waves, give each worker an isolated worktree and integrate results serially as
the skill directs.

## Tool vocabulary

References to reading, searching, shell execution, or applying edits describe
capabilities rather than fixed tool names. Use the corresponding Codex tools,
preferring `rg` for search and patch-based edits for manual file changes.
