# Combined candidate transaction

## Manifest

For a multi-task effort, invoke `scripts/integrate_wave.py` by absolute path through the shell with a JSON manifest path. Put the manifest outside the epic and implementer workspaces. The script requires a clean epic and implementers at the same base, disjoint exact allowlists, and an absent integration-workspace path. Include only tasks whose complete change sets passed their gates; a wave never waits for tasks still in routing. Manifest order is commit order.

```json
{
  "base": "<effort-base-commit>",
  "epic_worktree": "<absolute-epic-workspace>",
  "integration_worktree": "<absolute-absent-integration-workspace>",
  "gate": ["<program>", "<argument>"],
  "implementers": [
    {
      "name": "<task-slug>",
      "worktree": "<absolute-implementer-workspace>",
      "owned_paths": ["exact/source/path", "exact/test/path"],
      "commit_message": "<task-result>"
    }
  ]
}
```

`base` is the effort's current base: the revision its workspace and every listed implementer sit at when this wave begins. `gate` is the full Done gate as an argument vector; use a shell invocation when Done requires shell syntax. `owned_paths` lists every writable path, including new files, deletions, binary files, symlinks, and mode changes. Implementers leave changes uncommitted. Transporting only an ordinary diff would omit some of these states.

## Transaction

1. Validate the manifest, exact ownership, shared base, and clean epic. Discover each complete implementer change set NUL-safely. Prepare its tree in a temporary index, stage only its allowlist, print the binary full-index diff, and fingerprint its actual index and workspace. Empty changes or ownership violations fail before integration.
2. Revalidate inputs, create one orchestrator-owned commit object per task, and cherry-pick those commits in manifest order into the detached integration workspace. Conflicts preserve evidence without advancing the epic.
3. Run the full Done gate once on the combined candidate. A nonzero exit or any tracked, staged, or non-ignored untracked integration artifact fails the transaction.
4. Revalidate the candidate, implementers, and epic. Fast-forward the epic from the recorded base only to the exact clean candidate revision that passed the gate.
5. Remove transient workspaces only after that fast-forward succeeds. Failures before fast-forward retain workspaces and evidence without advancing the epic; preserve any rejected revision on `candidate/<effort>` and route its NOT DONE record through the skill's integration step. A cleanup failure is reported after the tested revision is accepted: record that revision and the remaining workspace paths rather than treating the candidate as rejected. Record successful candidate revisions in the task gates.
6. Move each task still in routing to the new effort base before its next dispatch or gate, and only while its implementer is not running: `git -C <workspace> checkout --detach <new-base>`. Disjoint ownership lets the checkout carry the task's uncommitted owned-file changes unchanged. Re-run its test command there before gating. If the checkout refuses, re-dispatch the task from a fresh workspace at the new base with its gate history. Neither move spends an attempt.

## Efforts

An orchestrator owns one effort and runs `scripts/integrate_wave.py` with `epic_worktree` set to that effort's workspace. Create the workspace from the accepted `base` on branch `effort/<epic-slug>-<n>`; concurrent efforts therefore never share a workspace. Keep each effort's manifest outside its workspaces.

Each effort manifest lists only that effort's gated tasks and supplies the full Done gate. Its `base` is the effort's current base and its `epic_worktree` is the effort workspace; implementers still use disjoint exact allowlists. The effort's transaction must pass before its branch is offered to the loading session.

The loading session checks out the epic branch from the accepted base, then merges each finished effort branch as it completes, in completion order. Concurrent efforts own disjoint files, so these merges are conflict-free. After each merge, run the full Done gate on the merged epic. On green, that revision becomes the accepted base, and every effort that became dependency-ready is briefed from it and dispatched. If that gate fails, record NOT DONE against the effort whose files it names and retain the rejected revision and evidence for integration handling; efforts that do not depend on it continue.
