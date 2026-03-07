---
name: using-worktrees
description: Creates isolated git worktrees for feature work. Use when starting branches, working on multiple features, or needing workspace isolation with environment setup and baseline verification.
---

# Using Git Worktrees

## Overview

Git worktrees create isolated workspaces sharing the same repository. No switching branches, no stashing, no conflicts with in-progress work.

**Core principle:** Discover location → verify safety → create → setup environment → verify baseline → report.

**Iron Law:** NO skipping baseline verification. Tests must pass in the new worktree BEFORE reporting ready. No exceptions.

**Announce at start:** "I'm using gambit:using-worktrees to set up an isolated workspace."

## Rigidity Level

LOW FREEDOM - Follow the 8-step process exactly. No skipping steps. STOP points halt execution until resolved.

## Quick Reference

| Step | Action | STOP If |
|------|--------|---------|
| 1 | Check existing directories | - |
| 2 | Check CLAUDE.md preference | - |
| 3 | Ask user for preference | No answer received |
| 4 | Verify directory is gitignored | Cannot add to .gitignore |
| 5 | Create worktree | Git command fails |
| 6 | Run environment setup | Setup fails |
| 7 | Verify clean baseline | Tests fail AND user says investigate |
| 8 | Report ready | - |

**Directory priority:** Existing dir > CLAUDE.md preference > Ask user

## When to Use

- Starting feature work that needs isolation from main workspace
- Before executing implementation plans
- Working on multiple features simultaneously
- Experimenting without affecting main workspace

**Don't use for:** quick fixes, single-file changes, when user explicitly wants current directory

## The Process

### Step 1: Check Existing Directories

```bash
ls -d .worktrees 2>/dev/null     # Check first (preferred, hidden)
ls -d worktrees 2>/dev/null      # Check second (alternative)
```

- `.worktrees/` exists → Use it, skip to Step 4
- `worktrees/` exists (no .worktrees) → Use it, skip to Step 4
- Both exist → Use `.worktrees/`, skip to Step 4
- Neither exists → Step 2

---

### Step 2: Check CLAUDE.md Preference

```bash
grep -i "worktree" CLAUDE.md 2>/dev/null
```

- Specifies location → Use it, go to Step 4
- No preference or no CLAUDE.md → Step 3

---

### Step 3: Ask User for Preference

**REQUIRED: Use AskUserQuestion tool.**

```
AskUserQuestion
  questions:
    - question: "No worktree directory found. Where should I create worktrees?"
      header: "Location"
      options:
        - label: ".worktrees/ (Recommended)"
          description: "Project-local, hidden directory"
        - label: "worktrees/"
          description: "Project-local, visible directory"
        - label: "~/.worktrees/<project>/"
          description: "Global location outside project"
      multiSelect: false
```

**STOP: Wait for user response before proceeding.**

---

### Step 4: Verify Directory is Gitignored

**Project-local directories only** (.worktrees or worktrees). Skip for global (~/.worktrees/).

```bash
git check-ignore -q .worktrees 2>/dev/null  # or worktrees
```

- Exit 0 (ignored) → Step 5
- Exit 1 (not ignored) → Fix immediately:

```bash
echo ".worktrees/" >> .gitignore
git add .gitignore && git commit -m "chore: add worktree directory to gitignore"
```

**STOP if commit fails.** Do not create worktree with unignored directory.

---

### Step 5: Create Worktree

Determine branch name from user request (e.g., "auth feature" → `feature/auth`).

```bash
# Set path based on location choice
path=".worktrees/$BRANCH_NAME"           # project-local
path="$HOME/.worktrees/$project/$BRANCH_NAME"  # global

git worktree add "$path" -b "$BRANCH_NAME"
```

**STOP if git command fails.** Report error and ask user.

Verify:

```bash
cd "$path" && git status  # Clean working tree on new branch
```

---

### Step 6: Run Environment Setup

**Detect project type and run FIRST match:**

| Priority | Detection | Setup Command |
|----------|-----------|---------------|
| 1 | `devenv.nix` or `.envrc` | See devenv workflow below |
| 2 | `package.json` | `npm install` / `yarn install` / `pnpm install` (match lockfile) |
| 3 | `Cargo.toml` | `cargo build` |
| 4 | `pyproject.toml` with `tool.poetry` | `poetry install` |
| 5 | `requirements.txt` | `pip install -r requirements.txt` |
| 6 | `go.mod` | `go mod download` |
| None | No match | Report "No recognized project type. Skipping setup." |

#### Devenv Database Handling

If devenv detected, check for database usage:

```bash
grep -l "DATABASE_URL\|postgres\|mysql" devenv.nix .envrc 2>/dev/null
```

**If database found, REQUIRED: Ask about strategy:**

```
AskUserQuestion
  questions:
    - question: "This project uses devenv with a database. How should the worktree handle it?"
      header: "Database"
      options:
        - label: "Share database (Recommended)"
          description: "Use same $DATABASE_URL as main. Faster setup, shared data."
        - label: "Isolated database"
          description: "Create new database. Clean slate, but requires migration."
      multiSelect: false
```

**STOP: Wait for response.**

- **Shared:** `direnv allow 2>/dev/null || devenv shell`
- **Isolated:** Create database, write `.env.local`, allow direnv, run migrations

---

### Step 7: Verify Clean Baseline

**REQUIRED: Run tests to establish baseline.**

| Project Type | Test Command |
|--------------|--------------|
| Node.js | `npm test` |
| Rust | `cargo test` |
| Python | `pytest` |
| Go | `go test ./...` |
| Devenv | Check Makefile for `test` target |

- **All pass** → Step 8
- **Tests fail** → Present options to user:

```
Tests failing (N failures) in fresh worktree.
[Show first 3-5 failures]

These failures exist in the base branch. Options:
1. Proceed anyway (failures are known/expected)
2. Investigate before proceeding
3. Cancel worktree creation
```

- **Investigate** → STOP until resolved
- **Cancel** → `git worktree remove "$path"`, STOP
- **Proceed** → Continue to Step 8, noting known failures

---

### Step 8: Report and Chain Forward

```
Worktree ready at <full-absolute-path>
Branch: <branch-name>
Tests: <N> passing, <M> failures (if any)
Environment: <devenv/npm/cargo/pip/go/none>
```

**Always use full absolute path.** User needs it for navigation.

**Then chain to the next skill automatically.** If tasks exist (invoked from brainstorming/writing-plans handoff), invoke executing-plans directly:

```
Skill skill="gambit:executing-plans"
```

If no tasks exist yet (invoked standalone), ask the user:

```
AskUserQuestion
  questions:
    - question: "Worktree ready. What's next?"
      header: "Next step"
      options:
        - label: "Plan the work"
          description: "Design and create tasks with gambit:brainstorming"
        - label: "Start executing"
          description: "Execute existing tasks with gambit:executing-plans"
      multiSelect: false
```

Then invoke the chosen skill directly using the Skill tool.

---

## Critical Rules

### Rules That Have No Exceptions

1. **Never create project-local worktree without verifying gitignore** → Risk of committing worktree contents
2. **Never skip baseline test verification** → Can't distinguish new bugs from inherited ones
3. **Never proceed with failing tests without explicit permission** → User must acknowledge known failures
4. **Never assume directory location** → Follow priority: existing > CLAUDE.md > ask
5. **Always ask about database strategy for devenv projects** → Database isolation is a critical choice
6. **Always report full absolute path** → User needs exact location for navigation

### Common Excuses

All mean: **STOP. Follow the process.**

| Excuse | Reality |
|--------|---------|
| "Directory is probably ignored" | RUN git check-ignore to verify |
| "Tests probably pass" | RUN tests to verify |
| "Same as last time, don't need to ask" | ASK — user preferences can change |
| "Small feature, don't need isolation" | User requested worktree — create it |
| "Can fix gitignore later" | FIX NOW — prevents accidents |

---

## Verification Checklist

Before reporting ready:

- [ ] Checked existing directories (.worktrees, worktrees)
- [ ] Checked CLAUDE.md for preference
- [ ] Asked user if no existing preference (using AskUserQuestion)
- [ ] Verified directory is gitignored (project-local only)
- [ ] Created worktree with branch
- [ ] Detected environment type and ran setup
- [ ] Asked about database strategy (devenv with database only)
- [ ] Ran tests to verify baseline
- [ ] Got permission if tests failed
- [ ] Reported full absolute path, branch, test status, environment

---

## Examples

See [REFERENCE.md](REFERENCE.md) for detailed good/bad examples including:
- Complete workflow with devenv database handling
- Skipping gitignore verification (and consequences)
- Proceeding with failing tests silently (and consequences)

---

## Integration

**Called by:**
- `gambit:brainstorming` (optional, user chooses at handoff)
- `gambit:writing-plans` (optional, user chooses at handoff)
- User via `/gambit:using-worktrees`

**Calls:**
- `gambit:executing-plans` (invoked directly after worktree setup, if tasks exist)
- `gambit:brainstorming` (if invoked standalone with no tasks)

**Pairs with:**
- `gambit:finishing-branch` — handles worktree cleanup after work complete

**Workflow:**
```
gambit:brainstorming ─┐
                      ├→ gambit:using-worktrees → gambit:executing-plans
gambit:writing-plans ─┘                                    ↓
                                                 gambit:review
                                                           ↓
                                                 gambit:finishing-branch
```
