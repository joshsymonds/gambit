---
name: verification
description: Use this implementation mechanic to substantiate a completion or readiness claim only when explicitly invoked by name or called by an active Gambit workflow owner; do not select it implicitly as a peer workflow.
---

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always. Be adversarial about proof and closed about scope.

## Rigidity Level

LOW FREEDOM - NO exceptions. Run verification command, read output, THEN make claim.

Violating the letter of the rules is violating the spirit of the rules.

## Quick Reference

| Claim | Verification Required | Not Sufficient |
|-------|----------------------|----------------|
| **Tests pass** | Run full test command, see 0 failures | Previous run, "should pass" |
| **Build succeeds** | Run build, see exit 0 | Linter passing |
| **Bug fixed** | Test original symptom, passes | Code changed |
| **Linter clean** | Linter output: 0 errors | Partial check, extrapolation |
| **Regression test works** | Red-green cycle verified | Test passes once |
| **Task complete** | Check ALL success criteria individually | "Implemented the feature" |
| **Review closure** | Open ledger IDs + original criteria/gates | A fresh audit or new criteria |
<!-- gambit-backend:claude -->
| **All tasks done** | `TaskList` shows all completed | "All tasks done" |
<!-- /gambit-backend -->
<!-- gambit-backend:codex -->
| **Wave ready for checkpoint** | Every worker result and criterion is verified and readiness is reported to the owning workflow | Individual worker reports alone |
| **All waves done** | `SessionPlanRead` shows every wave step completed | "All work is done" |
<!-- /gambit-backend -->
| **Agent completed** | VCS diff shows changes | Agent reports "success" |

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in THIS message, you cannot claim it passes.

- Previous runs don't count (you changed code since then)
- Agent reports don't count (verify independently)
- Mental confidence doesn't count (run it)

**Verification is non-generative.** Freeze the claims before checking them: approved requirements, recorded success criteria, open review-ledger IDs, and named project gates. Try hard to disprove those claims. Do not invent additional requirements, style work, process audits, or review findings while verifying. Report newly noticed observations separately as non-blocking; route any requested scope expansion back to the owning workflow.

## Red Flags — STOP

If you catch yourself doing ANY of the following, you are about to claim completion without evidence. STOP and run verification before the next word you say or tool you call.

**Language signals:**
- Using hedging words: "should", "probably", "seems to", "I think", "ought to"
- Satisfaction expressions BEFORE evidence: "Great!", "Perfect!", "Done!", "All set!", "That does it!", "Ready to commit."
- Any sentence that implies success without naming the verification command you ran

**State signals:**
- About to commit / push / open a PR / mark a task completed — and you haven't run the command in THIS message
- Trusting a subagent's success report without reading the VCS diff
- Relying on a partial check (ran one file's tests, about to claim "tests pass")
- Previous verification is stale — you changed code since the last run

**Emotional / fatigue signals** (these are the ones that bypass rational guards):
- "I'm tired" / end-of-day exhaustion — fatigue pushes you toward claiming done so you can stop
- "Just this once" / "just one exception" — no such thing
- "I'm confident it works" — confidence without evidence is the exact failure mode this skill exists to prevent
- Eagerness to wrap up the conversation or move to the next task

**All of these mean: STOP. Run the verification command fresh. Read the output. THEN claim the result.**

## When to Use

**ALWAYS before:**
- Any success/completion claim
- Any expression of satisfaction ("Great!", "Perfect!", "Done!")
- Committing, PR creation, task completion
- Moving to next task

**Don't use for:** Deciding what to build (`gambit:brainstorming`), how to build it (`gambit:executing-plans`)

## The Process

### 1. Identify What Proves the Claim

Before making any completion claim, ask: "What command proves this?"

Write down the complete claim set first. A failed declared claim blocks completion; an observation outside that set does not silently become a claim.

| Claim Type | Verification |
|------------|-------------|
| Tests pass | Project's test command (`go test ./...`, `npm test`, etc.) |
| Build succeeds | Project's build command |
| Linter clean | Project's lint command |
| Task complete | Each success criterion verified individually |
<!-- gambit-backend:claude -->
| Epic complete | `TaskList` + each epic criterion verified |
<!-- /gambit-backend -->
<!-- gambit-backend:codex -->
| Epic complete | Every `SessionPlanRead` wave step completed + each approved-contract criterion verified |
<!-- /gambit-backend -->

### 2. Run the Command (Fresh)

Execute the FULL command. Not a partial run. Not a cached result.

**For verbose output:** Dispatch a general-purpose agent:

```
Task
  subagent_type: "general-purpose"
  model: "<test-runner tier — see contracts/models.md>"
  description: "Run verification"
  prompt: "Run: [command]. Report pass/fail counts, exit code, and any failures. Make no edits."
```

**For quick commands:** Run directly with Bash.

**Critical:** If you changed code since the last run, previous results are STALE. Run again.

### 3. Read the Output Completely

**Don't:**
- Skim for "PASS"
- Assume success from partial output
- Trust cached results

**Do:**
- Read complete output
- Count actual pass/fail numbers
- Check exit code

### 4. State Claim WITH Evidence

**If verification FAILS:** State actual status with evidence.

```
Tests: 33 passed, 1 failed.
Failure: test_login_with_expired_token still fails.
The fix didn't handle expired tokens.
Investigating...
```

**If verification PASSES:** State claim WITH evidence.

```
Tests pass. [Ran: go test ./..., Output: 34/34 passed, exit 0]
Ready to commit.
```

<!-- gambit-backend:claude -->
### 5. Task Completion: Verify Each Criterion

Before marking any task complete:

1. `TaskGet` — re-read success criteria
2. Verify EACH criterion with its own command/check
3. Report status of each individually
4. ONLY THEN mark complete

```
TaskGet taskId: "current-task-id"

→ Success criteria from task:
  1. POST /auth/login returns valid JWT
  2. Invalid password returns 401
  3. All tests pass

→ Verification:
  1. Ran: curl -X POST localhost:8080/auth/login -d '...'
     Output: {"token": "eyJ..."} — VERIFIED
  2. Ran: curl with wrong password
     Output: 401 {"error": "Invalid credentials"} — VERIFIED
  3. Ran: go test ./...
     Output: 34/34 passed, exit 0 — VERIFIED

→ All criteria verified.

TaskUpdate taskId: "current-task-id" status: "completed"
```

**For epic completion:** Run `TaskList` first, confirm ALL subtasks show completed, then verify epic-level criteria the same way.
<!-- /gambit-backend -->
<!-- gambit-backend:codex -->
### 5. Wave Completion: Verify Every Worker Criterion

Before reporting the current wave ready for its durable checkpoint:

1. Use `SessionContextRead` to reread the complete worker briefs for the current wave and the approved epic contract
2. Verify EACH worker criterion with its own command/check
3. Confirm individual worker completion from native subagent results and the root checkpoint, not plan records
4. Report every criterion's status
5. Report that the wave is ready for its durable checkpoint

The owning execution workflow performs the completion mutation only after it commits the verified wave and retains the full checkpoint plus any next-wave briefs in the root transcript. Verification never marks native wave state completed itself.

```
SessionContextRead → complete current-wave worker briefs

→ Success criteria from a worker brief:
  1. POST /auth/login returns valid JWT
  2. Invalid password returns 401
  3. All tests pass

→ Verification:
  1. Ran: curl -X POST localhost:8080/auth/login -d '...'
     Output: {"token": "eyJ..."} — VERIFIED
  2. Ran: curl with wrong password
     Output: 401 {"error": "Invalid credentials"} — VERIFIED
  3. Ran: go test ./...
     Output: 34/34 passed, exit 0 — VERIFIED

→ All worker criteria verified. Wave is ready for the owning execution workflow's durable checkpoint.
```

**For epic completion:** Run `SessionPlanRead` first and confirm every wave step is completed. Then use `SessionContextRead` to reread the approved epic contract and verify every epic-level criterion. Worker completion evidence comes from checkpoints and native subagent results.
<!-- /gambit-backend -->

---

## Critical Rules

### Rules That Have No Exceptions

1. **Fresh evidence required** → If you changed code since last run, previous results don't count
2. **Each criterion individually** → "Tests pass" doesn't verify "no TODOs remain"
3. **Agent results verified independently** → Check VCS diff, don't trust reports
4. **No hedging language as evidence** → "Should", "probably", "seems to" are not verification
5. **Full command, not partial** → Run the complete test suite, not just one file
6. **Closed claim set** → Verification challenges declared claims; it never expands requirements or a review ledger

### Common Excuses

All of these mean: **STOP. Run verification.**

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler ≠ tests |
| "Agent said success" | Verify independently |
| "Partial check is enough" | Partial proves nothing |
| "I already verified earlier" | You changed code since then |
| "Different words so rule doesn't apply" | Spirit over letter |
| "While verifying, I noticed another improvement" | Report it separately. Do not turn verification into a new review |

---

## Verification Checklist

Before any completion claim:
- [ ] Froze the complete claim set from approved criteria, open ledger IDs, and named gates
- [ ] Kept newly noticed observations outside that set non-blocking

Before claiming tests pass:
- [ ] Ran full test command (not partial)
- [ ] Saw output showing 0 failures
- [ ] Exit code was 0

Before claiming build succeeds:
- [ ] Ran build command (not just linter)
- [ ] Saw exit code 0

<!-- gambit-backend:claude -->
Before marking task complete:
- [ ] Re-read success criteria from task
- [ ] Ran verification for EACH criterion
- [ ] Saw evidence all pass
- [ ] THEN marked complete

Before marking epic complete:
- [ ] Ran `TaskList`
- [ ] Saw all subtasks completed
- [ ] Ran verification for epic success criteria
- [ ] THEN marked epic complete
<!-- /gambit-backend -->
<!-- gambit-backend:codex -->
Before reporting a wave ready for its durable checkpoint:
- [ ] Re-read every complete current-wave worker brief with `SessionContextRead`
- [ ] Ran verification for EACH worker criterion
- [ ] Confirmed individual worker completion from checkpoints/native subagent results
- [ ] Saw evidence all pass
- [ ] Reported readiness to the owning execution workflow without mutating native plan state

Before reporting the epic ready for review:
- [ ] Ran `SessionPlanRead`
- [ ] Saw every wave step completed
- [ ] Re-read the approved contract with `SessionContextRead`
- [ ] Ran verification for epic success criteria
- [ ] Reported epic readiness without mutating native plan state
<!-- /gambit-backend -->

**Can't check all boxes?** Return to the process.

---

## Examples

See [REFERENCE.md](REFERENCE.md) for detailed good/bad examples including:
- Claiming success without verification vs. verification before claim
- Closing task without criterion verification vs. verifying each criterion
- Trusting agent reports vs. independent verification
- Stale verification after code changes

---

## Integration

**This skill is called by:**
- `gambit:test-driven-development` (verify tests pass/fail)
- `gambit:executing-plans` (verify task success criteria)
- `gambit:debugging` (confirm the failing test reproduces the bug; verify a fast-path fix is green)
- ALL skills before completion claims

**This skill calls:**
- a test-runner-tier `general-purpose` agent (run + report, no edits — `contracts/models.md`) for running verbose commands

**Called by:**
- Any skill before marking work complete

**Workflow:**
```
About to claim completion
    ↓
Step 1: What command proves this?
    ↓
Step 2: Run it (fresh)
    ↓
Step 3: Read output completely
    ↓
Step 4: State claim WITH evidence
    ↓
Step 5: For tasks, verify EACH criterion
    ↓
Evidence confirms → Make claim
```
