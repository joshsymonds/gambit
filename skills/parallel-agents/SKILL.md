---
name: parallel-agents
description: Use when facing 3+ independent test failures, bugs in unrelated subsystems, or investigation questions where each problem is isolable and does not share root cause, files, or shared state with the others. User phrases like "these failures look unrelated", "fan this out", "investigate in parallel".
---

# Parallel Agent Dispatch

## Overview

When facing 3+ independent failures, dispatch one agent per problem domain concurrently. Verify independence first, dispatch all in single message, wait for all agents, check conflicts, verify integration.

**Core principle:** Independence verification BEFORE dispatch. Single message dispatch for true parallelism.

**Iron Law:** NO dispatch without verifying independence first. ALL agents dispatched in a SINGLE message or they run sequentially. No exceptions.

**Announce at start:** "I'm using gambit:parallel-agents to investigate these independent failures concurrently."

## Rigidity Level

MEDIUM FREEDOM — Follow the 6-step process strictly. Independence verification mandatory. Parallel dispatch in single message required. Adapt agent prompt content to problem domain.

## Quick Reference

| Step | Action | STOP If |
|------|--------|---------|
| 1 | Identify domains | < 3 independent domains |
| 2 | Create agent prompts | Prompts incomplete |
| 3 | Dispatch in SINGLE message | - |
| 4 | Wait for all agents | Agent stuck > 5 min |
| 5 | Review results | Conflicts found |
| 6 | Verify integration | Tests fail |

**Why 3+?** With only 2 failures, coordination overhead often exceeds sequential time.

**Critical:** Dispatch all agents in a single message with multiple Task() calls, or they run sequentially.

## When to Use

**Use when:**
- 3+ test files failing with different root causes
- Multiple subsystems broken independently
- Each problem can be understood without context from others
- No shared state between investigations
- You've verified failures are truly independent
- Each domain has clear boundaries (different files, modules, features)

**Don't use when:**
- Failures are related (fix one might fix others)
- Need to understand full system state first
- Agents would interfere (editing same files)
- Haven't verified independence yet (exploratory phase)
- Failures share root cause (one bug, multiple symptoms)
- Need to preserve investigation order (cascading failures)
- Only 2 failures (overhead exceeds benefit)

## The Process

### Step 1: Identify Independent Domains

**Test for independence with 3 questions:**

1. **"If I fix failure A, does it affect failure B?"**
   - NO → Independent
   - YES → Related, investigate together

2. **"Do failures touch same code/files?"**
   - NO → Likely independent
   - YES → Check if different functions/areas

3. **"Do failures share error patterns?"**
   - NO → Independent
   - YES → Might be same root cause

**If < 3 independent domains: STOP.** Investigate sequentially instead.

**Create coordination Task:**

```
TaskCreate
  subject: "Parallel Investigation: [N] independent failures"
  description: |
    ## Independent Domains
    1. [Domain 1]: [files/tests]
    2. [Domain 2]: [files/tests]
    3. [Domain 3]: [files/tests]

    ## Independence Verification
    - Domain 1 vs 2: [why independent]
    - Domain 2 vs 3: [why independent]
    - Domain 1 vs 3: [why independent]

    ## Agent Status
    - [ ] Agent 1 ([Domain 1]): dispatched / returned / result
    - [ ] Agent 2 ([Domain 2]): dispatched / returned / result
    - [ ] Agent 3 ([Domain 3]): dispatched / returned / result

    ## Progress
    - [ ] All agents dispatched (single message)
    - [ ] All agents returned
    - [ ] No conflicts found
    - [ ] Integration verified (full test suite)
  activeForm: "Coordinating parallel investigation"
```

Then: `TaskUpdate taskId: "[id]" status: "in_progress"`

---

### Step 2: Create Focused Agent Prompts

Each agent prompt must have:

1. **Specific scope** — one test file or subsystem
2. **Clear goal** — make these tests pass
3. **Constraints** — don't change code outside scope
4. **Expected output** — summary of findings and fixes

**Good prompt structure:**

```markdown
Fix the 3 failing tests in src/agents/tool_abort_test.go:

1. "TestAbortWithPartialOutput" - expects 'interrupted at' in message
2. "TestMixedCompletedAndAborted" - fast tool aborted instead of completed
3. "TestPendingToolCount" - expects 3 results but gets 0

These are timing/race condition issues. Your task:

1. Read the test file and understand what each test verifies
2. Identify root cause - timing issues or actual bugs?
3. Fix by:
   - Replacing arbitrary timeouts with event-based waiting
   - Fixing bugs in abort implementation if found
   - Adjusting test expectations if testing changed behavior

Constraints:
- Do NOT just increase timeouts - find the real issue
- Do NOT modify files outside src/agents/
- Do NOT change behavior, only fix tests or bugs

Return: Summary of root cause and what you fixed.
```

**Bad prompts:** Too broad ("Fix all the tests"), no context ("Fix the race condition"), no constraints (agent might refactor everything).

---

### Step 3: Dispatch All Agents in SINGLE Message

**CRITICAL:** All agents in ONE message with multiple Task() calls.

```
// CORRECT - Single message, parallel execution
Task
  subagent_type: "general-purpose"
  description: "Fix tool_abort_test.go failures"
  prompt: "[prompt 1]"

Task
  subagent_type: "general-purpose"
  description: "Fix batch_completion_test.go failures"
  prompt: "[prompt 2]"

Task
  subagent_type: "general-purpose"
  description: "Fix tool_approval_test.go failures"
  prompt: "[prompt 3]"
```

```
// WRONG - Sequential messages
Task prompt1
[Wait for response]
Task prompt2  // Sequential, not parallel!
```

---

### Step 4: Wait for All Agents

- Don't start integration until ALL agents complete
- Check progress with `TaskOutput task_id: "[id]" block: false`
- If agent stuck > 5 minutes: check TaskOutput, retry with clearer prompt
- If agent needs context from another domain: wait for that agent, then restart with context

---

### Step 5: Review Results and Check Conflicts

**When all agents return:**

1. **Read each summary** — root cause, changes made, uncertainties
2. **Check for conflicts:**
   - Did multiple agents edit same files?
   - Did agents make contradictory assumptions?
   - Are there integration points between domains?
3. **Integration strategy:**
   - No conflicts → apply all changes
   - Conflicts → resolve manually before applying
   - Contradictory assumptions → verify with user

---

### Step 6: Verify Integration

Run full test suite (not just the fixed tests):

```
Task
  subagent_type: "general-purpose"
  description: "Run full test suite"
  prompt: "Run: [test command]. Report pass/fail counts and any failures."
```

**Decision tree:**
- All pass → mark coordination Task complete
- Failures → identify which agent's change caused regression

**Update coordination Task:**

```
TaskUpdate
  taskId: "[coordination-task-id]"
  description: |
    ## Results
    - Agent 1: Fixed [X] in [files]
    - Agent 2: Fixed [Y] in [files]
    - Agent 3: Fixed [Z] in [files]

    ## Conflicts
    [None / Description and resolution]

    ## Integration
    All tests pass. Changes integrated successfully.
  status: "completed"
```

---

## Critical Rules

### Rules That Have No Exceptions

1. **Verify independence first** — 3 questions before dispatching
2. **3+ domains required** — 2 failures: do sequentially
3. **Single message dispatch** — all agents in one message with multiple Task() calls
4. **Wait for ALL agents** — don't integrate until all complete
5. **Check conflicts manually** — read summaries, verify no contradictions
6. **Verify integration** — run full suite yourself, don't trust agents

### Common Excuses

All mean: **STOP. Follow the process.**

| Excuse | Reality |
|--------|---------|
| "Just 2 failures, can still parallelize" | Overhead exceeds benefit, do sequentially |
| "Probably independent, will dispatch and see" | Verify independence FIRST |
| "Can dispatch sequentially to save syntax" | Must dispatch in single message |
| "Agent failed, but others succeeded" | All agents must succeed or re-investigate |
| "Conflicts are minor, can ignore" | Resolve all conflicts explicitly |
| "Can skip verification, agents ran tests" | Agents can make mistakes, YOU verify |

---

## Examples

See [REFERENCE.md](REFERENCE.md) for detailed good/bad examples including:
- Independence verification (correct rejection vs false assumption)
- Sequential vs parallel dispatch
- Conflict detection and resolution
- Integration verification

---

## Verification Checklist

Before completing parallel agent work:

- [ ] Verified independence with 3 questions (fix A affects B? same code? same error?)
- [ ] 3+ independent domains identified
- [ ] Created focused agent prompts (scope, goal, constraints, output)
- [ ] Dispatched all agents in single message
- [ ] Waited for ALL agents to complete
- [ ] Read all agent summaries
- [ ] Checked for conflicts (same files, contradictory assumptions)
- [ ] Resolved any conflicts manually
- [ ] Ran full test suite
- [ ] Documented which agents fixed what
- [ ] Coordination Task marked complete

**Can't check all boxes?** Return to process.

---

## Integration

**This skill calls:**
- `gambit:debugging` (how to investigate individual failures)
- `gambit:verification` (verify integration)
- general-purpose agents (`subagent_type: "general-purpose"`) for parallel investigation and test running

**Called by:**
- When multiple independent test failures detected
- When multiple subsystems broken independently

**Workflow:**
```
Multiple failures detected
    ↓
Step 1: Verify independence (3+ domains)
    ↓
Step 2: Create agent prompts
    ↓
Step 3: Dispatch in SINGLE message
    ↓
Step 4: Wait for all agents
    ↓
Step 5: Review results, check conflicts
    ↓
Step 6: Verify integration
    ↓
All failures resolved
```
