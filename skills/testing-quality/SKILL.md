---
name: testing-quality
description: Use when bugs keep slipping through despite high test coverage, when suspecting tests are giving false confidence, before a major refactor that will depend on the existing test suite, or when coverage metrics don't match incident rates. User phrases like "do these tests actually catch bugs?", "is this suite any good?", "why didn't the tests catch this?".
user_invokable: true
---

# Testing Quality Analysis

## Overview

Audit test suites for real effectiveness, not vanity metrics. Identify tests that provide false confidence and missing corner cases. Create Tasks for improvements.

**Core principle:** Tests must catch bugs, not inflate coverage metrics. Coverage measures execution, not assertion quality.

**Announce at start:** "I'm using gambit:testing-quality to audit these tests with SRE-level scrutiny."

## Rigidity Level

MEDIUM FREEDOM — Follow analysis phases exactly. RED/YELLOW/GREEN criteria are rigid. Corner case discovery adapts to the codebase.

## Quick Reference

| Phase | Action | Output |
|-------|--------|--------|
| 1 | Inventory all test files | Test catalog |
| 2 | Read production code | Context for analysis |
| 3 | Categorize (skeptical default) | RED/YELLOW/GREEN per test |
| 4 | Self-review all classifications | Validated categories |
| 5 | Discover missing corner cases | Gap analysis |
| 6 | Prioritize by business impact | Priority matrix |
| 7 | Create Tasks for improvements | Tracked improvement plan |

**Iron Law:** Read production code BEFORE categorizing ANY test.

**CRITICAL MINDSET: Assume tests were written by junior engineers optimizing for coverage metrics.** A test is RED or YELLOW until proven GREEN.

## When to Use

- Production bugs appear despite high test coverage
- Suspecting coverage gaming or tautological tests
- Before major refactoring (ensure tests catch regressions)
- Onboarding to unfamiliar codebase (assess test quality)
- Planning test improvement initiatives

**Don't use when:**
- Writing new tests → use `gambit:test-driven-development`
- Just need to run tests → use test-runner agent

## The Process

### Phase 1: Test Inventory

Create complete catalog of tests to analyze. Use Glob and Grep to find all test files and count tests per module. Adapt file patterns to the language.

### Phase 2: Read Production Code

**MANDATORY before categorizing ANY test.**

For each test file:
1. Read the production code the test claims to exercise
2. Understand what the production code actually does
3. Trace the test's call path to verify it reaches production code

**Why:** Without reading production code, you WILL miscategorize tests as GREEN when they're YELLOW or RED. Junior engineers commonly create test utilities and test THOSE instead of production code, or set up mocks that determine test outcomes.

### Phase 3: Categorize Each Test (Skeptical Default)

**Assume every test is RED or YELLOW until you have concrete evidence it's GREEN.**

For EACH test, answer these four questions:

1. **What bug would this catch?** (Can't name one → RED)
2. **Does it exercise PRODUCTION code or a mock/test utility?** (Mock determines outcome → RED)
3. **Could production break while test passes?** (Yes → YELLOW or RED)
4. **Meaningful assertion on PRODUCTION output?** (`!= nil`, testing fixtures → weak)

#### RED — Must Remove or Replace

Tests that pass by definition or test mocks instead of production code:

- **Tautological:** Asserts something guaranteed by the type system or compiler
- **Mock-testing:** Mock determines the test outcome — test verifies what the mock returns, not what production does
- **Line hitters:** Execute code without meaningful assertions (just "no crash")
- **Evergreen/Liar:** Always pass regardless of production behavior (swallowed exceptions, bypassed logic)

See [REFERENCE.md](REFERENCE.md) for detailed code examples of each RED pattern.

#### YELLOW — Must Strengthen

Tests with real value but significant gaps:

- **Happy path only:** Tests valid input, misses edge cases
- **Weak assertions:** `!= nil` or `> 0` when exact values are available
- **Partial coverage:** Tests success but not failure paths

See [REFERENCE.md](REFERENCE.md) for detailed code examples of each YELLOW pattern.

#### GREEN — Exceptional Quality Required

**GREEN is the EXCEPTION, not the rule.** A test is GREEN only if ALL four conditions are true:

1. Exercises actual PRODUCTION code (not mocks, not test utilities)
2. Has precise assertions (exact values, not `!= nil`)
3. Would fail if production breaks (name the specific bug)
4. Tests behavior, not implementation (survives valid refactoring)

**Before marking ANY test GREEN, you MUST state:**
- "This test exercises [specific production code path]"
- "It would catch [specific bug] because [reason]"
- "The assertion verifies [exact production behavior], not a test fixture"

**If you cannot fill in those blanks, the test is YELLOW at best.**

### Phase 4: Self-Review

**Before finalizing ANY categorization, verify:**

For each GREEN test:
- [ ] Did I read the PRODUCTION code this test exercises?
- [ ] Does the test call PRODUCTION code or a test utility/mock?
- [ ] Can I name the SPECIFIC BUG this test would catch?
- [ ] If production broke, would this test DEFINITELY fail?
- [ ] Am I being too generous because the test "looks reasonable"?

For each YELLOW test:
- [ ] Should this actually be RED? Is there ANY bug-catching value?
- [ ] Is the weakness fundamental (tests a mock) or fixable (weak assertion)?

**If you have ANY doubt about a GREEN, downgrade to YELLOW.**

### Phase 5: Line-by-Line Justification

**MANDATORY for every RED or YELLOW classification.**

This forces verification that your classification is correct by explaining exactly WHY the test is problematic.

**Required format:**

```markdown
### [Test Name] - RED/YELLOW

**Test code (file:lines):**
- Line X: `code` - [what this line does]
- Line Y: `assertion` - [what this asserts]

**Production code it claims to test (file:lines):**
- [Brief description of what production code does]

**Why RED/YELLOW:**
- [Specific reason with line references]
- [What bug could slip through despite this test passing]
```

**If you cannot write this justification, you haven't done the analysis properly.**

### Phase 6: Corner Case Discovery

For each module, identify missing corner case tests across these categories:

- **Input validation:** Empty values, boundary values, unicode, injection, malformed data
- **State:** Uninitialized, already closed, concurrent access, re-entrant calls
- **Integration:** Timeouts, partial responses, rate limiting, service errors

See [REFERENCE.md](REFERENCE.md) for the complete corner case tables with specific examples and recommended test names.

### Phase 7: Prioritize by Business Impact

| Priority | Criteria | Action Timeline |
|----------|----------|-----------------|
| P0 - Critical | Auth, payments, data integrity | This sprint |
| P1 - High | Core business logic, user-facing | Next sprint |
| P2 - Medium | Internal tools, admin features | Backlog |
| P3 - Low | Utilities, non-critical paths | As time permits |

### Phase 8: Create Tasks for Improvements

Create epic Task for test quality improvement, then subtasks for each action group (remove RED tests, strengthen YELLOW tests, add missing corner cases).

Each subtask must be:
- **Scoped:** 2-5 minutes of work
- **Explicit:** File paths and line numbers specified
- **Testable:** At least 3 success criteria

Set dependencies so removal happens before additions.

See [REFERENCE.md](REFERENCE.md) for epic and subtask templates.

## Output Format

Present results as a structured report. See [REFERENCE.md](REFERENCE.md) for the complete output template.

**Executive summary table:**

| Metric | Count | % |
|--------|-------|---|
| Total tests analyzed | N | 100% |
| RED (remove/replace) | N | X% |
| YELLOW (strengthen) | N | X% |
| GREEN (keep) | N | X% |
| Missing corner cases | N | - |

**Overall Assessment:** CRITICAL / NEEDS WORK / ACCEPTABLE / GOOD

## Critical Rules

1. **Read production code FIRST** — before categorizing ANY test
2. **Skeptical default** — RED/YELLOW until proven GREEN
3. **Justify every GREEN** — name the production path, the bug, and the assertion
4. **Justify every RED/YELLOW** — line-by-line with file references
5. **Self-review before finalizing** — challenge every GREEN classification
6. **Create actionable Tasks** — don't just report, create tracked improvement plan

### Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Test looks reasonable" | Looking reasonable ≠ catching bugs. Read production code. |
| "High coverage = good tests" | Coverage measures execution, not assertion quality |
| "Mock is necessary here" | Mock is fine, but assert on production behavior, not mock returns |
| "Test exercises the function" | Calling a function without meaningful assertions is a line hitter |
| "It would catch obvious bugs" | Name the specific bug. If you can't, it's YELLOW at best. |
| "Too many tests to justify each" | Unjustified classifications are wrong classifications |

## Anti-patterns

**Don't:**
- Mark tests GREEN because they "look reasonable" (verify call paths)
- Trust test names and comments (code doesn't lie, comments do)
- Give benefit of the doubt (skeptical default, always)
- Rush categorization (read production code FIRST)
- Mark YELLOW when it's actually RED (mock determines outcome → RED)
- Skip corner case analysis ("existing tests are enough")

**Do:**
- Read production code before categorizing ANY test
- Trace call paths to verify production code is exercised
- Apply skeptical default (RED/YELLOW until proven GREEN)
- Complete self-review checklist for all GREEN classifications
- Create actionable Tasks for improvements

## Verification Checklist

**Analysis Quality (MANDATORY):**
- [ ] Read production code for EVERY test before categorizing
- [ ] Traced call paths to verify tests exercise production, not mocks/utilities
- [ ] Applied skeptical default (assumed RED/YELLOW, required proof for GREEN)
- [ ] Completed self-review checklist for ALL GREEN tests
- [ ] Each GREEN test has explicit justification (production path + bug + assertion)
- [ ] Each RED/YELLOW has line-by-line justification

**Per module:**
- [ ] All tests categorized (RED/YELLOW/GREEN)
- [ ] RED tests have specific removal/replacement actions
- [ ] YELLOW tests have specific strengthening actions
- [ ] Corner cases identified (input, state, integration)
- [ ] Priority assigned (P0/P1/P2/P3)

**Task Integration:**
- [ ] Created epic for test quality improvement
- [ ] Created subtasks for each category (remove, strengthen, add)
- [ ] Set task dependencies

## Integration

**Called by:**
- User via `/gambit:testing-quality`
- Before major refactoring efforts
- When coverage is high but bugs slip through

**Creates:**
- Tasks for removing RED tests
- Tasks for strengthening YELLOW tests
- Tasks for adding missing corner cases

**Workflow:**
```
gambit:testing-quality → Analyze → Create improvement Tasks
gambit:executing-plans → Implement improvements with TDD
gambit:verification → Verify improvements complete
```
