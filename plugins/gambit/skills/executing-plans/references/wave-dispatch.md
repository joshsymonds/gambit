# Wave dispatch — parallel workers with atomic integration

Read this for every wave with **≥2 tasks**. A single-task wave needs none of it: the worker uses the epic worktree and the ordinary checkpoint commit path.

## Isolate every worker at one base

File-disjoint tasks still interfere in a shared tree: one worker's mid-RED state, generated artifact, or build output can invalidate another worker's verification. Run each worker in a detached worktree forked from the clean epic worktree's exact HEAD:

```bash
BASE=$(git rev-parse HEAD)                    # run in the epic worktree
git worktree add --detach ../wave-<worker-slug> "$BASE"
```

Reserve a sibling path for the detached integration worktree, but do not create it. `integrate_wave.py` creates it only after every worker validates. Pass each worker its own path and the shared `$BASE`; workers edit but never commit.

## Make ownership executable

Every brief must name:

```markdown
## Files owned
- exact/repository/path.ext

## Hidden shared surfaces
- package lockfiles, generated indexes, registries, snapshots, or `None`

## Neighbors
- <worker name> — exact allowlist: <every path it owns> (off-limits)
```

`Files owned` is an exact path allowlist, not a directory, glob, or illustrative list. Any hidden surface a worker must change belongs in its allowlist; if that overlaps a neighbor, move the work to another wave. New and untracked text or binary files, deletions, symlinks, and executable-mode changes are deliverables and must be listed exactly.

## Inspect each worker before integration

After all workers return, inspect every isolated worktree's NUL-delimited status and actual diff against its brief. Run the checkpoint quality gate on each worker's complete change set. Do not use a plain `git diff` patch as transport: it can omit untracked files and cannot safely reconstruct every binary, index, mode, and symlink state.

Reject or re-dispatch quality defects before invoking the integrator. Do not run the full repository gate per worker; worker-scoped tests already ran concurrently in their isolated worktrees.

## Integrate the whole wave atomically

Create a JSON manifest outside the epic and worker worktrees. Preserve worker order because it becomes commit order:

```json
{
  "base": "<wave-start commit>",
  "epic_worktree": "<absolute epic worktree path>",
  "integration_worktree": "<absolute absent sibling path>",
  "gate": ["<program>", "<arg1>", "<arg2>"],
  "workers": [
    {
      "name": "<worker name>",
      "worktree": "<absolute worker worktree path>",
      "owned_paths": ["exact/path.ext", "exact/new-binary.dat"],
      "commit_message": "<durable per-worker commit subject>"
    }
  ]
}
```

Resolve the script beside this skill (plugin/cache paths vary), then run it by absolute path:

```bash
python3 <absolute-skill-directory>/scripts/integrate_wave.py <manifest.json>
```

The script executes one fail-closed transaction in this order:

1. **Validate inputs.** Reject any exact path owned by more than one worker before touching Git state. Verify the clean epic and every worker at `base`; discover staged, unstaged, untracked, deleted, binary, mode, symlink, space-containing, and Unicode paths NUL-safely; and reject empty or out-of-allowlist work. For each worker, build the complete candidate tree in a temporary index initialized from `base`, stage only its exact allowlist there, print its `--binary --full-index` diff, and fingerprint the unchanged real worktree and index.
2. **Combine ordered commits.** Revalidate every input, create one orchestrator-owned Git commit object per worker, and cherry-pick those commits in manifest order into the detached integration worktree. This is commit-based Git transport, never a plain patch. A conflict leaves epic HEAD unmoved and preserves the integration and worker worktrees as evidence.
3. **Run one combined gate.** Run the manifest's full-suite gate exactly once after every worker commit is combined on the detached candidate HEAD. A nonzero gate or any tracked, staged, or non-ignored untracked integration artifact fails closed.
4. **Fast-forward the exact tested head.** After the gate, revalidate the clean integration state, every worker, and the epic. Only then fast-forward the epic from `base` to the exact combined HEAD that passed the gate.
5. **Clean up only after success.** Remove worker and integration worktrees only after the exact-head fast-forward succeeds. Every validation, conflict, gate, or fast-forward failure leaves epic HEAD unmoved and retains all worktrees and artifacts as failure evidence.

## Checkpoint once

A successful ≥2-task wave reaches the epic as one atomic fast-forward containing one distinct history entry per worker. It still produces one checkpoint and one STOP after the whole wave. On any failure, do not clean or commit around the evidence: route the validation, conflict, or gate defect while the native wave remains in progress.
