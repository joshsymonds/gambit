---
name: debugging
description: Use when a test is failing, when a bug is reported, when behavior is unexpected or intermittent, when a build or integration step fails, or when a flaky test keeps resurfacing. Especially when "the fix seems obvious", when multiple previous fixes haven't stuck, or when under time pressure to ship.
---

# Debugging — Root Cause Investigation

## Overview

Debugging in gambit is **investigation, not fixing.** You reproduce the bug, gather evidence, trace to the true root cause, and write a test that *proves* you understand it. Then you hand that understanding to `gambit:brainstorming`, which designs the fix as an epic and runs it through the normal build pipeline.

Random fixes waste time and create new bugs. A fix for a symptom you don't understand is a guess wearing a confidence costume.

**Core principle:** Find the root cause with evidence before any fix is designed.

**Iron Law:** No fix designed without root-cause evidence AND a failing test that reproduces the bug. Think the fix is obvious? Prove it with evidence first. No exceptions.

**Announce at start:** "I'm using gambit:debugging to find the root cause."

## Rigidity Level

MEDIUM FREEDOM — Follow the investigation sequence; adapt the techniques to the bug in front of you. Non-negotiable: evidence before hypothesis, a failing test before handoff, fix the source not the symptom.

## Quick Reference

| Step | Action | STOP If |
|------|--------|---------|
| 1 | Reproduce & gather evidence | Can't reproduce consistently |
| 2 | Investigate root cause | Still guessing (no evidence) |
| 3 | Write failing test that captures the bug | Test passes (doesn't catch it) |
| 4 | Hand root cause to brainstorming | 3+ hypotheses already failed → question architecture |

**Terminal:** root cause + failing test → `gambit:brainstorming` designs and executes the fix. This skill does NOT fix, classify, or close — it understands, then hands off.

## When to Use

- Test failures, bugs, unexpected behavior, regressions, build failures, performance problems, flaky tests
- **Especially** under time pressure, after multiple failed fixes, or when "the fix seems obvious"

**Don't use for:** new features (`gambit:brainstorming`), refactoring (`gambit:refactoring`)

## The Process

### 1. Reproduce & Gather Evidence

**BEFORE forming any theory:**

1. **Read the error carefully** — stack traces, line numbers, error codes often contain the answer
2. **Reproduce consistently** — if intermittent, add instrumentation; if you can't reproduce it, **STOP** and gather more data
3. **Check recent changes** — `git log --oneline -10` and `git diff HEAD~5..HEAD -- path/to/affected/code`

**Multi-component path?** When the failing path crosses 3+ boundaries (CI → build → signing; handler → service → cache → DB), you can't reason out *which* component is broken from the error alone — instrument every boundary, run once, then investigate the layer the evidence points at. See [references/root-cause-tracing.md](references/root-cause-tracing.md#instrumenting-boundaries-in-multi-component-systems).

### 2. Investigate Root Cause

**Evidence before hypothesis. Use tools, not guessing.**

- **Search for context** — `WebSearch` for error messages. For bounded codebase investigation, Glob `**/contracts/scout.md`, dispatch `subagent_type: "Explore"` with `model:` at the scout tier (default cheap-or-standard; `contracts/models.md`), and prompt it to Read `contracts/scout.md` first, then ask the question. The scout returns `file:line` evidence or `NOT FOUND`.
- **Find a working neighbor and compare** — most codebases contain a near-neighbor of the broken path (another caller of the same function, another feature using the same library). Comparing working-vs-broken is faster than pure tracing and catches "configured differently" bugs. List **every** difference, not just the ones that seem relevant — "that can't matter" is how real bugs hide. Read the working reference *completely*.
- **Trace data flow backward** — find where the bad value *originates*, not where it crashes. A null check at the crash site is a symptom fix; finding *why* the value is null and preventing it at the source is a root-cause fix. Full technique: [references/root-cause-tracing.md](references/root-cause-tracing.md).
- **Form a hypothesis with evidence** — "I think X is the root cause because Y." Evidence = stack trace showing the call path, log output showing state, code showing missing validation, or test output showing the failure mode. **No evidence? STOP.** Keep investigating.

**Match the bug shape to a technique:**

| Bug shape | Technique |
|-----------|-----------|
| Flaky / timing-dependent test | [references/condition-based-waiting.md](references/condition-based-waiting.md) |
| "Which test pollutes shared state?" | [references/find-polluter.sh](references/find-polluter.sh) |
| Deep-stack bug, unclear origin | [references/root-cause-tracing.md](references/root-cause-tracing.md) |

### 3. Write the Failing Test (proof of understanding)

Write the smallest test that reproduces the bug. **Run it — it MUST fail.**

A failing test is how you *prove* you found the real bug instead of a plausible story. If it passes immediately, you don't understand the bug yet — return to step 2.

```python
def test_rejects_empty_email():
    # Reproduces the reported bug: empty email slips through registration
    _, err = create_user(User(email=""))
    assert err is not None, "expected validation error for empty email"
```

This test is the artifact you hand to brainstorming — it pins down exactly what "fixed" means.

### 4. Hand Off to Brainstorming

You now hold the two things a good fix needs: **the root cause (with evidence)** and **a failing test that captures it.** That's the seed of the fix epic.

**Default (almost always) — invoke `gambit:brainstorming`:**

```
Skill skill="gambit:brainstorming"
```

Tell it the investigation is done so it designs the fix rather than re-investigating. Feed it:
- **Root cause:** the source, with evidence (file:line, the backward trace)
- **Failing test:** make this pass — that's the immutable success criterion
- **Symptom location:** mark "patch here" as a forbidden anti-pattern
- Consider **defense-in-depth** ([references/defense-in-depth.md](references/defense-in-depth.md)) so the whole bug class becomes structurally impossible, not just this instance

Brainstorming turns this into an epic and routes it through `executing-plans` → `review` like any other work — that's where the fix gets written, verified, and reviewed.

**Fast path (one-liners only):** if the root cause is a genuine one-line change and the failing test fully guards it, just make the change and verify (test passes + full suite green). Don't spin up an epic for a typo. Anything larger than a one-liner → brainstorming.

**If 3+ hypotheses or fixes have already failed: STOP.** Each fix revealing a new problem elsewhere, or fixes that need "massive refactoring," means your root-cause model is wrong or the architecture is. Question fundamentals *with the user* before handing a shaky diagnosis to brainstorming.

---

## Critical Rules

### Rules That Have No Exceptions

1. **Evidence before hypothesis** → code path, logs, or test output showing WHY
2. **Reproduce before investigating** → can't reproduce → gather data, don't guess
3. **Failing test before handoff** → proves you caught the real bug, not a story
4. **Trace to the SOURCE** → fix where the bad value originates, not where it crashes
5. **3+ failed attempts → question architecture** → stop and discuss with the user
6. **Hand the root cause to brainstorming** → don't rebuild a fix-and-close pipeline here

### Common Excuses

All mean: **STOP. Return to steps 1–2.**

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need to investigate" | Simple issues have root causes too |
| "Emergency, no time to investigate" | Systematic is FASTER than thrashing |
| "Just try this fix first, then investigate" | First fix sets the pattern. Do it right. |
| "I'll write the test after I confirm the fix" | Untested fixes don't stick |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem |
| "Obviously X is the cause" | "Obvious" causes are often wrong. Get evidence. |

---

## Verification Checklist

- [ ] Bug reproduced consistently
- [ ] Root cause identified WITH evidence (not a plausible guess)
- [ ] Failing test reproduces the bug (RED)
- [ ] Root cause (not symptom) handed to brainstorming — or one-line fix verified green
- [ ] If 3+ attempts failed: architecture questioned with the user

**Can't check these?** Return to the process.

---

## References

- [references/root-cause-tracing.md](references/root-cause-tracing.md) — backward tracing, stack instrumentation, multi-component boundary logging
- [references/condition-based-waiting.md](references/condition-based-waiting.md) — fix flaky/timing tests by polling for the condition, not guessing a delay
- [references/defense-in-depth.md](references/defense-in-depth.md) — after root cause, validate at every layer so the bug class is impossible
- [references/find-polluter.sh](references/find-polluter.sh) — bisect which test pollutes shared state
- [REFERENCE.md](REFERENCE.md) — symptom-vs-root-cause and RED-GREEN worked examples

---

## Integration

**This skill calls:**
- Contracted scout agents through the active backend's native dispatch for bounded independent codebase investigation
- `WebSearch` for error-message research
- `gambit:brainstorming` (terminal — designs and executes the fix from the root cause)

**Called by:**
- A bug discovered during development, a failing test, a user-reported bug

**Workflow:**
```
Bug → reproduce → evidence → root cause → failing test → gambit:brainstorming → (epic → executing-plans → review)
```
