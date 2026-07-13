# Parallel Agents Examples and Patterns

Detailed examples for the parallel-agents skill. See [SKILL.md](SKILL.md) for the process.

## Bad: Assume Independence Without Checking

```
# 3 test failures:
# - API endpoint tests failing
# - Database query tests failing
# - Cache invalidation tests failing

Thinks: "Different subsystems, must be independent"
Dispatches 3 agents immediately without checking

# All three failures caused by same root cause: schema change
# Agents make conflicting fixes based on different assumptions
# Integration fails
```

**Why it fails:**
- Assumed independence from naming alone
- Didn't ask the 3 questions
- One root cause (schema change) manifesting in 3 places
- Wasted parallel effort, then had to redo everything

## Good: Verify Independence First

```
# 3 test failures observed

Question 1: "If I fix API, does it affect database?"
- API uses database queries
- If database schema changes, API breaks
- YES - related

Question 2: "Do they touch same code/files?"
- All reference user_accounts table
- YES - shared data model

Question 3: "Same error pattern?"
- All mention "column not found"
- YES - shared root cause

Result: NOT INDEPENDENT
These are one problem (schema change) manifesting in 3 places.
Solution: Single agent investigates all three together.
```

## Good: Correct Independence Identification

```
Failure 1: Tool abort tests failing (timing issues in tool_abort_test.go)
Failure 2: Batch completion tests failing (state management in batch_test.go)
Failure 3: Tool approval tests failing (race conditions in approval_test.go)

Question 1: "Fix one affects others?"
- Abort tests: timeout handling in abort.go
- Batch tests: ordering logic in batch.go
- Approval tests: mutex in approval.go
- NO - different modules, different logic

Question 2: "Touch same code/files?"
- Different test files, different implementation files
- NO - isolated modules

Question 3: "Same error pattern?"
- Abort: "expected 'interrupted at' in message"
- Batch: "expected 5 results, got 3"
- Approval: "mutex not held"
- NO - different symptoms, different root causes

Result: 3 INDEPENDENT domains ✓ → Proceed to dispatch
```

## Bad: Dispatch Sequentially

```
# Developer sees 3 independent failures

Task prompt1
[Wait for response from agent 1]

Task prompt2
[Wait for response from agent 2]

Task prompt3
[Wait for response from agent 3]

# Total time: Sum of all three (sequential)
# No parallelization benefit
```

**Why it fails:**
- Each agent waited for the previous one
- Total time = agent1 + agent2 + agent3
- Should be max(agent1, agent2, agent3)

## Good: Dispatch in Single Message

```
# All in ONE message — each a worker (Read codex-contracts/worker.md first, worker tier per codex-contracts/models.md):

Task
  agent_type: "default"
  agent_profile: "<worker tier>"
  description: "Fix tool_abort_test.go"
  prompt: "[prompt 1]"

Task
  agent_type: "default"
  agent_profile: "<worker tier>"
  description: "Fix batch_test.go"
  prompt: "[prompt 2]"

Task
  agent_type: "default"
  agent_profile: "<worker tier>"
  description: "Fix approval_test.go"
  prompt: "[prompt 3]"

# All three run concurrently
# Total time: max(agent1, agent2, agent3)
```

## Bad: Integrate Without Checking Conflicts

```
# 3 agents complete

Agent 1: "Fixed timeout issue by increasing wait time to 5000ms"
- File: src/executor.go, DEFAULT_TIMEOUT = 5000

Agent 2: "Added mutex lock around critical section"
- File: src/executor.go, added sync.Mutex

Agent 3: "Fixed timing issue by reducing wait time to 1000ms"
- File: src/executor.go, DEFAULT_TIMEOUT = 1000

Developer: "All succeeded, ship it"
[Applies all changes without reading]

# Agent 1 and 3 changed same constant with different values
# Final code has inconsistent state
# Tests still fail
```

**Why it fails:**
- Didn't read agent summaries carefully
- Agents 1 and 3 edited same file, same constant
- Contradictory changes applied blindly
- Integration was never verified

## Good: Check for Conflicts Before Integration

```
# Review each agent's changes

Agent 1: timeout = 5000ms in executor.go
Agent 2: added mutex in executor.go
Agent 3: timeout = 1000ms in executor.go

CONFLICT DETECTED:
- Agent 1 and 3 both edited DEFAULT_TIMEOUT
- Contradictory values (5000 vs 1000)

Investigation:
- Agent 1's tests were slow due to unrelated issue
- Agent 3 found correct timeout value
- Fix Agent 1's slow tests separately

Resolution:
- Apply Agent 2's mutex ✓
- Apply Agent 3's 1000ms timeout ✓
- Don't apply Agent 1's 5000ms (investigate slow tests separately)
```

## Bad: Only 2 Failures, Force Parallelism

```
# 2 test failures:
# - Auth tests failing
# - Config tests failing

Developer: "Let me dispatch 2 agents in parallel"

# Creates coordination task, writes prompts, dispatches...
# Total overhead: 10 minutes of setup
# Each agent takes 5 minutes
# Parallel time: 10 min setup + 5 min agents = 15 min
# Sequential time: 5 min + 5 min = 10 min

# Parallel was SLOWER due to coordination overhead
```

**Why it fails:**
- 2 failures don't justify parallel dispatch
- Coordination overhead (Task creation, prompt writing, conflict checking)
  exceeds time saved
- Sequential investigation would have been faster

## Recovery: False Independence Discovered

```
# Dispatched 3 agents believing domains were independent

Agent 1 returns: "Fixed auth token validation in auth.go"
Agent 2 returns: "Had to modify auth.go to fix session handling"
Agent 3 returns: "Cache tests pass after updating auth token format"

PROBLEM: All three touched auth.go or auth-related code
Domains were NOT truly independent.

Recovery:
1. Don't apply any changes yet
2. Merge domains: auth + session + cache are one domain
3. Dispatch single agent with combined context
4. Learn: "auth token format" was the shared dependency
   the independence check missed
```

## Prompt Quality Comparison

### Bad: Too Broad

```
Fix all the failing tests in the project.
```

No scope, no context, no constraints. Agent might change anything.

### Bad: No Context

```
Fix the race condition in tool_approval_test.go.
```

Which race condition? What's the expected behavior? What are the constraints?

### Good: Specific, Contextual, Constrained

```
Fix 2 failing tests in src/agents/tool_approval_test.go:

1. "TestApprovalRaceCondition" (line 78) - mutex not held during check
2. "TestConcurrentApprovals" (line 112) - approvals processed out of order

Context: The approval system uses a sync.Mutex to protect shared state.
These tests verify thread safety under concurrent access.

Steps:
1. Read tool_approval.go to understand the locking pattern
2. Identify where the mutex should be held but isn't
3. Fix the locking to cover the full critical section

Constraints:
- Do NOT change the approval API
- Do NOT modify files outside src/agents/
- Keep the existing mutex pattern, just fix its scope

Return: Root cause and what you changed.
```
