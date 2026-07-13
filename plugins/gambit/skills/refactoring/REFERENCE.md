# Refactoring Examples and Patterns

Detailed examples for the refactoring skill. See [SKILL.md](SKILL.md) for the process.

## Bad: Big-Bang Refactoring

```
# Changes made all at once:
- Renamed 15 functions across 5 files
- Extracted 3 new classes
- Moved code between 10 files
- Reorganized module structure

# Then runs tests
$ pytest
... 23 test failures ...

# Now what? Which change broke what?
# Can't identify. Must revert everything.
# 3 hours of work lost.
```

**Why it fails:**
- Can't identify which change broke tests
- Reverting means losing ALL work
- Fixing requires debugging entire refactoring

## Good: Incremental Refactoring

```
# Step 1
Extract validate_email() → test → commit ✓

# Step 2
Extract validate_name() → test → commit ✓

# Step 3 (test fails!)
Move validation to new file → test → FAIL
Undo: git checkout -- .
Try smaller: Just move one function → test → pass → commit ✓

# Step 4
Move second function → test → commit ✓

# Result: 4 commits, each reviewable, each safe
# If step 3 had broken something, knew exactly which change
```

## Bad: Changing Behavior While "Refactoring"

```python
# Original
def validate_email(email):
    if not email:
        raise ValueError("email required")
    if "@" not in email:
        raise ValueError("invalid email")

# "Refactored" - but added behavior!
def validate_email(email):
    if not email:
        raise ValueError("email required")
    if "@" not in email:
        raise ValueError("invalid email")
    # NEW: Added validation - this is NOT refactoring
    if "." not in email:
        raise ValueError("invalid email domain")
```

**Why it fails:**
- Changes behavior (now rejects emails like "user@localhost")
- Tests might pass if they don't cover this case
- Not refactoring — this is modifying functionality
- Do separately: refactor first, then add feature

## Bad: Refactoring Without Tests

```python
# Legacy code with no tests
def process_payment(amount, user_id):
    # 200 lines of complex payment logic
    # Multiple edge cases
    # No tests exist

# Developer refactors without tests:
# - Extracts 5 methods
# - Renames variables
# - Simplifies conditionals
# - "Looks good to me!"

# Deploys to production
# Payments fail for amounts over $1000
# Edge case handling was accidentally changed
```

**Why it fails:**
- No tests to verify behavior preserved
- Complex logic has hidden edge cases
- Subtle behavior changes go unnoticed
- Breaks in production, not development

## Good: Write Tests First, Then Refactor

```python
# BEFORE refactoring: Write tests documenting current behavior

def test_process_payment_valid_amount(): ...
def test_process_payment_zero_amount(): ...
def test_process_payment_large_amount(): ...   # The $1000+ case!
def test_process_payment_negative_amount(): ...
def test_process_payment_invalid_user(): ...

# Run tests → all pass (documenting current behavior)

# NOW refactor with tests as safety net:
# Extract method → test → commit
# Rename → test → commit
# Simplify → test → commit

# Tests catch any behavior changes immediately
```

## Bad: "While I'm Here" Scope Creep

```
Task: Extract validation methods from UserService

What actually happened:
1. Extract validate_email() ✓
2. Extract validate_name() ✓
3. "While I'm here, let me add type hints" ← scope creep
4. "These docstrings need updating" ← not part of refactoring
5. "This import ordering is wrong" ← separate concern
6. "I should also extract the database calls" ← different refactoring

# 6 unrelated changes in one session
# Tests fail at step 5 — was it the type hints? docstrings? imports?
```

**The fix:** Each of those is a separate commit (or separate task). Finish the extraction first, then do cosmetic changes in their own commits.

## Strangler Fig Pattern

**When to use:**
- Need to replace system but can't tolerate downtime
- Want incremental migration with monitoring
- System too large to refactor in one go

**How it works:**

```
Legacy: Monolithic UserService (5000 LOC)
Goal: Extract into separate module

Step 1 (Transform):
- Create new UserValidator module
- Implement validation logic
- Tests pass in isolation

Step 2 (Coexist):
- Add routing layer (facade)
- Route validation calls to new module
- Route other calls to legacy
- Monitor both

Step 3 (Eliminate):
- Once confident, migrate more functionality
- Remove from legacy
- Repeat until legacy empty
```

**Benefits:**
- Incremental replacement reduces risk
- Legacy continues operating during transition
- Can pause/rollback at any point
- Each step independently valuable

## Common Refactoring Patterns

| Pattern | Description | When to Use |
|---------|-------------|-------------|
| **Extract Method** | Pull code into new function | Duplicated logic, long functions |
| **Extract Class** | Pull related methods into new type | God class, mixed responsibilities |
| **Inline** | Replace function call with body | Over-abstracted, single-use helper |
| **Rename** | Make names clearer | Confusing or misleading names |
| **Move** | Relocate code to better location | Feature envy, misplaced logic |
| **Replace Conditional with Polymorphism** | Use interfaces | Complex switch/if chains |
| **Introduce Parameter Object** | Group related params | Functions with 4+ parameters |
| **Extract Interface** | Define contract separately | Need to swap implementations |
