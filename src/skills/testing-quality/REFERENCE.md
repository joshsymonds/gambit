# Testing Quality Reference

Code examples, corner case tables, output templates, and task templates for the testing-quality skill.

## RED Pattern Examples

### Tautological Tests (pass by definition)

```go
// RED: Verifies non-optional return is not nil
func TestBuilderReturnsValue(t *testing.T) {
    result := NewBuilder().Build()
    assert.NotNil(t, result) // Always passes - return type guarantees this
}

// RED: Verifies enum has cases (compiler checks this)
func TestStatusEnumHasValues(t *testing.T) {
    assert.Greater(t, len(StatusValues), 0)
}

// RED: Duplicates implementation
func TestAddReturnsSum(t *testing.T) {
    assert.Equal(t, 2+3, Add(2, 3)) // Tautology: testing 2+3 == 2+3
}
```

### Mock-Testing Tests (test the mock, not production)

```go
// RED: Only verifies mock was called, not actual behavior
func TestServiceFetchesData(t *testing.T) {
    mockAPI := &MockAPI{}
    mockAPI.On("Fetch").Return([]Data{}, nil)
    service := NewService(mockAPI)
    service.GetData()
    mockAPI.AssertCalled(t, "Fetch") // Tests mock, not service logic
}

// RED: Mock determines test outcome
func TestProcessorHandlesData(t *testing.T) {
    mockParser := &MockParser{}
    mockParser.On("Parse").Return(&Result{Valid: true}, nil)
    result := processor.Process(mockParser)
    assert.True(t, result.Valid) // Just returns what mock returns
}
```

### Line Hitters (execute without asserting)

```go
// RED: Calls function, doesn't verify outcome
func TestProcessorRuns(t *testing.T) {
    processor := NewProcessor()
    processor.Run() // No assertion - just verifies no crash
}

// RED: Assertion is trivial
func TestConfigLoads(t *testing.T) {
    config := LoadConfig()
    assert.NotNil(t, config) // Too weak - doesn't verify correct values
}
```

### Evergreen/Liar Tests (always pass)

```go
// RED: Catches and ignores exceptions
func TestParserHandlesInput(t *testing.T) {
    defer func() {
        recover() // Swallowed - test passes even on panic
    }()
    parser.Parse(input)
    assert.True(t, true) // Always passes
}

// RED: Test setup bypasses code under test
func TestValidatorValidates(t *testing.T) {
    validator := NewValidator(WithSkipValidation(true)) // Oops
    assert.True(t, validator.Validate(badInput))
}
```

## YELLOW Pattern Examples

### Happy Path Only

```go
// YELLOW: Only tests valid input
func TestParseValidJSON(t *testing.T) {
    result, err := Parse(`{"port": 8080, "host": "localhost"}`)
    assert.NoError(t, err)
    assert.Equal(t, 8080, result.Port)
    assert.Equal(t, "localhost", result.Host)
}
// Missing: empty string, malformed JSON, deeply nested, unicode, huge payload
```

### Weak Assertions

```go
// YELLOW: Assertion too weak
func TestFetchReturnsData(t *testing.T) {
    result, _ := Fetch("/api/users")
    assert.NotNil(t, result)          // Should verify actual content
    assert.Greater(t, len(result), 0) // Should verify exact count or specific items
}
```

### Partial Coverage

```go
// YELLOW: Tests success, not failure
func TestCreateUserSucceeds(t *testing.T) {
    user, err := CreateUser("test", "test@example.com")
    assert.NoError(t, err)
    assert.NotEmpty(t, user.ID)
}
// Missing: duplicate email, invalid email, missing fields, database error
```

## GREEN Pattern Examples

```go
// GREEN: Verifies specific behavior with exact values FROM PRODUCTION
func TestCalculateTotal_AppliesDiscountCorrectly(t *testing.T) {
    cart := NewCart([]Item{{Price: 100, Quantity: 2}}) // Real Cart
    cart.ApplyDiscount("SAVE20")                       // Real discount logic
    assert.Equal(t, 160, cart.Total())                 // 200 - 20% = 160
}
// GREEN because: Exercises Cart.ApplyDiscount production code
// Would catch: Discount calculation bugs, rounding errors
// Assertion: Verifies exact computed value from production

// GREEN: Tests boundary conditions IN PRODUCTION CODE
func TestUsername_RejectsEmptyString(t *testing.T) {
    _, err := NewUser(WithUsername(""))
    assert.ErrorIs(t, err, ErrInvalidUsername)
}
// GREEN because: Exercises User constructor validation (production)
// Would catch: Missing empty string validation
// Assertion: Exact error type from production code
```

## RED/YELLOW Justification Example

```markdown
### TestAuthWorks - RED (Tautological)

**Test code (auth_test.go:45-52):**
- Line 46: `auth := NewAuthService()` - Creates auth instance
- Line 47: `result := auth.Login("user", "pass")` - Calls login
- Line 48: `assert.NotNil(result)` - Asserts result exists

**Production code (auth.go:78-95):**
- Login() returns *AuthResult (never nil by Go semantics)

**Why RED:**
- Line 48 asserts `!= nil` but Go guarantees non-nil return
- If login returned {Success: false, Error: "invalid"}, test still passes
- Bug example: Wrong password accepted → returns {Success: true} → test passes
```

## Corner Case Tables

### Input Validation Corner Cases

| Category | Examples | Test Name Pattern |
|----------|----------|-------------------|
| Empty values | `""`, `[]`, `{}`, `nil` | test_empty_X_rejected/handled |
| Boundary values | 0, -1, MAX_INT, MAX_LEN | test_boundary_X_handled |
| Unicode | RTL, emoji, combining chars, null byte | test_unicode_X_preserved |
| Injection | SQL: `'; DROP`, XSS: `<script>`, cmd: `; rm` | test_injection_X_escaped |
| Malformed | truncated JSON, invalid UTF-8, wrong type | test_malformed_X_error |

### State Corner Cases

| Category | Examples | Test Name Pattern |
|----------|----------|-------------------|
| Uninitialized | Use before init, double init | test_uninitialized_X_error |
| Already closed | Use after close, double close | test_closed_X_error |
| Concurrent | Parallel writes, read during write | test_concurrent_X_safe |
| Re-entrant | Callback calls same method | test_reentrant_X_safe |

### Integration Corner Cases

| Category | Examples | Test Name Pattern |
|----------|----------|-------------------|
| Network | timeout, connection refused, DNS fail | test_network_X_timeout |
| Partial response | truncated, corrupted, slow | test_partial_response_handled |
| Rate limiting | 429, quota exceeded | test_rate_limit_handled |
| Service errors | 500, 503, malformed response | test_service_error_handled |

## Output Report Template

```markdown
# Test Effectiveness Analysis: [Project Name]

## Executive Summary

| Metric | Count | % |
|--------|-------|---|
| Total tests analyzed | N | 100% |
| RED (remove/replace) | N | X% |
| YELLOW (strengthen) | N | X% |
| GREEN (keep) | N | X% |
| Missing corner cases | N | - |

**Overall Assessment:** [CRITICAL / NEEDS WORK / ACCEPTABLE / GOOD]

## Detailed Findings

### RED Tests (Must Remove/Replace)

| Test | File:Line | Problem | Action |
|------|-----------|---------|--------|
| TestUserExists | auth_test.go:45 | Tautological (non-optional != nil) | Delete |
| TestServiceFetches | api_test.go:23 | Tests mock, not production | Replace |

### YELLOW Tests (Must Strengthen)

| Test | File:Line | Current | Recommended |
|------|-----------|---------|-------------|
| TestParse | parser_test.go:34 | Happy path only | Add edge cases |
| TestFetch | api_test.go:56 | Weak assertion (> 0) | Verify exact values |

### GREEN Tests (Exemplars)

[List 3-5 tests that exemplify good testing practices with justification]

## Missing Corner Cases by Module

### Module: [name]/ - Priority: [P0-P3]

| Corner Case | Bug Risk | Recommended Test |
|-------------|----------|------------------|
| Empty password | Auth bypass | test_empty_password_rejected |
| Unicode username | Encoding corruption | test_unicode_username_preserved |

## Tasks Created

| Task ID | Subject | Priority |
|---------|---------|----------|
| [id] | Remove tautological tests from auth | P0 |
| [id] | Strengthen weak assertions in api | P1 |
| [id] | Add corner case tests for auth | P0 |
```

## Task Templates

### Epic Template

```
TaskCreate
  subject: "Epic: Test Quality Improvement"
  description: |
    ## Goal
    Improve test effectiveness by removing tautological tests, strengthening weak tests,
    and adding missing corner case coverage.

    ## Requirements (IMMUTABLE)
    - All RED tests removed or replaced with meaningful tests
    - All YELLOW tests strengthened with proper assertions
    - All P0 missing corner cases covered

    ## Success Criteria
    - [ ] No tautological tests remain
    - [ ] All tests verify production behavior, not mock behavior
    - [ ] P0 modules have edge case coverage
    - [ ] Tests document what bug they catch

    ## Anti-patterns (FORBIDDEN)
    - Adding tests that only check `!= nil`
    - Adding tests that verify mock behavior
    - Adding happy-path-only tests
    - Leaving tautological tests "for coverage"
  activeForm: "Planning test quality improvement"
```

### Subtask Templates

**Remove RED tests:**

```
TaskCreate
  subject: "Remove tautological tests from [module]"
  description: |
    ## Tests to Remove
    - [file:line] - [TestName] (tautological: [reason])

    ## Success Criteria
    - [ ] All listed tests deleted
    - [ ] No new tautological tests introduced
    - [ ] Test suite still passes
    - [ ] Coverage may decrease (this is expected and good)
  activeForm: "Removing tautological tests"
```

**Add corner case tests:**

```
TaskCreate
  subject: "Add corner case tests for [module]"
  description: |
    ## Tests to Add
    - test_empty_X_rejected - prevents [bug]
    - test_unicode_X_preserved - prevents [bug]

    ## Implementation (TDD)
    For each test:
    1. Write failing test first (RED)
    2. Verify test fails for the right reason
    3. Test catches the specific bug listed

    ## Success Criteria
    - [ ] All corner case tests written and passing
    - [ ] Each test documents the bug it catches
    - [ ] No tautological tests added
  activeForm: "Adding corner case tests"
```

## Mutation Testing (Optional)

If mutation testing tools are available in the codebase, use them to validate test effectiveness.

Mutation testing reveals tests that execute code without meaningful assertions by:
1. Introducing small bugs (mutations) in production code
2. Running tests
3. If tests still pass, the test didn't detect the bug

**Tools by language:**

| Language | Tool | Command |
|----------|------|---------|
| Go | go-mutesting | `go-mutesting ./...` |
| Python | mutmut | `mutmut run` |
| TypeScript | Stryker | `stryker run` |

**Interpreting results:**

| Result | Meaning | Action |
|--------|---------|--------|
| Killed | Test detected the bug | Test is meaningful |
| Survived | Test missed the bug | Test needs strengthening (YELLOW) |
| No coverage | Mutation in untested code | Missing test (add to corner cases) |

Add surviving mutations to the gap analysis.
