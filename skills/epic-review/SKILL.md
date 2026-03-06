---
name: epic-review
description: Reviews completed epic implementation for quality, architecture, security, and completeness before finishing-branch. Dispatches four specialized reviewer agents (conformance, security, quality, performance) in parallel for unbiased review. Use after all tasks in an epic are completed and before merging, creating a PR, or discarding work.
user_invokable: true
---

# Epic Review

## Overview

Dispatch four specialized reviewer agents to independently audit a completed epic, then synthesize their findings into a gate decision. Reviewers run in fresh context — they haven't seen the implementation process and have no sunk cost bias.

**Core principle:** The implementing context is the worst reviewer of its own work. Delegate review to fresh agents.

**Announce at start:** "I'm using gambit:epic-review to validate this implementation before finishing."

## Rigidity Level

LOW FREEDOM — Dispatch all four reviewers. Synthesize all findings. No approval if any reviewer finds gaps. No skipping reviewers for "simple" epics.

## Quick Reference

| Step | Action | STOP If |
|------|--------|---------|
| **1. Load Context** | Epic + tasks + changed files list | Can't load epic |
| **2. Prepare Brief** | Epic requirements + file list + base branch | Brief incomplete |
| **3. Dispatch Reviewers** | 4 agents in parallel | Any agent fails to run |
| **4. Synthesize** | Merge findings, resolve conflicts | — |
| **5. Implement Improvements** | Implement ALL reviewer improvements | Tests fail after changes |
| **6. Gate** | APPROVED or GAPS FOUND | Gaps → fix tasks, STOP |

## When to Use

- All epic subtasks show "completed"
- Before `gambit:finishing-branch`
- Called automatically by `gambit:executing-plans` Step 5

**Don't use when:**
- Tasks still in progress → use `gambit:executing-plans`
- Single task review → use `gambit:verification`
- Mid-implementation quality check → too early

## The Process

### Step 1: Load Context

```
TaskGet → epic (requirements, success criteria, anti-patterns)
TaskList → all subtasks (verify all completed)
```

```bash
git diff main...HEAD --name-only    # Changed files
git diff main...HEAD --stat         # Change summary
```

### Step 2: Prepare Review Brief

Build a brief that each reviewer agent will receive. Include:

1. **Epic requirements** — full text from TaskGet (requirements, success criteria, anti-patterns)
2. **Changed files** — the `--name-only` output
3. **Base branch** — what the diff is against

Do NOT include your opinions, implementation notes, or rationale. The reviewers should form their own conclusions from the code.

### Step 3: Dispatch Four Reviewers

Read the four reviewer instruction files from `reviewers/` within this skill's directory:
- `reviewers/conformance.md`
- `reviewers/security.md`
- `reviewers/quality.md`
- `reviewers/performance.md`

For each reviewer, dispatch a `general-purpose` agent. The prompt for each agent must contain:
1. The full contents of that reviewer's instruction file
2. The review brief (epic requirements + changed files list) appended after the instructions

```
Agent subagent_type="general-purpose" description="Conformance review" prompt="[conformance.md contents]\n\n---\n\n## Review Brief\n\n[brief]"
Agent subagent_type="general-purpose" description="Security review" prompt="[security.md contents]\n\n---\n\n## Review Brief\n\n[brief]"
Agent subagent_type="general-purpose" description="Quality review" prompt="[quality.md contents]\n\n---\n\n## Review Brief\n\n[brief]"
Agent subagent_type="general-purpose" description="Performance review" prompt="[performance.md contents]\n\n---\n\n## Review Brief\n\n[brief]"
```

**Critical:** Dispatch all four in ONE message so they run in parallel. Do not wait for one before dispatching the next.

Each reviewer will:
- Read the changed files independently
- Evaluate their dimensions with evidence
- Return findings as APPROVED or GAPS FOUND

### Step 4: Synthesize Findings

Collect all four reviewer reports. Present a unified summary:

```markdown
## Epic Review: [Epic Name]

### Conformance Review
**Verdict:** [APPROVED/GAPS FOUND]
[Key findings with evidence]

### Security Review
**Verdict:** [APPROVED/GAPS FOUND]
[Key findings with evidence]

### Quality Review
**Verdict:** [APPROVED/GAPS FOUND]
[Key findings with evidence]

### Performance Review
**Verdict:** [APPROVED/GAPS FOUND]
[Key findings with evidence]

### Gaps (if any)
[Consolidated blocking issues from all reviewers]

### Improvements to Implement
[Consolidated list from all reviewers — deduplicated if multiple reviewers flagged the same thing]

### Overall Verdict: APPROVED / GAPS FOUND
```

**Conflict resolution:** If reviewers disagree (e.g., one flags something another considers fine), err toward the finding. Investigate the specific concern before dismissing it.

**Deduplication:** If multiple reviewers flag the same improvement (e.g., both quality and performance suggest adding a LIMIT clause), consolidate into one item. Credit both reviewers but implement once.

### Step 5: Implement Improvements

Collect ALL items categorized as **Improvements** from all four reviewer reports. These are non-blocking findings that reviewers determined should be fixed before merge.

**You MUST implement every improvement.** Do not list them and move on. Do not defer them to a follow-up. Do not describe them as "non-blocking suggestions" and skip them. Reviewer improvements are work items, not commentary.

For each improvement:
1. Read the relevant code at the file:line the reviewer cited
2. Implement the change the reviewer described
3. Move to the next improvement

After implementing all improvements, run the project's test suite to verify nothing broke.

**The only valid reason to skip an improvement** is if the reviewer fundamentally misunderstood the code — their suggestion is incoherent or would break correctness. If skipping, you MUST document:
- What the reviewer suggested
- What they misunderstood (with evidence from the code)
- Why implementing it would be incorrect

"Low priority," "not blocking," or "can be done later" are NOT valid reasons to skip.

### Step 6: Gate Decision

**If APPROVED (all four reviewers approve and all improvements are implemented):**

Announce: "Epic review passed. All reviewer improvements implemented. Proceeding to finishing-branch."

Invoke `gambit:finishing-branch` directly via Skill tool.

**If GAPS FOUND (any reviewer finds gaps):**

```markdown
## Gaps Found — Cannot Proceed

### Issues by Reviewer
[Consolidated list with evidence and locations]

### Recommended Fix Tasks
- [Concrete task description for each gap]
```

Create fix tasks with `TaskCreate` for each gap. Set dependencies. Then STOP — return to `gambit:executing-plans` to implement fixes.

**Do NOT proceed to finishing-branch with gaps. Do NOT override reviewer findings. Do NOT proceed with unimplemented improvements.**

---

## Examples

### Good: Parallel Dispatch

```
# Read all four reviewer instruction files
# Build prompt = [reviewer instructions] + [review brief]
# ONE message, four general-purpose Agent calls:
Agent general-purpose: "[conformance.md] + [brief]"  (parallel)
Agent general-purpose: "[security.md] + [brief]"     (parallel)
Agent general-purpose: "[quality.md] + [brief]"      (parallel)
Agent general-purpose: "[performance.md] + [brief]"  (parallel)

# All four return findings independently
# Synthesize into unified verdict
```

### Bad: Sequential, Skipped, or Ignored

```
# WRONG: Only dispatching two reviewers
"Security isn't relevant for this config change"

# WRONG: Reviewing in main context instead of dispatching
"Let me just quickly check the architecture myself..."

# WRONG: Overriding a reviewer
"The quality reviewer flagged nolint pragmas but those are fine"

# WRONG: Not reading reviewer files, writing instructions inline
"I'll just tell the agent to check for security issues..."

# WRONG: Listing improvements without implementing them
"Non-blocking suggestions: consider extracting a helper..."
"None of these block the commit. Ready to commit."

# WRONG: Deferring improvements to follow-up work
"These are good ideas for a future PR."
```

## Critical Rules

1. **All four reviewers dispatched** — no skipping for "simple" epics
2. **Parallel dispatch** — one message, four agents
3. **No self-review** — main context prepares brief and synthesizes, does NOT review code
4. **Reviewer findings are authoritative** — don't override without investigation
5. **Any gap blocks** — one reviewer finding gaps = GAPS FOUND overall
6. **Brief is neutral** — don't include opinions or justifications in what you send reviewers
7. **All improvements implemented** — reviewer improvements are work items, not suggestions to acknowledge and skip

**Common rationalizations:**

| Excuse | Reality |
|--------|---------|
| "I already reviewed during implementation" | You're biased — that's why agents exist |
| "Security isn't relevant here" | Every project has an attack surface |
| "Performance review is overkill" | Dispatch it anyway — it's parallel, costs nothing |
| "The reviewer is being too strict" | Investigate the finding before dismissing |
| "I can review faster myself" | Speed isn't the goal — unbiased review is |
| "These are non-blocking suggestions" | Improvements are work items — implement them |
| "Good ideas for a future PR" | No. Implement now, before this merge |
| "None of these block the commit" | Improvements don't block the verdict, but they block the merge |

## Verification Checklist

- [ ] Epic loaded, all tasks confirmed completed
- [ ] Review brief prepared (requirements + changed files, no opinions)
- [ ] All four reviewers dispatched in single message
- [ ] All four reviewer reports collected
- [ ] Findings synthesized into unified summary
- [ ] ALL improvements from all reviewers implemented (or skipped with misunderstanding evidence)
- [ ] Tests pass after implementing improvements
- [ ] If APPROVED: invoked finishing-branch via Skill tool
- [ ] If GAPS: created fix tasks, STOPPED

## Integration

**Called by:**
- `gambit:executing-plans` (Step 5, replaces direct finishing-branch call)
- User via `/gambit:epic-review`

**Calls:**
- `gambit:finishing-branch` (if approved)

**Dispatches general-purpose agents (parallel) using reviewer instructions from:**
- `reviewers/conformance.md` — completeness, architecture, dead code
- `reviewers/security.md` — OWASP audit, secrets, auth, data exposure
- `reviewers/quality.md` — language idioms, linter circumvention, test quality
- `reviewers/performance.md` — scaling, N+1, resource management

**Call chain:**
```
executing-plans (all tasks done) → epic-review → finishing-branch
                                       ↓
                                 (if gaps: STOP → fix → re-review)
```
