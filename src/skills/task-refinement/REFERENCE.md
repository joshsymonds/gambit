# Task Refinement Examples and Patterns

Detailed examples for the task-refinement skill. See [SKILL.md](SKILL.md) for the process.

## Bad: Skip Edge Case Analysis

```
Task: "Implement VIN scanner"

Review:
1. Granularity: OK
2. Implementability: OK
3. Success Criteria: OK
4. Dependencies: OK
5. Safety Standards: OK
6. Edge Cases: [SKIPPED - "looks straightforward"]
7. Red Flags: OK
8. Tests: OK

Conclusion: "Task looks good, approve"

# Production issues:
# - VIN scanner matches random 17-char strings (no checksum validation)
# - Lowercase VINs not handled
# - Catastrophic regex backtracking (DoS vulnerability)
```

**Why it fails:**
- Skipped edge case analysis for a "straightforward" task
- Missed ISO 3779 checksum validation requirement
- Missed case normalization
- Missed regex performance/security concern

## Good: Full Edge Case Analysis

```
Task: "Implement VIN scanner"

Category 6 (Edge Cases):
- Malformed input? VIN has checksum - must validate per ISO 3779
- Empty/nil? What if empty string passed?
- Unicode/special? VIN is alphanumeric only, but what about lowercase?
- Large inputs? Regex patterns can cause catastrophic backtracking

Findings:
- VIN checksum validation not mentioned
- Case normalization not mentioned
- Regex backtracking risk not mentioned

Update Task with Key Considerations:

## Key Considerations (ADDED BY REVIEW)

**VIN Checksum**
- ISO 3779 requires transliteration and weighted sum
- MUST validate checksum, not just pattern match

**Case Normalization**
- VINs can appear lowercase in user input
- MUST normalize to uppercase before validation

**Regex Backtracking Risk**
- Test with pathological inputs (10000 'X's)
- Use bounded repetition, avoid nested quantifiers
```

---

## Bad: Accept Vague Success Criteria

```
Task: "Implement data encryption"

## Success Criteria
- [ ] Encryption is implemented correctly
- [ ] Code is good quality
- [ ] Tests work properly

Review: "Has 3 success criteria. OK."

# Junior engineer:
# "How do I know if encryption is 'correct'?"
# "What makes code 'good quality'?"
# Uses ECB mode (insecure), no IV generation
# Complete rewrite required
```

**Why it fails:**
- "Implemented correctly" is not verifiable
- "Good quality" is subjective
- Junior chose insecure defaults because criteria didn't specify

## Good: Rewrite as Measurable Criteria

```
## Success Criteria (STRENGTHENED BY REVIEW)

**Encryption Implementation**:
- [ ] Uses AES-256-GCM (verified in code review)
- [ ] Unique IV generated per encryption via crypto_random
- [ ] Authentication tag verified on decryption
- [ ] Key derivation uses PBKDF2 or Argon2

**Code Quality** (automated):
- [ ] `npm run lint` exits 0 with no warnings
- [ ] No panic/unwrap in production code (grep confirms)
- [ ] No TODOs without task references

**Tests** (specific bugs each catches):
- [ ] test_encrypt_decrypt_roundtrip — catches serialization bugs
- [ ] test_wrong_key_fails_auth — catches missing auth tag check
- [ ] test_empty_plaintext — catches empty input crash
- [ ] test_large_plaintext_10mb — catches memory/streaming bugs
- [ ] test_unicode_plaintext — catches encoding corruption
```

---

## Bad: Tests That Don't Catch Bugs

```
## Test Specifications
- test_user_model_exists — verify User struct has correct fields
- test_basic_functionality — verify basic usage works
- test_encode_decode — verify encode then decode returns original

# Problems:
# - "model exists" is tautological — compiler catches this
# - "basic functionality" is vague — what bug does it prevent?
# - "encode_decode" only tests happy path — misses edge cases
```

## Good: Tests That Catch Specific Bugs

```
## Test Specifications (STRENGTHENED BY REVIEW)
- test_empty_payload_returns_validation_error — catches missing input validation
- test_concurrent_writes_dont_corrupt_data — catches race condition in shared state
- test_malformed_json_returns_400_not_500 — catches unhandled parse error
- test_unicode_name_preserved_after_roundtrip — catches encoding/decoding bugs
- test_expired_token_returns_401_not_500 — catches missing expiry check
```

Each test name describes the bug it catches. If you can't describe the bug, the test is tautological.

---

## Bad: Placeholder Text Left in Task

```
TaskUpdate
  taskId: "task-3"
  description: |
    ## Goal
    Implement rate limiting for API endpoints.

    ## Steps
    1. Set up middleware
    2. [Details as specified in the design document]
    3. Add tests

    ## Success Criteria
    - [ ] Rate limiting works as designed
    - [ ] [Additional criteria from requirements]

Review: "Task updated. Moving on."
```

**Why it fails:**
- Step 2 is a placeholder — "[Details as specified in the design document]"
- Success criterion 2 is a placeholder — "[Additional criteria from requirements]"
- No read-back verification after update
- Junior engineer sees placeholders and has to guess

## Good: Replace Placeholders, Verify After Update

```
TaskUpdate
  taskId: "task-3"
  description: |
    ## Goal
    Implement token bucket rate limiting for API endpoints.

    ## Steps
    1. Create src/middleware/ratelimit.ts with token bucket algorithm
    2. Configure: 100 requests/minute per IP, 1-minute sliding window
    3. Add X-RateLimit-Remaining and Retry-After response headers
    4. Write tests for limit exceeded, header values, IP extraction

    ## Success Criteria
    - [ ] 429 returned after 100th request in 1-minute window
    - [ ] X-RateLimit-Remaining header decrements correctly
    - [ ] Retry-After header shows seconds until bucket refill
    - [ ] X-Forwarded-For used when behind proxy

# VERIFY: Read back the task
TaskGet taskId: "task-3"

# Confirm: No placeholders, all steps specific, all criteria measurable
```

---

## Edge Case Categories by Domain

### Web API Tasks
- Empty request body
- Missing required fields
- Invalid JSON (malformed, truncated)
- Extremely large payloads
- Unicode in string fields
- SQL injection in string fields
- Concurrent requests to same resource
- Auth token expired/malformed/missing
- Rate limiting under burst traffic

### Database Tasks
- Empty tables (first record)
- NULL columns in queries
- Duplicate key violations
- Transaction rollback behavior
- Connection pool exhaustion
- Large result sets (pagination)
- Concurrent writes to same row

### File Processing Tasks
- Empty file
- Binary file when text expected
- Very large file (memory limits)
- File with no newline at end
- File with mixed line endings (CRLF/LF)
- Path traversal in filenames
- Unicode filenames
- Permission denied

### CLI/Script Tasks
- No arguments provided
- Invalid flag combinations
- Stdin is a pipe vs. terminal
- Very long arguments (ARG_MAX)
- Special characters in arguments
- Exit code handling
