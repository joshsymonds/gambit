---
name: task-refinement
description: Use this implementation mechanic to refine prepared work briefs only when explicitly invoked by name or called by an active Gambit workflow owner; do not select it implicitly as a peer workflow.
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

# Task Refinement

## Overview

Review complete worker briefs systematically. Find gaps, fix them, present each revised brief in full, and reread it from the root transcript. A brief is ready when a junior engineer can execute it without asking questions.

**Core principle:** Don't just identify problems — revise each worker brief, present it in full, then reread it with `SessionContextRead` to verify.

**Iron Law:** NO worker brief passes review with vague criteria, missing file paths, or placeholder text. Every brief must be executable by a junior engineer without questions. No exceptions.

## Rigidity Level

LOW FREEDOM — Apply all 8 categories to every worker brief. No skipping. Present revised briefs in full, then verify no placeholders remain. Reject plans with critical gaps.

## Quick Reference

| Category | Key Check | Auto-Reject If |
|----------|-----------|----------------|
| 1. Granularity | Scoped to one sitting (~15-45m)? | Any worker brief without breakdown estimate |
| 2. Implementability | Junior executes without questions? | Vague language, missing file paths |
| 3. Success Criteria | Measurable, verifiable? | "Works correctly", "is implemented" |
| 4. Dependencies | Correct blocking order? | Circular or missing dependencies |
| 5. Anti-patterns | Forbidden patterns specified? | No anti-patterns section |
| 6. Edge Cases | Empty/unicode/concurrent/failure? | No edge case consideration |
| 7. Red Flags | Placeholder text? TODOs? | "[detailed above]", "[as specified]" |
| 8. Test Quality | Tests catch real bugs? | Tautological or happy-path-only tests |

## When to Use

- Before `gambit:executing-plans` starts implementation
- After `gambit:brainstorming` presents complete first-wave worker briefs
- When reviewing any plan for quality before execution

**Don't use for:**
- A worker brief whose wave is already in progress (too late)
- Creating plans from scratch → `gambit:brainstorming`
- Debugging → `gambit:debugging`

## The Process

### 1. Load the Contract, Wave Plan, and Worker Briefs

Use `SessionPlanRead` to inspect only the root session's concise wave steps and statuses. Then use `SessionContextRead` to reread the complete approved epic contract and every full worker brief from the root transcript or latest checkpoint. Do not infer individual worker records from the plan.

### 2. Review Each Worker Brief (All 8 Categories)

For each worker brief, apply every category. No skipping — "straightforward" briefs hide the worst edge cases.

#### Category 1: Granularity

- Each worker brief completable in one focused sitting (~15-45 min)?
- Large briefs split into focused briefs with clear deliverables?
- Each resulting brief independently completable?

**If too large:** Split it into complete focused worker briefs in the root transcript. Use `SessionPlanWrite` only to replace the complete plan when the concise wave summary or ordering changes; represent prerequisites through later waves, never dependency edges.

#### Category 2: Implementability

- Can a junior engineer execute without asking questions?
- All file paths specified (or marked "TBD: new file")?
- Function signatures/behaviors described, not just "implement X"?
- "Done" clearly defined?

**Red flags:** "Implement properly", "Add support", "Make it work", missing file paths.

#### Category 3: Success Criteria

- Each worker brief has 3+ specific, measurable criteria?
- All criteria verifiable with a command or code review?
- No subjective criteria?

**Rewrite vague criteria into measurable ones:**
- "Authentication works" → "POST /auth/login with valid creds returns 200 + JWT; invalid creds returns 401"
- "Code is good quality" → "Lint clean, no TODOs, no panic/unwrap in production code"
- "Tests pass" → "Run `npm test`, 0 failures, exit 0"

#### Category 4: Wave Order

- Prerequisite work appears in an earlier wave?
- Every parallel wave is represented by one plan step?
- At most one wave is in progress?

Verify the concise wave list with `SessionPlanRead`; verify the complete worker briefs with `SessionContextRead`.

#### Category 5: Anti-patterns

- Worker brief specifies what NOT to do?
- Includes: no TODOs without issue refs, no stub implementations, no swallowed errors?
- Error handling requirements specified?

#### Category 6: Edge Cases

**Ask for each worker brief:**
- What happens with empty/nil/zero input?
- What happens with malformed input?
- What about Unicode, special characters, large inputs?
- What about concurrent access?
- What when dependencies fail?

**Add findings to the complete worker brief's Key Considerations section, then present the revised brief in full.** See [REFERENCE.md](REFERENCE.md) for edge case examples.

#### Category 7: Red Flags (AUTO-REJECT)

**If any found, REJECT the plan:**
- Placeholder text: "[detailed above]", "[as specified]", "[complete steps here]"
- Vague instructions: "implement properly", "add support"
- Unverifiable criteria: "code is good", "works well"
- "We'll handle this later" or "TODO" in the plan itself
- Missing test specifications

#### Category 8: Test Quality

**Tests must catch real bugs, not inflate coverage.**

For each test specification, ask:
- What specific bug would this test catch?
- Could production code break while this test passes?
- Does the assertion verify behavior, not just existence?

**Reject:** Tests that only verify syntax/existence, tautological tests, tests without meaningful assertions, generic test names ("test_basic").

See [REFERENCE.md](REFERENCE.md) for good/bad test examples.

---

### 3. Present Each Revised Worker Brief

After reviewing, present each revised full worker brief in the root transcript. Never pass the full brief to `SessionPlanWrite`:

```
Present as "Revised Worker Brief: [worker subject]":
    [Original content, preserved and strengthened]

    ## Key Considerations (ADDED BY REVIEW)

    **Edge Case: [Name]**
    - [What could go wrong]
    - MUST [specific mitigation]

    ## Anti-patterns
    [Original anti-patterns]
    - NEW: [Specific anti-pattern for this worker brief's risks]
```

**Rules for updates:**
- Preserve original intent
- Strengthen vague criteria into measurable ones
- Replace ALL placeholder text with actual content
- Add edge case analysis

---

### 4. Verify Updates (MANDATORY)

**After revising a brief, present the revised full worker brief in the root transcript. Use `SessionPlanWrite` only when its concise wave summary, order, or status changes; every such call replaces the complete ordered plan. Then use `SessionContextRead` to verify the full brief:**

```
SessionContextRead
  read: "revised worker brief from this root transcript"
```

Check:
- All sections contain actual content (not placeholders)
- Success criteria are measurable
- Edge cases addressed
- File paths specified
- No "[detailed above]", "[as specified]", or similar

**If ANY placeholder found:** Rewrite with actual content immediately.

---

### 5. Present Results

```markdown
## Plan Review Results

### Overall: [APPROVE / NEEDS REVISION / REJECT]

### Worker Brief by Worker Brief

#### [Worker Brief]
**Status**: [Ready / Needs Revision / Rejected]
**Issues Found**: [count]
**Improvements Made**:
- [What was fixed]
**Edge Cases Added**:
- [What failure modes now addressed]

[Repeat for each worker brief]

### Summary
- Worker briefs revised and presented in full: [list]
- Concise wave summary/order/status changes: [list or none]
- Critical issues found: [count]
- Recommendation: [approve/revise/reject with reasoning]
```

---

## Critical Rules

### Rules That Have No Exceptions

1. **Apply all 8 categories to every worker brief** — no skipping any category
2. **Reject plans with placeholder text** — "[detailed above]" = instant reject
3. **Verify every revised brief** — present it in full, then reread it with `SessionContextRead`; update the complete wave list only for concise summary/order/status changes
4. **Strengthen vague criteria** — "works correctly" must become measurable commands
5. **Add edge cases to every worker brief** — empty, unicode, concurrency, failure modes
6. **Reject tautological tests** — tests must catch specific bugs

### Common Excuses

All mean: **STOP. Apply the full checklist.**

| Excuse | Reality |
|--------|---------|
| "Worker brief looks straightforward" | Edge cases hide in "straightforward" briefs |
| "Has 3 criteria, meets minimum" | Criteria must be MEASURABLE, not just 3+ items |
| "Placeholder is just formatting" | Placeholder = incomplete specification |
| "Can handle edge cases during implementation" | Must specify upfront to prevent rework |
| "Junior will figure it out" | Junior should NOT need to figure anything out |
| "Tests are specified, don't need review" | Test quality matters more than quantity |

---

## Verification Checklist

**Per worker brief reviewed:**
- [ ] Applied all 8 categories
- [ ] Presented the complete revised brief with missing information
- [ ] Reread the revised brief from the root transcript (no placeholders remain)
- [ ] Success criteria are measurable
- [ ] Edge cases addressed
- [ ] Test specifications are meaningful

**Overall plan:**
- [ ] Reviewed every worker brief (no exceptions)
- [ ] Presented structured results
- [ ] Provided clear recommendation

**Can't check all boxes?** Return to the review process.

---

## Examples

See [REFERENCE.md](REFERENCE.md) for detailed examples including:
- Skipping edge case analysis vs. full analysis (VIN scanner example)
- Accepting vague criteria vs. rewriting as measurable (encryption example)
- Good vs. bad test specifications

---

### 6. Chain to Execution

After refinement is complete, route to execution.

Invoke executing-plans directly — it enters the epic worktree automatically:

```
Invoke skill="$gambit:executing-plans"
```

Announce it in one line first ("Worker briefs refined and ready — starting execution.") so the transition is visible.

---

## Integration

**Called by:**
- `gambit:brainstorming` (optional, user chooses at handoff)
- User via `$gambit:task-refinement`

**Calls:**
- `gambit:executing-plans` (invoked directly after refinement — enters the epic worktree automatically)

**Workflow:**
```
gambit:brainstorming → gambit:task-refinement → gambit:executing-plans
                                ↓
                         (if gaps: revise full worker briefs, re-review)
```
