---
name: review
description: Reviews completed implementation for quality, architecture, security, and completeness. Dispatches four specialized reviewer agents (conformance, security, quality, performance) in parallel for unbiased review. Use after all tasks in an epic are completed, after debugging, after refactoring, or before merging.
user_invokable: true
---

# Review

## Overview

Dispatch four specialized reviewer agents to independently audit completed work, then synthesize their findings into a gate decision. Reviewers run in fresh context — they haven't seen the implementation process and have no sunk cost bias.

Works in two modes:
- **Epic review:** When an epic Task exists, conformance checks against epic requirements and success criteria
- **Task review:** When reviewing standalone work (debugging, refactoring), conformance checks against the workflow Task's goal and success criteria

**Core principle:** The implementing context is the worst reviewer of its own work. Delegate review to fresh agents.

**Announce at start:** "I'm using gambit:review to validate this implementation before finishing."

## Rigidity Level

LOW FREEDOM — Dispatch all four reviewers. Synthesize all findings. No approval if any reviewer finds gaps. No skipping reviewers for "simple" changes.

## Quick Reference

| Step | Action | STOP If |
|------|--------|---------|
| **1. Detect Context** | Epic Task or workflow Task | Can't find any Task |
| **2. Load Context** | Task + changed files list | Can't load task |
| **3. Prepare Brief** | Requirements/goal + file list + base branch | Brief incomplete |
| **4. Dispatch Reviewers** | 4 agents in parallel | Any agent fails to run |
| **5. Verify Findings** | Skeptically re-check every finding's `Verify by:` | — |
| **6. Synthesize** | Merge confirmed findings, resolve conflicts | — |
| **7. Implement Improvements** | Implement ALL confirmed reviewer improvements | Tests fail after changes |
| **8. Gate** | APPROVED or GAPS FOUND with verification counts | Gaps → fix tasks, STOP |

## When to Use

- All epic subtasks show "completed" (called automatically by `gambit:executing-plans` Step 5)
- After `gambit:debugging` completes a fix (mandatory)
- After `gambit:refactoring` completes changes (mandatory)
- Before `gambit:finishing-branch`
- Any time you want independent review of completed work

**Don't use when:**
- Tasks still in progress → use `gambit:executing-plans`
- Mid-implementation quality check → too early

## The Process

### Step 1: Detect Context

Determine what you're reviewing against:

**Epic context** (default when epic exists):
```
TaskList → find epic Task (subject starts with "Epic:")
TaskGet → epic (requirements, success criteria, anti-patterns)
TaskList → all subtasks (verify all completed)
```

**Task context** (debugging, refactoring, or standalone work):
```
TaskList → find the workflow Task (most recent in-progress or just-completed Task)
TaskGet → task (goal, implementation steps, success criteria)
```

The review brief adapts based on which context is detected. If both exist (e.g., debugging during an epic), prefer the epic context.

### Step 2: Load Context

**For epic context:**
```
TaskGet → epic (requirements, success criteria, anti-patterns)
TaskList → all subtasks (verify all completed)
```

**For task context:**
```
TaskGet → workflow task (goal, success criteria)
```

**Both contexts:**
```bash
git diff main...HEAD --name-only    # Changed files
git diff main...HEAD --stat         # Change summary
```

### Step 3: Prepare Review Brief

Build a brief that each reviewer agent will receive. Include:

**For epic context:**
1. **Epic requirements** — full text from TaskGet (requirements, success criteria, anti-patterns)
2. **Changed files** — the `--name-only` output
3. **Base branch** — what the diff is against

**For task context:**
1. **Task goal and success criteria** — full text from TaskGet
2. **Changed files** — the `--name-only` output
3. **Base branch** — what the diff is against
4. **Context type indicator** — "This is a task-level review (debugging/refactoring), not an epic review. Evaluate against the task's stated goal and success criteria."

Do NOT include your opinions, implementation notes, or rationale. The reviewers should form their own conclusions from the code.

### Step 4: Dispatch Four Reviewers

Read the four reviewer instruction files from `reviewers/` within this skill's directory:
- `reviewers/conformance.md`
- `reviewers/security.md`
- `reviewers/quality.md`
- `reviewers/performance.md`

For each reviewer, dispatch a `general-purpose` agent. The prompt for each agent must contain:
1. The full contents of that reviewer's instruction file
2. The review brief (requirements/goal + changed files list) appended after the instructions

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
- Fetch documentation or references from the web when local knowledge is insufficient or the code is sensitive/complex
- Attach a `**Verify by:**` line to every Gap and Improvement (required — see each reviewer file's "Verification Requirement" section)
- Return findings as APPROVED or GAPS FOUND

**Critical:** Reviewers are strictly advisory. They must NOT run tests, execute commands, or edit files. All tests are already passing by the time review runs — their job is code analysis only. They DO have access to `WebFetch` and `WebSearch` and should use them to validate edge cases, check API documentation, verify security patterns, or confirm language-specific behavior when they aren't confident from code reading alone.

### Step 5: Verify Findings (Skeptical, Non-Trusting Re-Check)

Sub-agent reports arrive with a `**Verify by:**` line attached to every Gap and Improvement. **Treat these as proposals, not authority.** Reviewers can be wrong in two ways: they can emit confident-but-wrong findings (hallucinations), or they can emit findings with lazy/tautological `Verify by:` steps that pass a shallow check while the underlying claim is false. You are the quality gate. Re-check each finding yourself with the same tools the reviewers had.

#### Skepticism checklist (run on every finding before executing its Verify by)

1. **Does this `Verify by:` actually test the claim in the finding body?** A lazy verify-by might say "Read the file" while the body claims a race condition that can't be verified by reading one line. If the verify-by and body don't match, design your own verification — don't run a shallow check and rubber-stamp.
2. **Could the `Verify by:` pass while the finding is still wrong?** Tautological verify-bys ("confirm line 42 exists") always pass but prove nothing about the claim. If yes, the verify-by is insufficient — add the checks it's missing.
3. **Does the `Verify by:` cover all reasonable angles?** A finding about a missing `LIMIT` clause needs a grep for `LIMIT` AND a check for alternative bounds (subquery, upstream filter). A finding about a race condition needs the invariant traced through every caller.

#### Running the verification

After the skepticism pass:

1. Run the reviewer's proposed `Verify by:` steps.
2. Run any additional checks you identified in the skepticism pass.
3. Re-read the cited file + line directly. The most common reviewer failure mode is emitting a claim about a file they didn't read carefully — e.g. asserting a SQL query lacks `LIMIT 1` when the file plainly includes `LIMIT 1`. Re-read even when the reviewer sounded confident.

#### Classify each finding

- **Confirmed** — the full chain of reasoning in the finding holds after your independent checks. Keep in the synthesis.
- **Unverifiable** — you tried your verification AND any additional checks from the skepticism pass, and you genuinely cannot confirm (tool failed, cited file doesn't exist, evidence ambiguous, requires access you don't have). Keep in the synthesis with a one-sentence "unverifiable because: ..." note so the user can investigate or dismiss.
- **Refuted** — you re-read the evidence and the finding is factually wrong (e.g., claims a field is missing but it's right there; claims a function is called in a hot loop but it isn't; a tautological `Verify by:` that passes without testing the claim). Drop. Record only as a count in the synthesis for calibration.

**False positives damage reviewer credibility. Silent drops hide real bugs. Refute only when you have positive evidence the finding is wrong; surface as unverifiable (with reason) when you simply couldn't confirm; confirm only when the full claim chain holds under your skeptical re-check.**

### Step 6: Synthesize Findings

Collect all four reviewer reports with your verification classifications. Present a unified summary:

```markdown
## Review: [Epic/Task Name]

### Verification Summary
- Sub-agent findings received: [N]
- Confirmed (kept): [N]
- Unverifiable (surfaced with reason): [N]
- Refuted (dropped): [N]

### Conformance Review
**Verdict:** [APPROVED/GAPS FOUND]
[Confirmed findings with evidence]

### Security Review
**Verdict:** [APPROVED/GAPS FOUND]
[Confirmed findings with evidence]

### Quality Review
**Verdict:** [APPROVED/GAPS FOUND]
[Confirmed findings with evidence]

### Performance Review
**Verdict:** [APPROVED/GAPS FOUND]
[Confirmed findings with evidence]

### Gaps (confirmed, if any)
[Consolidated blocking issues that survived verification]

### Improvements to Implement (confirmed)
[Consolidated list from all reviewers — deduplicated if multiple reviewers flagged the same thing]

### Unverifiable Findings (surfaced, not blocking)
1. [Finding body]
   **Unverifiable because:** [One sentence — tool failed, requires production access, etc.]

### Overall Verdict: APPROVED / GAPS FOUND
```

**Conflict resolution:** If reviewers disagree (e.g., one flags something another considers fine), err toward the finding. Investigate the specific concern before dismissing it.

**Deduplication:** If multiple reviewers flag the same improvement (e.g., both quality and performance suggest adding a LIMIT clause), consolidate into one item. Credit both reviewers but implement once.

**Unverifiable vs. dropped:** Unverifiable findings stay in the report with a caveat — the user still sees them. Refuted findings are dropped and only counted. This prevents silent loss of real bugs while blocking confident-but-wrong hallucinations.

### Step 7: Implement Improvements

Collect ALL items categorized as **Improvements** (confirmed status) from all four reviewer reports. These are non-blocking findings that reviewers determined should be fixed before merge, and that you independently confirmed in Step 5. Unverifiable improvements are surfaced to the user but not auto-implemented — the user decides.

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

### Step 8: Gate Decision

The gate evaluates **confirmed** findings only. Refuted findings are dropped; unverifiable findings are reported to the user but don't block.

**If APPROVED (no confirmed gaps remain and all confirmed improvements are implemented):**

Announce: "Review passed. [N] sub-agent findings checked — [X] confirmed, [Y] unverifiable, [Z] refuted. All confirmed improvements implemented. Proceeding to finishing-branch."

Invoke `gambit:finishing-branch` directly via Skill tool.

**If GAPS FOUND (any confirmed gap remains):**

```markdown
## Gaps Found — Cannot Proceed

### Verification Summary
[X] confirmed / [Y] unverifiable / [Z] refuted

### Issues by Reviewer (confirmed only)
[Consolidated list with evidence, locations, and the Verify by each reviewer provided]

### Recommended Fix Tasks
- [Concrete task description for each confirmed gap]

### Unverifiable Findings (for your awareness, not blocking)
- [Finding body] — Unverifiable because: [reason]
```

Create fix tasks with `TaskCreate` for each confirmed gap. Set dependencies. Then STOP — return to `gambit:executing-plans` to implement fixes (for epic context) or address fixes directly (for task context).

**Do NOT proceed to finishing-branch with confirmed gaps. Do NOT override confirmed reviewer findings. Do NOT proceed with unimplemented confirmed improvements. Do NOT create fix tasks for refuted findings — they were disproved for a reason.**

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

### Good: Task-Level Review After Debugging

```
# Context detection: no epic, found debugging Task #5
# TaskGet #5 → goal: "Fix race condition in connection pool"
# Brief includes task goal + success criteria + changed files
# All four reviewers dispatched with task-level brief
# Conformance checks fix addresses stated goal
# Security checks no new vulnerabilities introduced
# Quality checks code quality of the fix
# Performance checks fix doesn't regress performance
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

# WRONG: Skipping review for "small" debugging fixes
"This was just a one-line fix, no need for four reviewers"
```

## Critical Rules

1. **All four reviewers dispatched** — no skipping for "simple" changes
2. **Parallel dispatch** — one message, four agents
3. **No self-review** — main context prepares brief and synthesizes, does NOT review code
4. **Reviewer findings are proposals, not authority** — run the skepticism checklist on every finding's `Verify by:`, then re-check independently
5. **Any confirmed gap blocks** — one confirmed gap = GAPS FOUND overall
6. **Brief is neutral** — don't include opinions or justifications in what you send reviewers
7. **All confirmed improvements implemented** — confirmed reviewer improvements are work items, not suggestions to acknowledge and skip
8. **Unverifiable findings surface, not drop** — keep them in the report with a reason so the user can investigate
9. **Refuted findings drop** — don't create fix tasks for findings your verification disproved
10. **Context detection is automatic** — epic if epic exists, task otherwise

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
| "It's just a small debugging fix" | Small fixes can introduce regressions. Review anyway |
| "The reviewer said they verified it, so it's fine" | Reviewers self-reporting verification is how false positives ship. Re-check with the skepticism checklist |
| "The Verify by: looks reasonable, skip the skepticism pass" | Lazy Verify-bys pass shallow checks. Audit them before running them |

## Verification Checklist

- [ ] Context detected (epic or task)
- [ ] Task/epic loaded, requirements/goal identified
- [ ] Review brief prepared (requirements/goal + changed files, no opinions)
- [ ] All four reviewers dispatched in single message
- [ ] All four reviewer reports collected with `Verify by:` on every finding
- [ ] Skepticism checklist run on each finding's `Verify by:`
- [ ] Each finding independently re-checked and classified (confirmed / unverifiable / refuted)
- [ ] Findings synthesized with verification counts (N confirmed / N unverifiable / N refuted)
- [ ] ALL **confirmed** improvements implemented (or skipped with misunderstanding evidence)
- [ ] Unverifiable findings surfaced to the user, not dropped
- [ ] Refuted findings dropped, not converted into fix tasks
- [ ] Tests pass after implementing improvements
- [ ] If APPROVED: invoked finishing-branch via Skill tool
- [ ] If GAPS: created fix tasks for confirmed gaps only, STOPPED

## Integration

**Called by:**
- `gambit:executing-plans` (Step 5, when all tasks complete)
- `gambit:debugging` (mandatory, after fix is verified)
- `gambit:refactoring` (mandatory, after final verification passes)
- User via `/gambit:review`

**Calls:**
- `gambit:finishing-branch` (if approved)

**Dispatches general-purpose agents (parallel, read-only) using reviewer instructions from:**
- `reviewers/conformance.md` — completeness, architecture, dead code
- `reviewers/security.md` — OWASP audit, secrets, auth, data exposure
- `reviewers/quality.md` — language idioms, linter circumvention, test quality
- `reviewers/performance.md` — scaling, N+1, resource management

**Call chain (epic context):**
```
executing-plans (all tasks done) → review → finishing-branch
                                      ↓
                                (if gaps: STOP → fix → re-review)
```

**Call chain (task context):**
```
debugging/refactoring (fix verified) → review → finishing-branch
                                          ↓
                                    (if gaps: STOP → fix → re-review)
```
