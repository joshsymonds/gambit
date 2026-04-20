---
name: task-refinement
description: Use when a task plan has just been created and needs review before execution, when brainstorming or writing-plans just handed off, when unsure whether a junior could execute without questions, or when you see placeholder text, vague success criteria, or missing edge cases. User phrases like "review these tasks", "are these ready?", "before we start", "catch any gaps". Do NOT use when implementation is already in progress or for creating plans from scratch.
user_invokable: true
---

# Task Refinement

## Overview

Review Tasks systematically. Find gaps, fix them, verify fixes. A task is ready when a junior engineer can execute it without asking questions.

**Core principle:** Don't just identify problems — fix them. Update each Task, then read it back to verify.

**Iron Law:** NO task passes review with vague criteria, missing file paths, or placeholder text. Every task must be executable by a junior engineer without questions. No exceptions.

**Announce at start:** "I'm using gambit:task-refinement to review and strengthen these tasks."

## Rigidity Level

LOW FREEDOM — Apply all 8 categories to every task. No skipping. Update tasks with fixes, then verify no placeholders remain. Reject plans with critical gaps.

## Quick Reference

| Category | Key Check | Auto-Reject If |
|----------|-----------|----------------|
| 1. Granularity | Tasks 2-5 min? | Any task without breakdown estimate |
| 2. Implementability | Junior executes without questions? | Vague language, missing file paths |
| 3. Success Criteria | Measurable, verifiable? | "Works correctly", "is implemented" |
| 4. Dependencies | Correct blocking order? | Circular or missing dependencies |
| 5. Anti-patterns | Forbidden patterns specified? | No anti-patterns section |
| 6. Edge Cases | Empty/unicode/concurrent/failure? | No edge case consideration |
| 7. Red Flags | Placeholder text? TODOs? | "[detailed above]", "[as specified]" |
| 8. Test Quality | Tests catch real bugs? | Tautological or happy-path-only tests |

## When to Use

- Before `gambit:executing-plans` starts implementation
- After `gambit:brainstorming` or `gambit:writing-plans` creates tasks
- When reviewing any plan for quality before execution

**Don't use for:**
- Task already being implemented (too late)
- Creating plans from scratch → `gambit:brainstorming` or `gambit:writing-plans`
- Debugging → `gambit:debugging`

## The Process

### 1. Load All Tasks

```
TaskList
```

Identify the epic and all subtasks. Read each with `TaskGet`.

### 2. Review Each Task (All 8 Categories)

For each task, apply every category. No skipping — "straightforward" tasks hide the worst edge cases.

#### Category 1: Granularity

- Each task completable in 2-5 minutes?
- Large tasks broken into subtasks with clear deliverables?
- Each subtask independently completable?

**If too large:** Create subtasks with `TaskCreate`, link with `addBlockedBy`.

#### Category 2: Implementability

- Can a junior engineer execute without asking questions?
- All file paths specified (or marked "TBD: new file")?
- Function signatures/behaviors described, not just "implement X"?
- "Done" clearly defined?

**Red flags:** "Implement properly", "Add support", "Make it work", missing file paths.

#### Category 3: Success Criteria

- Each task has 3+ specific, measurable criteria?
- All criteria verifiable with a command or code review?
- No subjective criteria?

**Rewrite vague criteria into measurable ones:**
- "Authentication works" → "POST /auth/login with valid creds returns 200 + JWT; invalid creds returns 401"
- "Code is good quality" → "Lint clean, no TODOs, no panic/unwrap in production code"
- "Tests pass" → "Run `npm test`, 0 failures, exit 0"

#### Category 4: Dependencies

- `blockedBy` relationships correct?
- No circular dependencies?
- Dependency graph logically ordered?

Verify with `TaskList` output.

#### Category 5: Anti-patterns

- Task specifies what NOT to do?
- Includes: no TODOs without issue refs, no stub implementations, no swallowed errors?
- Error handling requirements specified?

#### Category 6: Edge Cases

**Ask for each task:**
- What happens with empty/nil/zero input?
- What happens with malformed input?
- What about Unicode, special characters, large inputs?
- What about concurrent access?
- What when dependencies fail?

**Add findings to task's Key Considerations section.** See [REFERENCE.md](REFERENCE.md) for edge case examples.

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

### 3. Update Each Task

After reviewing, update each task with fixes:

```
TaskUpdate
  taskId: "[task-id]"
  description: |
    [Original content, preserved and strengthened]

    ## Key Considerations (ADDED BY REVIEW)

    **Edge Case: [Name]**
    - [What could go wrong]
    - MUST [specific mitigation]

    ## Anti-patterns
    [Original anti-patterns]
    - NEW: [Specific anti-pattern for this task's risks]
```

**Rules for updates:**
- Preserve original intent
- Strengthen vague criteria into measurable ones
- Replace ALL placeholder text with actual content
- Add edge case analysis

---

### 4. Verify Updates (MANDATORY)

**After every TaskUpdate, read back with TaskGet and verify:**

```
TaskGet
  taskId: "[task-id]"
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

### Task-by-Task

#### [Task Name] ([task-id])
**Status**: [Ready / Needs Revision / Rejected]
**Issues Found**: [count]
**Improvements Made**:
- [What was fixed]
**Edge Cases Added**:
- [What failure modes now addressed]

[Repeat for each task]

### Summary
- Tasks updated: [list]
- Critical issues found: [count]
- Recommendation: [approve/revise/reject with reasoning]
```

---

## Critical Rules

### Rules That Have No Exceptions

1. **Apply all 8 categories to every task** — no skipping any category
2. **Reject plans with placeholder text** — "[detailed above]" = instant reject
3. **Verify after every update** — read back with TaskGet, check for placeholders
4. **Strengthen vague criteria** — "works correctly" must become measurable commands
5. **Add edge cases to every task** — empty, unicode, concurrency, failure modes
6. **Reject tautological tests** — tests must catch specific bugs

### Common Excuses

All mean: **STOP. Apply the full checklist.**

| Excuse | Reality |
|--------|---------|
| "Task looks straightforward" | Edge cases hide in "straightforward" tasks |
| "Has 3 criteria, meets minimum" | Criteria must be MEASURABLE, not just 3+ items |
| "Placeholder is just formatting" | Placeholder = incomplete specification |
| "Can handle edge cases during implementation" | Must specify upfront to prevent rework |
| "Junior will figure it out" | Junior should NOT need to figure anything out |
| "Tests are specified, don't need review" | Test quality matters more than quantity |

---

## Verification Checklist

**Per task reviewed:**
- [ ] Applied all 8 categories
- [ ] Updated task with missing information
- [ ] Verified update (no placeholders remain)
- [ ] Success criteria are measurable
- [ ] Edge cases addressed
- [ ] Test specifications are meaningful

**Overall plan:**
- [ ] Reviewed ALL tasks (no exceptions)
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

**If invoked from brainstorming or writing-plans handoff:** They already asked about worktrees. Invoke executing-plans directly:

```
Skill skill="gambit:executing-plans"
```

**If invoked standalone by user:** Ask what's next:

```
AskUserQuestion
  questions:
    - question: "Tasks refined and ready. How should we proceed?"
      header: "Next step"
      options:
        - label: "Start executing (Recommended)"
          description: "Begin implementing with gambit:executing-plans"
        - label: "Set up worktree first"
          description: "Create isolated workspace with gambit:using-worktrees"
      multiSelect: false
```

Then invoke the chosen skill directly using the Skill tool.

---

## Integration

**Called by:**
- `gambit:brainstorming` (optional, user chooses at handoff)
- `gambit:writing-plans` (optional, user chooses at handoff)
- User via `/gambit:task-refinement`

**Calls:**
- `gambit:executing-plans` (invoked directly after refinement)
- `gambit:using-worktrees` (optional, if user wants isolation)

**Workflow:**
```
gambit:brainstorming ─┐
                      ├→ gambit:task-refinement → gambit:executing-plans
gambit:writing-plans ─┘         ↓
                         (if gaps: revise tasks, re-review)
```
