# Debugging Examples and Patterns

Detailed examples for the debugging skill. See [SKILL.md](SKILL.md) for the process.

## Bad: Symptom Fix Without Investigation

```
Developer sees: NullPointerException at UserService:45

"Obviously email is null. Add null check."

String email = user.getEmail() != null ? user.getEmail().toLowerCase() : "";

Bug "fixed"... but crashes continue with different data.
```

**Why it fails:**
- Fixed symptom (null at line 45), not root cause
- Didn't investigate WHY email is null
- Root cause: Registration endpoint doesn't validate email
- Null-check applied everywhere, root cause unfixed

## Good: Systematic Investigation

```
Developer sees: NullPointerException at UserService:45

Step 1: Reproduce
  $ curl -X POST /api/register -d '{"name":"test"}'
  # Consistently returns 500

Step 2: Investigate
  WebSearch: "NullPointerException getEmail java"
  Scout (agent_type: "explorer" + Read codex-contracts/scout.md, scout tier):
    "Find where User objects are created without email validation — cite file:line"

  Trace backward:
    UserService:45 ← email null
    Controller:23 ← User from RegistrationHandler
    RegistrationHandler:15 ← User created without email validation

  ROOT CAUSE: Registration doesn't validate email field

Step 3: Write failing test (proof of understanding)
  @Test void registrationRequiresEmail() {
      assertThrows(ValidationException.class, () ->
          register(new UserDTO(null, "password")));
  }
  // RUN: FAILS (bug exists) ✓

Step 4: Hand off to brainstorming
  Invoke skill="$gambit:brainstorming"
  Seed it with:
    Root cause: Registration endpoint missing email validation (RegistrationHandler:15)
    Failing test (immutable success criterion): registrationRequiresEmail must pass
    Anti-pattern (forbidden): null-check at the UserService:45 crash site — that's a symptom patch
    Consider defense-in-depth: validate at the DTO boundary AND in RegistrationHandler

  Brainstorming designs the fix epic → executing-plans implements it → review.
```

(For a genuine one-liner fully guarded by the failing test, the fast path applies: make
the change, confirm the test passes and the suite is green, done — no epic needed.)

## Bad: Test Written After Fix

```
Developer fixes validation bug, then writes test:

def validate_email(email):
    return "@" in email and len(email) > 0  # Fix

def test_validate_email():
    assert validate_email("user@example.com") == True  # Test after

# Test passes immediately - but only tests happy path
# Later, someone breaks validation:
def validate_email(email):
    return True  # Oops!

# Test STILL PASSES (only checked happy path)
```

**Why it fails:**
- Test written after fix — never saw it fail
- Only tests happy path remembered
- Doesn't test the actual bug (empty email)
- Regression goes undetected

## Good: Test Written Before Fix (RED-GREEN)

```
Phase 4: Write failing test FIRST
def test_empty_email_rejected():
    assert validate_email("") == False  # The bug case

def test_no_at_symbol_rejected():
    assert validate_email("invalid") == False

# RUN: FAILS (bug exists) ✓

Phase 5: Implement fix
def validate_email(email):
    if not email or "@" not in email:
        return False
    return True

# RUN: PASSES ✓

# Later regression attempt:
def validate_email(email):
    return True  # Oops!

# TEST CATCHES IT:
# FAIL: assert validate_email("") == False
```

## Investigation Patterns

### Single-Component Bug

Use Read and Grep to trace through the code directly:

```
1. Read the error location
2. Grep for callers of the failing function
3. Read each caller, trace the data
4. Identify where bad value enters
```

### Multi-Component Bug

Dispatch an explorer agent to map the system:

```
SpawnAgent
  agent_type: "explorer"  # Profile-aware: requires hide_spawn_agent_metadata = false and a non-reserved tool_namespace.          # the read-only scout class
  task_name: "map_data_flow_for_feature"
  fork_turns: "none"
  message: |
    Read <abs>/codex-contracts/scout.md first (your binding scout contract), then trace the request flow for [operation]:
    1. Where does the request enter? (handler/controller)
    2. What services process it?
    3. What database queries run?
    4. Where could data be lost or corrupted?
    Report with file:line evidence; say NOT FOUND for anything absent.
```

Add diagnostic logging at boundaries, run once, analyze:

```python
# Handler
logger.debug(f"=== Handler received: {request.json}")

# Service
logger.debug(f"=== Service processing: {order}")

# Repository
logger.debug(f"=== Query result: {result}")
```

### Intermittent Bug

1. Add instrumentation, don't try to fix
2. Run multiple times, collect data
3. Look for patterns (timing, concurrency, input variation)
4. If timing-related: check for race conditions or arbitrary timeouts

### Performance Bug

1. Profile before optimizing — measure, don't guess
2. Identify the bottleneck with actual numbers
3. Fix the bottleneck, re-measure
4. If no clear bottleneck: check for N+1 queries, missing indices, unnecessary work
