---
name: finishing-branch
description: Integrates a finished branch — merge, pull request, keep, or discard — after verifying tests on the result. Use when every native epic wave is completed, when ready to integrate after review approval, when choosing between merge / PR / keep / discard for a branch, when tests need final verification before integration, or when a merge produced conflicts that require re-testing. User phrases like "ready to merge", "open a PR", "done with this branch", "ship it".
---

<!-- Generated backend adapter: edit src/backends/codex/, not plugins/gambit/. -->

## Codex Backend

This skill is assembled for Codex. Before following the workflow, read
`references/codex-backend.md` completely. Its operation mappings are binding:
`SessionPlanRead` reads the root session's native wave plan, `SessionPlanWrite`
mutates it only through `update_plan`, and `SessionContextRead` reads the same
root transcript. One native plan step is one Gambit wave; parallel workers are
subagent threads inside that single step. These are backend operations, not
literal shell commands.

# Finishing a Branch

**Freedom: LOW** — verify tests before integrating (unless review's handoff guarantees green), never discard without typed confirmation, always use GambitAskUser for the options.

## Overview

Complete development work by verifying readiness, presenting integration options, and executing the user's choice. Handles merge, PR creation, keeping work, or discarding — with appropriate safety gates for each.

**Core principle:** Verify everything passes → Present options → Execute choice → Clean up only what should be cleaned up.

**Announce at start:** "I'm using gambit:finishing-branch to complete this work."

## Quick Reference

| Step | Action | STOP If |
|------|--------|---------|
| **1. Verify Waves** | `SessionPlanRead` — every wave step must be `completed`; confirm worker completion from checkpoints/native subagent results | Any wave incomplete |
| **2. Verify Tests** | Run full test suite (skip if review just ran it) | Any test fails |
| **3. Base Branch** | Detect via git merge-base | Can't determine base |
| **4. Present Options** | `GambitAskUser` with 4 choices | No response |
| **5. Execute Choice** | Merge / PR / Keep / Discard | Git command fails |
| **6. Cleanup** | Remove worktree if applicable | Only for merge/discard |

**Iron Law:** Tests must be known-green BEFORE presenting options — either freshly run here (standalone invocation) or verified by `gambit:review` at its handoff (chained invocation). Never present options without recent green evidence.

## When to Use

- Every native epic wave shows `completed`, with worker completion retained in root checkpoints
- Implementation reviewed and ready to integrate
- After `gambit:review` approves the implementation

**Don't use when:**
- Any native wave is pending or in progress → use `gambit:executing-plans`
- Epic not yet reviewed → use `gambit:review` first
- Tests failing → fix first
- Work still in progress
- No epic exists → use `gambit:brainstorming`

## The Process

### Step 1: Verify Every Wave Complete

Run `SessionPlanRead`. Every concise wave step must show `completed`.

**If a wave is still open — STOP:**

```
Cannot finish: native plan still has open waves:
- Current wave: [summary] (status: in_progress)
- Later wave: [summary] (status: pending)

Complete every wave before finishing.
```

**If all waves are complete:** use `SessionContextRead` to confirm individual worker completion from the latest checkpoints/native subagent results and reread the full approved epic contract. Verify every epic success criterion. Plan steps never stand in for worker records or the contract.

---

### Step 2: Verify Tests Pass

**Skip this step if invoked by `gambit:review`.** Review's handoff guarantees tests are green (either freshly run at its Step 9 gate decision after remediation, or already green since review began and no code changed). Re-running here is pure redundancy. Trust review's handoff announcement and go to Step 3.

**Run the full suite only when invoked standalone** (user ran `$gambit:finishing-branch` directly without a prior review, or invoked from any path other than review's approval gate). Detect the test command from project files (go.mod → `go test ./...`, package.json → `npm test`, Cargo.toml → `cargo test`, pyproject.toml → `pytest`, Makefile → `make test`).

- All tests pass (or skipped because review just ran them) → Step 3
- Any test fails → **STOP.** Show failures. Cannot proceed until tests pass.

---

### Step 3: Determine Base Branch

Determine the **branch name** this work should integrate into. `git merge-base` returns a commit
SHA, not a branch — it cannot answer this, and Step 5 needs a name to check out.

```bash
git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||'
```

If that is empty or the repo has several long-lived bases, ask the user which base branch to use.
Do not guess between `main` and `master`.

---

### Step 4: Present Options

**Use GambitAskUser — do not print options as text.**

```
GambitAskUser
  questions:
    - question: "All waves complete, tests passing. How should we integrate?"
      header: "Integration"
      options:
        - label: "Merge locally"
          description: "Merge to <base-branch>, delete feature branch"
        - label: "Create Pull Request"
          description: "Push and create PR for review"
        - label: "Keep as-is"
          description: "Leave branch and worktree, handle later"
        - label: "Discard"
          description: "Delete all work (requires typed confirmation)"
      multiSelect: false
```

**STOP.** Wait for user response. Do not add recommendations, defaults, or explanations.

**The 4 options above are fixed.** Never modify, reorder, add variants (like "merge and push"), or remove any. The "Never push main" rule means the *base branch* is never pushed — the user pushes it manually after merge. (Option 2 does push the feature branch; that is what opening a PR requires.)

---

### Step 5: Execute Choice

#### Option 1: Merge Locally

1. `git checkout <base-branch>`
2. `git pull`
3. `git merge <feature-branch>`
4. **Run tests on merged result** — if tests fail, present sub-options:
   - Fix failures before completing
   - Abort merge (`git merge --abort`)

   **STOP and wait for user choice.**
5. `git branch -d <feature-branch>` (safe delete)
6. Go to Step 6

**Do NOT push to remote.** User pushes when ready.

---

#### Option 2: Create Pull Request

1. `git push -u origin <feature-branch>`
2. Use `SessionContextRead` to reread the full approved epic contract and latest checkpoint for PR content
3. Create PR:

```bash
gh pr create --title "feat: <epic-name>" --body "$(cat <<'EOF'
## Summary
<2-3 bullets from epic requirements>

## Waves Completed
<concise completed-wave list from SessionPlanRead, with worker outcomes summarized from checkpoints>

## Test Plan
- [ ] All tests passing
- [ ] <verification steps from epic>
EOF
)"
```

4. Report PR URL

**DONE — do NOT go to Step 6.** Branch and worktree (if any) are preserved for PR feedback.

---

#### Option 3: Keep As-Is

Report: "Keeping branch `<name>`." If worktree exists, add: "Worktree preserved at `<path>`."

**DONE — do NOT go to Step 6.**

---

#### Option 4: Discard

1. Show what will be deleted:

```bash
git log --oneline <base-branch>..HEAD
```

2. **Request typed confirmation:**

```
This will permanently delete:
- Branch <name>
- All N commits listed above
- Worktree at <path> (if applicable)

Type 'discard' to confirm.
```

**STOP.** Wait for exact text "discard". Anything else → clarify, do not proceed.

3. `git checkout <base-branch>`
4. `git branch -D <feature-branch>`
5. Go to Step 6

---

### Step 6: Cleanup (Merge and Discard Only)

**Only runs for Options 1 and 4. Options 2 and 3 skip this entirely.**

Check if a worktree exists for this branch:

```bash
git worktree list
```

- Session is inside a worktree created by `GambitEnterWorktree` this session → `GambitExitWorktree action: "remove"` (for Discard, pass `discard_changes: true` only after the typed confirmation)
- Worktree exists from an earlier session or repository tooling (for example, `.worktrees/`) → return to the base branch, then `git worktree remove <path>`
- No worktree → skip (branch may not have used one)

Report cleanup results.

---

## Examples

### Good: Full Merge Process

```
Step 1: SessionPlanRead → all wave steps completed; checkpoints confirm every worker result
Step 2: npm test → 127 tests passed
Step 3: git merge-base HEAD main → abc123
Step 4: [GambitAskUser with 4 options]
         User selects: Merge locally
Step 5: git checkout main
        git pull
        git merge feature-auth
        npm test → 127 tests passed  (verify merged result)
        git branch -d feature-auth
Step 6: GambitExitWorktree action:"remove"   (or git worktree remove for an older worktree)

Done. Feature merged to main.
```

### Bad: Skip Tests + Cleanup PR Worktree

```
Step 1: Waves complete
Step 2: SKIPPED             ← WRONG: tests might fail
Step 4: User selects PR
Step 5: git push, gh pr create
        git worktree remove  ← WRONG: PR needs worktree

# Merged broken code. Lost worktree for PR feedback.
```

### Good: Discard With Typed Confirmation

```
git log --oneline main..HEAD
→ a1b2c3d Add OAuth
→ d4e5f6g Add rate limiting

"This will permanently delete branch and 2 commits.
 Type 'discard' to confirm."

User: "discard"

git checkout main && git branch -D feature-experimental
git worktree remove .worktrees/experimental
```

## Integration

**Called by:**
- User via `$gambit:finishing-branch`
- `gambit:review` (after approval — the normal workflow path)
- After `gambit:executing-plans` → `gambit:review` completes

**Calls:**
- `gh` CLI (PR creation)
- `git` commands (merge, branch, worktree)

**Pairs with:**
- The epic worktree (created through the repository convention or standard Git worktree tooling) — cleaned up here on merge/discard
