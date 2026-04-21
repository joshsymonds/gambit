---
name: review
description: Use after all tasks in an epic complete, after debugging finishes a fix, after refactoring verifies, or before merging to main. Triggers when independent validation is needed that code meets requirements, has no security gaps, passes quality standards, and has no performance regressions. User phrases like "review this", "is this ready to merge", "validate the implementation".
user_invokable: true
---

# Review

## Overview

Dispatch four specialized reviewer agents to independently audit completed work, then dispatch a dedicated verifier sub-agent to kill-or-keep each finding, then synthesize surviving findings into a gate decision. Reviewers and verifier run in fresh context — they haven't seen the implementation process and have no sunk cost bias.

The verification work is delegated to a **dedicated verifier sub-agent**, not done in the main context. Main context's job is dispatch + assembly; the verifier's job is ruthless kill-or-keep classification. This split follows Anthropic's `CitationAgent` pattern and avoids the synthesizer becoming context-starved from juggling four simultaneous roles (dispatch, verify, dedup, implement).

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
| **5. Dedupe Candidates** | Merge reviewer outputs; dedupe on byte-identical `(file, line, verify_by)` tuples | — |
| **6. Dispatch Verifier** | 1 verifier sub-agent with the deduped candidate list | Verifier fails to run |
| **7. Assemble Findings** | Route verifier verdicts: confirmed → kept, gap → surfaced, refuted → dropped | — |
| **8. Implement Improvements** | Implement ALL confirmed reviewer improvements | Tests fail after changes |
| **9. Gate** | APPROVED or GAPS FOUND with verification counts | Confirmed gaps → fix tasks, STOP |

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

### Step 5: Dedupe Candidate Findings

Collect the four reviewer reports into one candidate list. Each finding carries a `**Verify by:**` line; assign each finding an opaque `id` (any stable string — reviewer name + sequence works).

**Dedupe on byte-identical `(path, line_range, Verify by:)` tuples only. Do NOT dedupe on semantic similarity.**

Semantic dedup ("these two findings sound alike, collapse them") silently drops true positives — different reviewers flagging the same line with *different* verify_by steps have different investigation paths, and losing one loses coverage. Only collapse when all three fields match byte-for-byte. The verifier handles near-duplicates downstream.

**Before dispatching to the verifier, build a side-table keyed by `id`** recording each finding's `category` (gap or improvement), `verify_by` (original reviewer text), and `reviewer` (which of the four emitted it). The verifier never sees this side-table — it's the main context's private state. You need it back in Step 7 to route confirmed verdicts to the Gaps vs. Improvements sections, in Step 8 to identify which confirmed items are implementable improvements, and in Step 9 to render `Verify by` text in the GAPS FOUND template. Losing this mapping breaks all three steps.

The deduped list goes to the verifier in Step 6.

### Step 6: Dispatch Verifier Sub-Agent

Read `reviewers/verifier.md` within this skill's directory. Dispatch ONE `general-purpose` agent with the prompt structure:

```
Agent subagent_type="general-purpose" description="Verify candidates" prompt="[verifier.md contents]\n\n---\n\n## Candidate Findings\n\n[deduped list with ids]"
```

**Do NOT include reviewer severity, category (Gap vs. Improvement), or reasoning chain in the candidate list.** The verifier receives only: `id`, `path`, `line_range`, `body`, `verify_by`. Fresh context prevents the verifier anchoring on the reviewer's confidence. The stripped `category`, original `verify_by`, and `reviewer` are retained by main context in the Step 5 side-table — they're restored via `id` lookup after the verifier returns.

**Do NOT verify findings in the main context.** Main context's job is dispatch + assembly. The verifier is the single source of truth for classification.

Skip the verifier dispatch only if the candidate list is empty — in which case all reviewers returned APPROVED, and the overall verdict is APPROVED with zero findings.

### Step 7: Assemble Findings From Verifier Output

The verifier returns one classification per candidate, each with `verdict`, `quoted_evidence`, `evidence_location`, `tool_calls_made`, `confidence`, and (for gaps) `gap_reason`.

Route by verdict, using the Step 5 side-table to recover each finding's original `category`:

- **confirmed** → keep in the final report as a finding. Preserve the reviewer's original body text and the verifier's `quoted_evidence` / `evidence_location`. Place the finding in the "Gaps" section if the side-table's `category` is `gap`, or the "Improvements to Implement" section if `improvement`.
- **gap** → surface in a "🔍 Couldn't verify" section of the final report. NOT a confirmed finding — a coverage boundary. Include the verifier's `gap_reason` verbatim.
- **refuted** → drop entirely. Do not include in the report. Count only for calibration.

Present the unified summary:

```markdown
## Review: [Epic/Task Name]

### Verification Summary
- Candidates sent to verifier: [N]
- Confirmed (kept): [X]
- Refuted (dropped): [Y]
- Gaps (surfaced, not blocking): [Z]

### Conformance / Security / Quality / Performance Review
[Per-reviewer sections with only CONFIRMED findings, each carrying evidence]

### Gaps (confirmed blocking issues, if any)
[Consolidated blocking findings]

### Improvements to Implement (confirmed)
[Consolidated non-blocking improvements — one entry per unique issue, credit all reviewers who flagged it]

### 🔍 Couldn't verify (for your awareness, not blocking)
- [Area the reviewer wanted to check] — [verifier's specific gap_reason: tool + error, missing credential, inaccessible system]

### Overall Verdict: APPROVED / GAPS FOUND
```

**Conflict resolution is gone** — the verifier already picked. Do not override verifier verdicts. If a refuted finding looks correct to you, that's a calibration signal about reviewer or verifier prompts, not a reason to un-drop.

**Gap vs. dropped:** Gaps are literal walls the verifier ran into — tool failures, missing credentials, inaccessible systems. Not "evidence was ambiguous" (that's refuted). If the gap section is populated with prose like "couldn't confirm" or "plausible but hard to verify," those entries are badly-classified and should be refuted instead — treat them as calibration signal and drop.

### Step 8: Implement Improvements

Collect ALL items categorized as **Improvements** that the verifier returned `confirmed` for. These are non-blocking findings that reviewers determined should be fixed before merge, and that the verifier independently proved hold. Gap-classified findings are surfaced to the user but not auto-implemented — the user decides whether to investigate.

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

### Step 9: Gate Decision

The gate evaluates **confirmed** findings only. Refuted findings are dropped; gap-classified findings are surfaced to the user but don't block.

**If APPROVED (no confirmed gaps remain and all confirmed improvements are implemented):**

Announce: "Review passed. [N] candidates verified — [X] confirmed, [Y] refuted, [Z] gaps. All confirmed improvements implemented. Tests green (ran in Step 8 after improvements, or already green since review began and no code changed). Proceeding to finishing-branch."

Invoke `gambit:finishing-branch` directly via Skill tool. **Because tests are known-green at this handoff, finishing-branch will skip its own test run (its Step 2).** State this explicitly in your handoff announcement so finishing-branch knows tests were just verified.

**If GAPS FOUND (any confirmed gap remains):**

```markdown
## Gaps Found — Cannot Proceed

### Verification Summary
[X] confirmed / [Y] refuted / [Z] gaps

### Issues by Reviewer (confirmed only)
[Consolidated list with the verifier's `quoted_evidence` and `evidence_location`, plus the reviewer's original `Verify by` text recovered from the Step 5 side-table, attributed to the `reviewer` recorded there]

### Recommended Fix Tasks
- [Concrete task description for each confirmed gap]

### 🔍 Couldn't verify (for your awareness, not blocking)
- [Area] — [verifier's specific gap_reason]
```

Create fix tasks with `TaskCreate` for each confirmed gap. Set dependencies. Then STOP — return to `gambit:executing-plans` to implement fixes (for epic context) or address fixes directly (for task context).

**Do NOT proceed to finishing-branch with confirmed gaps. Do NOT override verifier verdicts. Do NOT proceed with unimplemented confirmed improvements. Do NOT create fix tasks for refuted findings — they were disproved for a reason. Do NOT create fix tasks for gap-classified findings — a gap means the verifier hit a literal wall, not that a bug exists.**

---

## Examples

### Good: Two-Stage Dispatch (reviewers → verifier)

```
# Stage 1: Read the four reviewer files. ONE message, four Agent calls, parallel:
Agent general-purpose: "[conformance.md] + [brief]"  (parallel)
Agent general-purpose: "[security.md] + [brief]"     (parallel)
Agent general-purpose: "[quality.md] + [brief]"      (parallel)
Agent general-purpose: "[performance.md] + [brief]"  (parallel)

# All four return findings independently. Dedupe on byte-identical tuples.

# Stage 2: Read verifier.md. ONE more Agent call, sequential:
Agent general-purpose: "[verifier.md] + [deduped candidate list]"

# Verifier returns confirmed/refuted/gap per candidate. Assemble final verdict.
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

# WRONG: Reviewing or verifying in main context instead of dispatching
"Let me just quickly check the architecture myself..."
"I'll verify these findings inline instead of spawning another agent..."

# WRONG: Skipping the verifier
"The findings look good, let's just implement them"

# WRONG: Overriding a verifier verdict
"The verifier refuted this but I think it's real"

# WRONG: Feeding the verifier reviewer severity/reasoning
Agent general-purpose: "[verifier.md] + [full reviewer reports with severity tags]"
# Correct: strip to id/path/line/body/verify_by only

# WRONG: Semantic dedup before the verifier
"Findings 2 and 5 look similar, collapse them"
# Correct: byte-identical (path, line, verify_by) tuples only

# WRONG: Creating fix tasks for gap-classified findings
"The gap says we couldn't check LaunchDarkly — add a fix task to check it"
# Correct: gap is a tool-access boundary, not a bug

# WRONG: Not reading reviewer/verifier files, writing instructions inline
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
3. **No self-review** — main context prepares brief and assembles, does NOT review or verify code
4. **Verifier is the single source of truth for classification** — do NOT override confirmed/refuted/gap verdicts; do NOT verify in the main context
5. **Any confirmed gap blocks** — one confirmed gap = GAPS FOUND overall
6. **Brief is neutral** — don't include opinions or justifications in what you send reviewers
7. **Verifier sees no severity / no reasoning** — only `id`, `path`, `line_range`, `body`, `verify_by`; fresh context prevents anchoring
8. **All confirmed improvements implemented** — confirmed improvements are work items, not suggestions to acknowledge and skip
9. **Gap findings surface, not drop** — keep them in the report with the verifier's specific gap_reason so the user can investigate
10. **Refuted findings drop** — don't create fix tasks for verdicts the verifier returned refuted
11. **Dedupe byte-identical, never semantic** — collapsing similar-looking findings silently drops true positives
12. **Context detection is automatic** — epic if epic exists, task otherwise
13. **Retain the id side-table** — stripping category/verify_by from verifier input (rule 7) means main context MUST keep an `id → {category, verify_by, reviewer}` side-table before dispatch; losing it breaks Steps 7–9 routing

**Common rationalizations:**

| Excuse | Reality |
|--------|---------|
| "I already reviewed during implementation" | You're biased — that's why agents exist |
| "Security isn't relevant here" | Every project has an attack surface |
| "Performance review is overkill" | Dispatch it anyway — it's parallel, costs nothing |
| "The reviewer is being too strict" | The verifier handles this — trust the verdict |
| "I can review faster myself" | Speed isn't the goal — unbiased review is |
| "These are non-blocking suggestions" | Improvements are work items — implement them |
| "Good ideas for a future PR" | No. Implement now, before this merge |
| "None of these block the commit" | Improvements don't block the verdict, but they block the merge |
| "It's just a small debugging fix" | Small fixes can introduce regressions. Review anyway |
| "The verifier refuted this but I think it's real" | Refuted is refuted. If you disagree, that's a prompt-calibration signal, not a gate-override |
| "This gap looks like a real bug to me" | A gap means the verifier hit a literal wall, not that a bug exists. If you suspect a bug, re-run review after fixing the tool-access issue the verifier cited |
| "I'll just skip the verifier for this small change" | The verifier is where the quality comes from. Main context cannot verify without anchoring |

## Verification Checklist

- [ ] Context detected (epic or task)
- [ ] Task/epic loaded, requirements/goal identified
- [ ] Review brief prepared (requirements/goal + changed files, no opinions)
- [ ] All four reviewers dispatched in single message
- [ ] All four reviewer reports collected with `Verify by:` on every finding
- [ ] Candidate list deduped on byte-identical `(path, line, verify_by)` tuples
- [ ] Side-table keyed by `id` built before verifier dispatch (category + verify_by + reviewer)
- [ ] Verifier sub-agent dispatched with candidate list (no severity, no reasoning chain)
- [ ] Verifier returned one verdict per candidate (confirmed / refuted / gap) with quoted evidence
- [ ] Findings assembled with verification counts (N confirmed / N refuted / N gaps)
- [ ] ALL **confirmed** improvements implemented (or skipped with misunderstanding evidence)
- [ ] Gap findings surfaced under "🔍 Couldn't verify" with specific gap_reason
- [ ] Refuted findings dropped, not converted into fix tasks
- [ ] Tests pass after implementing improvements
- [ ] If APPROVED: invoked finishing-branch via Skill tool
- [ ] If GAPS: created fix tasks for confirmed gaps only (NOT gap-classified), STOPPED

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

**Dispatches one verification agent (sequential, after reviewers, read-only) using:**
- `reviewers/verifier.md` — kill-or-keep each candidate finding with evidence, three-verdict enum (confirmed/refuted/gap)

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
