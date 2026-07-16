---
name: review
description: Use after all tasks in an epic complete, after refactoring verifies, or before merging to main. Triggers when independent validation is needed that code meets requirements, has no security gaps, passes quality standards, and has no performance regressions. User phrases like "review this", "is this ready to merge", "validate the implementation".
user_invokable: true
---

# Review

## Overview

Dispatch four specialized reviewer agents to independently audit completed work once, then dispatch a dedicated verifier sub-agent to kill-or-keep each finding and freeze the survivors into a review ledger. Remediation closes that ledger; it does not restart an open-ended audit.

The verification work is delegated to a **dedicated verifier sub-agent**, not done in the main context. Main context's job is dispatch + assembly; the verifier's job is ruthless kill-or-keep classification. This split follows Anthropic's `CitationAgent` pattern and avoids the synthesizer becoming context-starved from juggling four simultaneous roles (dispatch, verify, dedup, implement).

Works in epic or standalone workflow context; either context has an initial-audit phase and a bounded closure phase:
- **Epic review:** When an epic Task exists, conformance checks against epic requirements and success criteria
- **Task review:** When reviewing standalone work (debugging, refactoring), conformance checks against the workflow Task's goal and success criteria

**Core principle:** Review is adversarial and broad once; closure is adversarial and narrow until the frozen findings are resolved.

**Announce at start:** "I'm using gambit:review to validate this implementation before finishing."

## Rigidity Level

LOW FREEDOM — Dispatch all four reviewers for the initial audit. Freeze its scope and confirmed-finding ledger. Never run a fresh audit to close that ledger unless the user explicitly expands requirements or implementation scope.

## Quick Reference

| Step | Action | STOP If |
|------|--------|---------|
| **1. Detect Context** | Epic Task/workflow Task + any open review ledger | Can't find either context |
| **2. Load Context** | Task + changed files list | Can't load task |
| **3. Freeze Boundary** | Requirements + base revision + review snapshot + changed hunks | Boundary incomplete |
| **4. Dispatch Reviewers** | Initial audit only: 4 agents in parallel, each reading instructions by path | Any agent fails to run |
| **5. Scope + Dedupe** | Reject out-of-boundary candidates; byte-identical dedupe only | — |
| **6. Dispatch Verifier** | 1 verifier sub-agent with the deduped candidate list | Verifier fails to run |
| **7. Freeze Ledger** | Confirmed findings become the complete, immutable blocker set | — |
| **8. Remediate / Close** | Fix ledger items; re-verify only open IDs + original gates | Evidence fails |
| **9. Gate** | APPROVED or OPEN LEDGER with verification counts | Ledger remains open → fix tasks, STOP |

## When to Use

- All epic subtasks show "completed" (called automatically by `gambit:executing-plans` Step 5)
- After `gambit:refactoring` completes changes (mandatory)
- Before `gambit:finishing-branch`
- Any time you want independent review of completed work

**Don't use when:**
- Tasks still in progress → use `gambit:executing-plans`
- Mid-implementation, per-task quality check → that's the `executing-plans` checkpoint quality gate's job (it reuses this skill's `quality` reviewer, scoped to one diff, when it escalates). This skill is the multi-dimension end-of-epic backstop, not the per-task gate.

## The Process

### Step 1: Detect Context

First detect an open **Review Closure Ledger** in the current workflow state. A ledger is open when a prior review recorded confirmed finding IDs and has not recorded terminal closure for all of them.

- **Open ledger found → closure mode.** Skip Steps 3–5 and all four finders. Load the frozen boundary and only the still-open ledger entries, then continue at Step 6 with `mode: closure`.
- **No open ledger → initial mode.** Determine what you're reviewing against below and run the full audit.

An old APPROVED report is not an open ledger. A ledger is invalidated only when the user explicitly changes requirements or authorizes implementation outside the recorded remediation boundary; then record why and begin a new initial review. Incidental scope creep is not a reason to restart review — remove it or return it to the worker.

**Epic context** (default when epic exists):
```
TaskList → find epic Task (subject starts with "Epic:")
TaskGet → epic (requirements, success criteria, anti-patterns)
TaskList → all subtasks (verify all completed)
```

**Task context** (refactoring or standalone work):
```
TaskList → find the workflow Task (most recent in-progress or just-completed Task)
TaskGet → task (goal, implementation steps, success criteria)
```

The review brief adapts based on which context is detected. If both exist (e.g., a refactor during an epic), prefer the epic context. Detect an open ledger from the prior review checkpoint and its fix Tasks before creating a new audit.

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

**Initial mode, both contexts:** freeze exact revisions before dispatch:
```bash
git merge-base main HEAD            # review_base
git rev-parse HEAD                  # review_snapshot
git diff <review_base>..<review_snapshot> --name-only
git diff --unified=0 <review_base>..<review_snapshot>  # frozen changed hunks
```

If tracked or untracked implementation changes are absent from `review_snapshot`, STOP. The audited snapshot must contain everything intended for merge.

### Step 3: Freeze Boundary and Prepare Brief

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

**Both contexts also include a frozen Review Boundary:**

- `review_base` and `review_snapshot`
- exact changed files and zero-context changed hunks between those revisions
- explicit requirements/success criteria from the approved contract or workflow brief
- this rule: every finding must anchor to a line changed in that frozen diff, including missing-test/docs/config findings via the changed line that creates the obligation

Commit history, checkpoint formatting, transcript/process compliance, unchanged code, and "while I was reading" observations are outside the gate unless an explicit approved requirement names them. Report such observations separately; they cannot become candidates, ledger entries, fix work, or reasons to restart review.

Do NOT include your opinions, implementation notes, or rationale. The reviewers should form their own conclusions from the code.

Before any finder dispatch, validate that the frozen Review Brief contains the actual frozen diff hunks from `review_base..review_snapshot`. An empty or missing hunk set is a composition failure: stop the review before any finder dispatch, and never dispatch a finder with nothing to review.

### Step 4: Dispatch Four Reviewers

Resolve the absolute path to this skill's `reviewers/` directory **once** (Glob `**/skills/review/reviewers/conformance.md` if you don't already know it). You pass this path to the agents — **do NOT read the reviewer files into this context.** The four reviewer files are ~8k tokens; reading them here and re-emitting them as prompts wastes ~18k tokens every review. Each agent reads its own instruction file in its own fresh context.

#### Executor resolution (Claude only)

Resolve `finder` exactly once through `contracts/executors.md` before emitting any of the four calls. Missing registry or a valid registry with no `finder` role selects native Claude and the native branch below, including its current finder-tier model resolution. Invalid registry stops the review before any finder dispatch; report the validation failure. A valid configured role selects the configured Codex branch. A configured call failure is fail-closed: stop and report with never native fallback.

Do not infer selection from MCP tool availability, resolve once per dimension, or mix branches. One resolution selects the executor for the complete four-finder dispatch.

#### Native Claude finder dispatch

In ONE message, emit exactly four `general-purpose` Agent calls, each at the **finder tier** (`model:` resolved per `contracts/models.md` — default most-capable, because a missed finding is unrecoverable; set `model:` explicitly, never `inherit`). Each prompt is just: (1) a directive to read and follow that agent's instruction file by path, then (2) the review brief.

```
Agent subagent_type="general-purpose" model="<finder tier — see contracts/models.md>" description="Conformance review" prompt="Read <abs>/reviewers/conformance.md — that file is your complete instructions; your FIRST action must be to Read it, then follow it exactly.\n\n## Review Brief\n\n[brief]"
Agent subagent_type="general-purpose" model="<finder tier — see contracts/models.md>" description="Security review"    prompt="Read <abs>/reviewers/security.md — that file is your complete instructions; your FIRST action must be to Read it, then follow it exactly.\n\n## Review Brief\n\n[brief]"
Agent subagent_type="general-purpose" model="<finder tier — see contracts/models.md>" description="Quality review"     prompt="Read <abs>/reviewers/quality.md — that file is your complete instructions; your FIRST action must be to Read it, then follow it exactly.\n\n## Review Brief\n\n[brief]"
Agent subagent_type="general-purpose" model="<finder tier — see contracts/models.md>" description="Performance review" prompt="Read <abs>/reviewers/performance.md — that file is your complete instructions; your FIRST action must be to Read it, then follow it exactly.\n\n## Review Brief\n\n[brief]"
```

**Parallelism is structural, not a reminder.** That single message contains four Agent calls and nothing else — no `Read` calls, no prose between them. Reading one reviewer file before each dispatch is *exactly* what forces the agents sequential; passing paths removes the read step, so there's nothing left to interleave. If you catch yourself using `Read` on a reviewer file, you've reverted to the old serializing pattern — stop and dispatch by path.

#### Configured Codex finder dispatch

When resolution selects configured Codex, `finder.tool` is the configured fully qualified MCP tool. Follow `contracts/async-dispatch.md` for the frozen wrapper, artifact, handle, waiting, envelope, and failure mechanics; this section defines only the review finders' site-specific wire arguments and gates. The dimension-to-contract mapping is immutable: conformance, security, quality, and performance must each receive its matching absolute reviewer path and must never be interchanged.

Each call is fresh and distinct: omit any `threadId` input and never continue one dimension's thread for another. Each complete Wire arguments object has `prompt`, `model`, `cwd`, `sandbox`, `approval-policy`, `developer-instructions`, and `config`. `model` maps from `finder.model`; `cwd` is the absolute repository/worktree path under review; `sandbox` is the configured, schema-required `read-only`; `approval-policy` maps from `finder.approval_policy`; and `config.model_reasoning_effort` maps from `finder.reasoning_effort`.

The prompt value contains only the dimension's absolute reviewer-contract path directive plus the same frozen Review Brief, byte-for-byte. Use these four complete structured objects as the opaque Wire arguments payloads in the async relay prompts:

```
conformance Wire arguments:
{
  "prompt": "Read <abs>/reviewers/conformance.md — that file is your complete instructions; your FIRST action must be to Read it, then follow it exactly.\n\n## Review Brief\n\n[identical frozen Review Brief]",
  "model": "<finder.model>",
  "cwd": "<absolute repository/worktree path>",
  "sandbox": "read-only",
  "approval-policy": "<finder.approval_policy>",
  "developer-instructions": "You are a subordinate read-only advisory finder. Reading and analyzing the material supplied in the frozen Review Brief and the single named reviewer-contract path is REQUIRED and is not repository discovery. The prohibition covers only exploration beyond the supplied brief and that named path. Do not orchestrate, invoke skills, spawn nested agents, discover tasks, expand scope, edit files, or execute commands or tests. Analyze only those supplied materials and return advisory findings.",
  "config": {
    "model_reasoning_effort": "<finder.reasoning_effort>",
    "web_search": "live",
    "plugins.\"gambit@personal\".enabled": false,
    "skills.include_instructions": false,
    "orchestrator.skills.enabled": false,
    "features.collab": false,
    "features.multi_agent_v2.enabled": false
  }
}
security Wire arguments:
{
  "prompt": "Read <abs>/reviewers/security.md — that file is your complete instructions; your FIRST action must be to Read it, then follow it exactly.\n\n## Review Brief\n\n[identical frozen Review Brief]",
  "model": "<finder.model>",
  "cwd": "<absolute repository/worktree path>",
  "sandbox": "read-only",
  "approval-policy": "<finder.approval_policy>",
  "developer-instructions": "You are a subordinate read-only advisory finder. Reading and analyzing the material supplied in the frozen Review Brief and the single named reviewer-contract path is REQUIRED and is not repository discovery. The prohibition covers only exploration beyond the supplied brief and that named path. Do not orchestrate, invoke skills, spawn nested agents, discover tasks, expand scope, edit files, or execute commands or tests. Analyze only those supplied materials and return advisory findings.",
  "config": {
    "model_reasoning_effort": "<finder.reasoning_effort>",
    "web_search": "live",
    "plugins.\"gambit@personal\".enabled": false,
    "skills.include_instructions": false,
    "orchestrator.skills.enabled": false,
    "features.collab": false,
    "features.multi_agent_v2.enabled": false
  }
}
quality Wire arguments:
{
  "prompt": "Read <abs>/reviewers/quality.md — that file is your complete instructions; your FIRST action must be to Read it, then follow it exactly.\n\n## Review Brief\n\n[identical frozen Review Brief]",
  "model": "<finder.model>",
  "cwd": "<absolute repository/worktree path>",
  "sandbox": "read-only",
  "approval-policy": "<finder.approval_policy>",
  "developer-instructions": "You are a subordinate read-only advisory finder. Reading and analyzing the material supplied in the frozen Review Brief and the single named reviewer-contract path is REQUIRED and is not repository discovery. The prohibition covers only exploration beyond the supplied brief and that named path. Do not orchestrate, invoke skills, spawn nested agents, discover tasks, expand scope, edit files, or execute commands or tests. Analyze only those supplied materials and return advisory findings.",
  "config": {
    "model_reasoning_effort": "<finder.reasoning_effort>",
    "web_search": "live",
    "plugins.\"gambit@personal\".enabled": false,
    "skills.include_instructions": false,
    "orchestrator.skills.enabled": false,
    "features.collab": false,
    "features.multi_agent_v2.enabled": false
  }
}
performance Wire arguments:
{
  "prompt": "Read <abs>/reviewers/performance.md — that file is your complete instructions; your FIRST action must be to Read it, then follow it exactly.\n\n## Review Brief\n\n[identical frozen Review Brief]",
  "model": "<finder.model>",
  "cwd": "<absolute repository/worktree path>",
  "sandbox": "read-only",
  "approval-policy": "<finder.approval_policy>",
  "developer-instructions": "You are a subordinate read-only advisory finder. Reading and analyzing the material supplied in the frozen Review Brief and the single named reviewer-contract path is REQUIRED and is not repository discovery. The prohibition covers only exploration beyond the supplied brief and that named path. Do not orchestrate, invoke skills, spawn nested agents, discover tasks, expand scope, edit files, or execute commands or tests. Analyze only those supplied materials and return advisory findings.",
  "config": {
    "model_reasoning_effort": "<finder.reasoning_effort>",
    "web_search": "live",
    "plugins.\"gambit@personal\".enabled": false,
    "skills.include_instructions": false,
    "orchestrator.skills.enabled": false,
    "features.collab": false,
    "features.multi_agent_v2.enabled": false
  }
}
```

Before launching any wrapper, expand `~/.claude/gambit/async-results/` to an absolute path and ensure the directory exists. If preparation fails, stop before launching any wrapper; do not fall back to native execution. Generate four collision-resistant unique absolute artifact paths under that prepared directory and store each expected path with its call before dispatch:

- conformance → `<conformance-artifact-path>`
- security → `<security-artifact-path>`
- quality → `<quality-artifact-path>`
- performance → `<performance-artifact-path>`

Build each anonymous wrapper's exact relay prompt from `contracts/async-dispatch.md`, using `finder.tool`, that dimension's complete Wire arguments object, and its stored expected artifact path. At the wrapper tier from `contracts/models.md`, emit one message containing all four background Agent wrapper calls and nothing else. Every wrapper is anonymous: never pass `name:`. Descriptions are unique and identify this review site and the dimension:

```
Agent subagent_type="gambit-wrapper" model="<wrapper tier — see contracts/models.md>" run_in_background=true description="Review configured finder: conformance" prompt="<exact relay prompt from contracts/async-dispatch.md with conformance Wire arguments and conformance artifact path>"
Agent subagent_type="gambit-wrapper" model="<wrapper tier — see contracts/models.md>" run_in_background=true description="Review configured finder: security" prompt="<exact relay prompt from contracts/async-dispatch.md with security Wire arguments and security artifact path>"
Agent subagent_type="gambit-wrapper" model="<wrapper tier — see contracts/models.md>" run_in_background=true description="Review configured finder: quality" prompt="<exact relay prompt from contracts/async-dispatch.md with quality Wire arguments and quality artifact path>"
Agent subagent_type="gambit-wrapper" model="<wrapper tier — see contracts/models.md>" run_in_background=true description="Review configured finder: performance" prompt="<exact relay prompt from contracts/async-dispatch.md with performance Wire arguments and performance artifact path>"
```

As the wrappers launch, record every handle using the complete `task_id → dispatch site → task/dimension → worktree → expected artifact path` mapping, with the review dimension in `task/dimension`, and restate all four mappings in checkpoint scratch state. Drain every launched handle to a terminal state with repeated bounded `TaskOutput block=true` calls on that same handle, continuing after nonterminal waits and never messaging a wrapper. Per the collection barrier, validate all four terminal results before judging the batch; never cancel or retry a wrapper, and never stop collection while a sibling remains live.

For each terminal result, require the exact envelope from `contracts/async-dispatch.md`; require that the envelope contains a non-empty string `threadId` containing no CR or LF and that the envelope's artifact path matches its stored expected artifact path exactly. Only after that match may you read only that exact-matched artifact; require a non-empty string `content`, then delete it after successful validation. The exact artifact content is that dimension's advisory reviewer report; discard its `threadId` after validation, never persist it, pass it to another call, or use it again. Feed all four advisory reports unchanged into Step 5.

A terminal wrapper error, malformed envelope, artifact-path mismatch, missing or empty artifact, non-string `threadId` or `content`, tool error, protocol error, timeout, empty response, missing or empty response field, non-string field, or malformed response is a configured call failure. After satisfying the collection barrier, stop and report the complete batch outcome; never retry natively or fall back to native execution. Never call `codex-reply`. Configured Codex output otherwise receives the same frozen-boundary filtering, byte-identical deduplication, candidate side-table handling, and native verifier adjudication as native output.

Each reviewer will:
- Read the changed files independently
- Evaluate their dimensions with evidence
- Fetch documentation or references from the web when local knowledge is insufficient or the code is sensitive/complex
- Attach a `**Verify by:**` line to every Gap and Improvement (required — see each reviewer file's "Verification Requirement" section)
- Return findings as APPROVED or GAPS FOUND

**Critical:** Reviewers are strictly advisory. They must NOT run tests, execute commands, or edit files. All tests are already passing by the time review runs — their job is code analysis only. They DO have access to `WebFetch` and `WebSearch` and should use them to validate edge cases, check API documentation, verify security patterns, or confirm language-specific behavior when they aren't confident from code reading alone.

### Step 5: Scope-Filter and Dedupe Candidate Findings

Collect the four reviewer reports into one candidate list. Each finding carries a `**Verify by:**` line; assign each finding an opaque `id` (any stable string — reviewer name + sequence works).

**Apply the frozen boundary mechanically before verification.** A candidate is eligible only when its cited anchor intersects a changed hunk in `review_base..review_snapshot`, or an explicit requirement directly names the non-code artifact it cites. Put rejected items in a non-blocking `Out of scope` audit trail with the failed boundary check. Do not send them to the verifier and do not create work from them.

**Dedupe on byte-identical `(path, line_range, Verify by:)` tuples only. Do NOT dedupe on semantic similarity.**

Semantic dedup ("these two findings sound alike, collapse them") silently drops true positives — different reviewers flagging the same line with *different* verify_by steps have different investigation paths, and losing one loses coverage. Only collapse when all three fields match byte-for-byte. The verifier handles near-duplicates downstream.

**Before dispatching to the verifier, build a side-table keyed by `id`** recording each finding's `category` (gap or improvement), `verify_by` (original reviewer text), and `reviewer` (which of the four emitted it). The verifier never sees this side-table. Retain it to route verdicts, build complete ledger entries, and author any fix briefs; losing it breaks closure.

The deduped list and frozen boundary go to the verifier in Step 6.

### Step 6: Dispatch Verifier Sub-Agent

The verifier always dispatches as a native Claude agent at the verifier tier. Never read the executor registry for `verifier`, and never route verifier work through `finder.tool`, even when the four finder reports came from configured Codex calls.

Dispatch ONE `general-purpose` agent at the **verifier tier** (`model:` per `contracts/models.md` — default most-capable; a cheap verifier is forbidden for code/security review, where verifying a subtle finding is as hard as finding it). As with the reviewers, **pass the path — do NOT read `verifier.md` into this context.** The candidate list IS passed inline (it's dynamic):

```
Agent subagent_type="general-purpose" model="<verifier tier — see contracts/models.md>" description="Verify candidates" prompt="Read <abs>/reviewers/verifier.md — that file is your complete instructions; your FIRST action must be to Read it, then follow it exactly.\n\nmode: initial\nreview_base: [revision]\nreview_snapshot: [revision]\n\n## Candidate Findings\n\n[deduped list with ids]"
```

**Do NOT include reviewer severity, category (Gap vs. Improvement), or reasoning chain in the candidate list.** The verifier receives the mode, frozen revisions, and only `id`, `path`, `line_range`, `body`, `verify_by` per candidate. Fresh context prevents anchoring. Retain stripped fields in the Step 5 side-table.

**Do NOT verify findings in the main context.** Main context's job is dispatch + assembly. The verifier is the single source of truth for classification.

Skip the verifier dispatch only if the candidate list is empty. Continue to Step 9 with an empty ledger; original criteria and the full project gate still require fresh evidence before APPROVED.

### Step 7: Assemble Findings From Verifier Output

The verifier returns one classification per candidate, each with `verdict`, `quoted_evidence`, `evidence_location`, `tool_calls_made`, `confidence`, and (for gaps) `gap_reason`.

Route by verdict, using the Step 5 side-table to recover each finding's original `category`:

- **confirmed** → keep in the final report as a finding. Preserve the reviewer's original body text and the verifier's `quoted_evidence` / `evidence_location`. Place the finding in the "Gaps" section if the side-table's `category` is `gap`, or the "Improvements to Implement" section if `improvement`.
- **gap** → surface in a "🔍 Couldn't verify" section of the final report. NOT a confirmed finding — a coverage boundary. Include the verifier's `gap_reason` verbatim.
- **refuted** → drop from the findings and the gate. But list each one **tersely in the "Refuted (dropped)" audit trail** (file:line + the reviewer's one-line claim + the verifier's quoted counter-evidence). This is the only window into the verifier's one documented failure mode — aggressive refutation suppressing a real bug. Do not act on refuted findings, create tasks for them, or let them block; the audit trail exists so you (and the user) can spot a bad refutation, not to re-litigate verdicts.

After the initial verdicts, create a **Review Closure Ledger** containing every confirmed finding and no others:

```yaml
review_base: <revision>
review_snapshot: <revision>
requirements: <approved contract/brief identity>
open:
  - id: <stable id>
    category: <gap|improvement>
    path: <path>
    line_range: <range in review_snapshot>
    body: <original claim>
    verify_by: <original check>
    evidence: <verifier quote + location>
```

The ledger is immutable: closure may change only an entry's status from open to resolved. Refuted, gap-classified, and boundary-rejected candidates stay in non-blocking audit trails and never enter later work. Preserve the complete ledger in the review checkpoint; fix work must reference its IDs.

### Step 8: Remediate and Close the Ledger

In initial mode, implement every confirmed improvement. Confirmed gaps become fix work through the owning workflow. A suggestion may be skipped only with code evidence that the reviewer misunderstood it; record that as a verifier-calibration issue, not a new finding.

After any remediation, enter closure mode. **Do not dispatch the four finders again.** Dispatch the verifier with only open ledger entries:

```
Agent subagent_type="general-purpose" model="<verifier tier — see contracts/models.md>" description="Close review ledger" prompt="Read <abs>/reviewers/verifier.md and follow it exactly.\n\nmode: closure\nreview_base: [revision]\nreview_snapshot: [original reviewed revision]\ncurrent_revision: [current HEAD]\n\n## Open Ledger Findings\n\n[original candidate fields for open IDs only]"
```

Interpret closure verdicts against the original claim:

- `refuted` → the original claim no longer holds; mark that ID resolved.
- `confirmed` → the defect remains; keep that same ID open.
- `gap` → resolution lacks evidence; keep that same ID open with the literal wall.

Then invoke `gambit:verification` to run each ledger item's targeted check, the original success criteria, and the full project gate. Verification may fail these declared claims but may not invent new ones. Check `review_snapshot..current_revision` for remediation scope: unrelated edits return to the worker for removal; they do not expand the ledger.

Newly noticed issues from the frozen snapshot, process/history concerns, and unrelated observations are non-blocking `Outside frozen review boundary` notes. They cannot reopen an ID or create one. Only explicit user-approved requirement or implementation-scope expansion invalidates the ledger and authorizes a new initial audit.

### Step 9: Gate Decision

**APPROVED** requires either zero confirmed findings in initial mode, or every ledger ID resolved in closure mode, plus green original criteria and full project gate. This is the terminal condition; proceed directly to `gambit:finishing-branch` and pass the fresh test evidence.

If entries remain open, report only those IDs with their evidence and complete fix briefs. Preserve the same ledger:

Create or update fix Tasks for the open IDs only, then STOP and return to `gambit:executing-plans` (or the owning standalone workflow). The task descriptions retain the ledger fields needed for closure.

Never create work from refuted, gap-classified-in-initial-mode, boundary-rejected, or newly noticed closure observations. Never replace closure with another full review merely because the verifier or tests found an open ledger item.

## Critical Rules

1. **All four reviewers dispatched once** — no skipping in initial mode; never dispatch them in closure mode
2. **Parallel dispatch, by path** — one message, four calls through the once-selected finder executor: native Agent calls or configured anonymous background wrapper calls, each carrying its reviewer path in the finder wire arguments. Never read reviewer/verifier files into main context or paste their contents into prompts: the read-before-each-dispatch is what serializes the finders and wastes ~18k tokens/review
3. **No self-review** — main context prepares brief and assembles, does NOT review or verify code
4. **Verifier is the single source of truth for classification** — do NOT override confirmed/refuted/gap verdicts; do NOT verify in the main context
5. **Any open ledger entry blocks** — closure must refute every original claim with evidence
6. **Brief is neutral** — don't include opinions or justifications in what you send reviewers
7. **Verifier sees no severity / no reasoning** — only `id`, `path`, `line_range`, `body`, `verify_by`; fresh context prevents anchoring
8. **All confirmed findings freeze** — the initial confirmed set is the complete ledger; later observations cannot join it
9. **Gap findings surface, not drop** — keep them in the report with the verifier's specific gap_reason so the user can investigate
10. **Refuted findings drop** — don't create fix tasks for verdicts the verifier returned refuted
11. **Dedupe byte-identical, never semantic** — collapsing similar-looking findings silently drops true positives
12. **Context detection is automatic** — epic if epic exists, task otherwise
13. **Retain the ledger** — preserve its boundary and full finding fields across fix waves; plan summaries are not storage
14. **Closure is terminal** — all IDs resolved + original gates green means APPROVED, not another audit

**Common rationalizations:**

| Excuse | Reality |
|--------|---------|
| "I already reviewed during implementation" | You're biased — that's why agents exist |
| "Security isn't relevant here" | Every project has an attack surface |
| "Performance review is overkill" | Dispatch it anyway — it's parallel, costs nothing |
| "These are non-blocking suggestions" | Improvements are work items — implement them |
| "It's just a small debugging fix" | Small fixes can introduce regressions. Review anyway |
| "The verifier refuted this but I think it's real" | Refuted is refuted. If you disagree, that's a prompt-calibration signal, not a gate-override |
| "A fresh review is safer after fixes" | It reopens the search space. Close the frozen ledger instead |
| "We missed this in round one" | Report it outside the frozen boundary; it cannot become closure work |
| "The checkpoint/commits aren't ideal" | Process artifacts do not block without an explicit approved requirement |

## Verification Checklist

- [ ] Context and open-ledger state detected before dispatch
- [ ] Initial boundary freezes requirements, revisions, files, and changed hunks
- [ ] All four reviewers dispatched once, in one message, for initial mode only
- [ ] All four reviewer reports collected with `Verify by:` on every finding
- [ ] Out-of-boundary candidates rejected; eligible candidates byte-identical deduped
- [ ] Side-table keyed by `id` built before verifier dispatch (category + verify_by + reviewer)
- [ ] Verifier sub-agent dispatched with candidate list (no severity, no reasoning chain)
- [ ] Verifier returned one verdict per candidate (confirmed / refuted / gap) with quoted evidence
- [ ] Confirmed findings frozen into the complete Review Closure Ledger
- [ ] Closure dispatched only the verifier with open ledger IDs
- [ ] Every original criterion, targeted fix check, and full project gate freshly passes
- [ ] Outside-boundary observations reported without creating work
- [ ] If APPROVED: invoked finishing-branch via Skill tool
- [ ] If OPEN: created/updated fix Tasks for open ledger IDs only, STOPPED

## Integration

**Called by:**
- `gambit:executing-plans` (Step 5, when all tasks complete)
- `gambit:refactoring` (mandatory, after final verification passes)
- User via `/gambit:review`

**Calls:**
- `gambit:finishing-branch` (if approved)

**Dispatches four finders (parallel, read-only) through native general-purpose agents or configured async wrapper calls. Native calls resolve the finder tier through `contracts/models.md`; configured calls use the registry's concrete model behind anonymous background wrappers. Each finder reads its own instruction file by path — main context never loads it:**
- `reviewers/conformance.md` — completeness, architecture, dead code
- `reviewers/security.md` — OWASP audit, secrets, auth, data exposure
- `reviewers/quality.md` — language idioms, linter circumvention, test quality
- `reviewers/performance.md` — scaling, N+1, resource management

**Dispatches one verification agent at the verifier tier (`contracts/models.md`), also by path:**
- `reviewers/verifier.md` — initial kill-or-keep classification; later bounded closure of the frozen ledger

**Call chain (epic context):**
```
executing-plans (all tasks done) → review → finishing-branch
                                      ↓
                           (if ledger open: STOP → fix → close ledger)
```

**Call chain (task context):**
```
refactoring (changes verified) → review → finishing-branch
                                    ↓
                         (if ledger open: STOP → fix → close ledger)
```
