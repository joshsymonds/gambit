# Verification Examples and Patterns

Detailed examples for the verification skill. See [SKILL.md](SKILL.md) for the process.

## Bad: Claiming Success Without Verification

```
Developer modifies authentication logic.

Developer thinks: "This fix is straightforward, tests should pass now"

Developer writes: "Great! All tests passing. The bug is fixed."

[No test command run, no output shown]
```

**Why it fails:**
- "Should pass" ≠ evidence
- Confidence ≠ verification
- Might have broken other tests
- Might not have fixed the bug

## Good: Verification Before Claim

```
Developer modifies authentication logic.

Runs: go test ./...
Output: 33 passed, 1 failed
Failure: TestLoginWithExpiredToken

Developer writes:
"Tests: 33 passed, 1 failed.
Failure: TestLoginWithExpiredToken still fails.
The fix didn't handle expired tokens.
Investigating..."
```

**Why it works:**
- Ran actual command
- Read actual output
- Reported actual status
- No false claims

## Bad: Closing Task Without Criterion Verification

```
Task success criteria:
- [ ] All functions fully implemented (no stubs, no TODOs)
- [ ] Tests written and passing
- [ ] Pre-commit hooks pass

Developer implements functions.

Developer thinks: "I implemented everything, task complete"

TaskUpdate
  taskId: "task-id"
  status: "completed"

[No verification commands run]
```

**Why it fails:**
- Might have TODO comments left
- Specific tests not run
- Pre-commit hooks not checked
- "Implemented" ≠ "verified"

## Good: Verifying Each Criterion

```
TaskGet taskId: "task-id"

Success criteria:
- [ ] All functions fully implemented (no stubs, no TODOs)
- [ ] Tests written and passing
- [ ] Pre-commit hooks pass

Verification:

1. Check for TODOs:
   $ rg "TODO|FIXME" src/
   [no output]
   Status: VERIFIED

2. Run tests:
   $ go test ./...
   ok ... 12/12 tests passed
   Status: VERIFIED

3. Run pre-commit:
   $ pre-commit run --all-files
   [all checks passed]
   Status: VERIFIED

All criteria verified.

TaskUpdate
  taskId: "task-id"
  status: "completed"
```

## Bad: Trusting Agent Reports

```
Developer dispatches agent to run tests.

Agent reports: "All tests pass. 47/47 passed."

Developer writes: "Tests pass, we're good!"

[No independent verification of what agent actually did]
```

**Why it fails:**
- Agent might have run wrong command
- Agent might have misread output
- No VCS diff to confirm changes were made
- "Agent said so" ≠ evidence

## Good: Independent Verification After Agent

```
Developer dispatches agent to run tests.

Agent reports: "All tests pass. 47/47 passed."

Developer verifies:
- Checks git diff: confirms expected code changes present
- Runs: npm test
- Output: 47/47 passed, exit 0
- Confirms agent's report matches independent verification

Developer writes:
"Tests pass. [Verified independently: npm test, 47/47 passed, exit 0]"
```

## Bad: Stale Verification

```
Developer runs tests: 42/42 passed.

Developer then fixes an edge case (changes 3 lines).

Developer writes: "All tests pass (42/42 passed earlier)."

[Tests not re-run after the change]
```

**Why it fails:**
- Code changed since verification
- Edge case fix might break existing tests
- "Earlier" results are stale
- 3 lines can break anything

## Good: Fresh Verification After Every Change

```
Developer runs tests: 42/42 passed.

Developer then fixes an edge case (changes 3 lines).

Developer runs tests again: 42/42 passed.

Developer writes:
"Tests pass after edge case fix.
[Ran: npm test, Output: 42/42 passed, exit 0]"
```

## Verification Claim Format

### Tests

```
GOOD: [Run test command] [See: 34/34 pass] "All tests pass"
BAD:  "Should pass now" / "Looks correct"
```

### Regression Tests (TDD Red-Green)

```
GOOD: Write → Run (fail) → Fix → Run (pass) → Verify regression caught
BAD:  "I've written a regression test" (without red-green verification)
```

### Build

```
GOOD: [Run build] [See: exit 0] "Build passes"
BAD:  "Linter passed" (linter doesn't check compilation)
```

### Task Completion

```
GOOD: Re-read task → Verify each criterion → Report gaps or completion
BAD:  "Tests pass, task complete" (tests are only one criterion)
```

### Agent Delegation

```
GOOD: Agent reports → Check VCS diff → Run independently → Report actual state
BAD:  Trust agent report at face value
```
