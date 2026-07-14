# Wave dispatch — parallel workers in isolated worktrees

Read this when a wave has **≥2 tasks**. A single-task wave needs none of it: the worker works in the epic's tree and you commit as usual.

## Why worktrees, not shared-tree parallelism

File-disjoint tasks still interfere in a shared tree — one worker's mid-RED broken state, half-written package, or repo-wide lint run fails another worker's verification through no fault of either. (This happened in practice: a concurrent worker's temporary fixture deletion failed a neighbor's test run.) Isolation removes it — each worker gets its own worktree, so its tests, lints, and builds see only its own changes.

## Fork the wave from the epic worktree's HEAD

The epic's working tree is the integration base. For each task in the wave, fork a **detached-HEAD** worktree from its current HEAD, in a sibling directory:

```bash
BASE=$(git rev-parse HEAD)                    # run in the epic worktree
git worktree add --detach ../wave-<worker-slug> "$BASE"
```

Detached HEAD, not a branch: a branch can be checked out in only one worktree at a time, and a detached fork leaves no branch to clean up afterward. Pass the worktree path to the worker as its Workspace; it works only there.

**Alternative:** the Agent tool's native `isolation: "worktree"`. It works (real isolation; the diff is retrievable after the agent returns) but forks from the *orchestrator's-checkout* HEAD and leaves a lingering locked branch each wave — so prefer the explicit `git worktree add --detach` above, which forks from the exact base you name and cleans up completely.

## Neighbors in every brief

Each brief in the wave carries a Neighbors section:

```
## Neighbors
- <task subject> — owns <files>   (off-limits to you)
```

The worker contract treats a neighbor's file as out of scope (a Stop Trigger), so a worker that finds it needs a neighbor's file reports rather than colliding.

## Integrate serially — you are the sole committer

Workers never commit, even in their own worktrees — so a worker's changes are **uncommitted working-tree edits**, and its worktree HEAD is still `$BASE`. Retrieve them with a plain working-tree diff (NOT `$BASE..HEAD`, which compares two identical commits and yields nothing). Integrate one at a time, in the epic worktree:

```bash
patch=$(mktemp)                                   # scratch file (mktemp, not a predictable /tmp path)
git -C ../wave-<id> diff > "$patch"               # the worker's uncommitted edits
# → run the checkpoint quality gate on this diff (Step 2)
git apply "$patch"                                # apply into the epic tree
# → run the FULL test suite here, in the epic tree (not the worktree)
git add <the task's files by name> && git commit  # per-task commit (this is Step 4a)
```

Gate → apply → full suite → commit, then the next worker. Never apply two unverified diffs at once. If an apply conflicts, or the suite fails after applying, that task drops to BLOCKED / quality-defect routing (Step 2) — the workers already integrated stay committed; the wave does not roll back.

Integration is **serial**: each task's full-suite run happens one at a time, so a wave of N tasks costs ~N × the suite. The wave parallelizes worker *write* time, not integration — scale width to suite speed: a fast suite affords a wide wave, a slow one argues for narrower.

## Remove the worktrees

```bash
git worktree remove --force ../wave-<id>     # --force: test runs leave untracked artifacts
```

Detached HEAD means there is no branch left to delete.

## What reaches the checkpoint

A ≥2 wave produces **N per-task commits** (one per integrated worker) inside a single cycle, then **one** checkpoint summary (Step 4b) listing them all. The STOP still happens once, after the whole wave integrates.
