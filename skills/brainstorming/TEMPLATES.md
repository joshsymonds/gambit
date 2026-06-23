# Epic and Task Templates

Full templates for creating epics and first tasks. SKILL.md has condensed versions — use these for complete output.

## Epic Template

```
TaskCreate
  subject: "Epic: [Feature Name]"
  description: |
    ## Requirements (IMMUTABLE)
    [What MUST be true when complete — specific, testable]
    - Requirement 1: [concrete requirement]
    - Requirement 2: [concrete requirement]
    - Requirement 3: [concrete requirement]

    ## Success Criteria (MUST ALL BE TRUE)
    - [ ] Criterion 1 (objective, testable — e.g., 'Integration tests pass')
    - [ ] Criterion 2 (objective, testable — e.g., 'Works with existing User model')
    - [ ] All tests passing
    - [ ] Pre-commit hooks passing

    ## Anti-Patterns (FORBIDDEN)
    - NO [Pattern 1] (reason: [why forbidden])
    - NO [Pattern 2] (reason: [why forbidden])
    - NO [Pattern 3] (reason: [why forbidden])

    ## Quality Bar
    [The user-authored standard for what "good code" means on THIS epic — the subjective bar a
     reviewer (and the orchestrator at each checkpoint) judges each diff against, on top of the
     mechanical floor the worker contract already enforces (no suppression, no weakened tests, no
     dead code). State it as standards a capable model can APPLY to a diff, not metrics and not
     vague adjectives. Author it from the user's words, not your own.]
    - [standard 1, e.g. "parsimonious — no abstraction the requirements don't demand"]
    - [standard 2, e.g. "reads like the surrounding code: same naming, idioms, structure"]
    - [standard 3, e.g. "comments only where the WHY isn't obvious from the code"]
    [Default if the user offers no specifics — record this and tell them you did: "Code a senior
     engineer would approve without changes: clear, minimal, correct, idiomatic to the surrounding
     code, and commented only where the intent isn't self-evident."]

    ## Approach
    [2-3 paragraph summary of chosen approach]

    ## Architecture
    [Key components, data flow, integration points]

    ## Approaches Considered

    ### 1. [Chosen Approach] — CHOSEN
    **What:** [2-3 sentence description]
    **Investigation:** [What was researched]
    **Pros:** [benefits]
    **Cons:** [drawbacks]
    **Chosen because:** [specific reasoning]

    ### 2. [Rejected Approach] — REJECTED
    **What:** [2-3 sentence description]
    **Why explored:** [What made it seem viable]
    **Investigation:** [What was researched]
    **Pros:** [benefits]
    **Cons:** [fatal flaw]
    **REJECTED BECAUSE:** [specific reason]
    **DO NOT REVISIT UNLESS:** [condition that would change decision]

    ## Scope Boundaries
    **In scope:**
    - [explicit inclusions]

    **Out of scope:**
    - [explicit exclusions with reasoning]

    ## Open Questions
    - [uncertainties to resolve during implementation]
    - [decisions deferred to execution phase]
  activeForm: "Planning [feature name]"
```

### Anti-Pattern Examples

```
- NO localStorage tokens (reason: httpOnly prevents XSS token theft)
- NO new user model (reason: must integrate with existing db/models/user.ts)
- NO mocking OAuth in integration tests (reason: defeats purpose of testing real flow)
- NO Socket.IO (reason: user confirmed mobile clients use raw WebSocket)
- NO separate WebSocket port (reason: deployment complexity, firewall rules)
```

### Quality Bar Examples

Good — standards a reviewer can apply to a diff:

```
- Parsimonious: no helper, layer, or option the task's requirements don't demand
- Reads like the file it lives in: matches existing naming, structure, and idioms
- Names say what the thing is; no comments restating the code, comments only for non-obvious WHY
- Public surface is minimal: nothing exported or generalized the requirements don't need
```

Bad — vague adjectives a reviewer can't act on (rewrite or use the default):

```
- High-quality, clean code
- Good performance
- Well-structured and maintainable
```

## First Task Template

```
TaskCreate
  subject: "Add [specific deliverable]"
  description: |
    ## Goal
    [What this task delivers — one clear outcome]

    ## Implementation

    1. Study existing code
       [Point to 2-3 similar implementations: file.ts:line]

    2. Write tests first (TDD)
       [Specific test cases for this task]

    3. Implementation checklist
       - [ ] file.ts:line - function_name() - [what it does]
       - [ ] test.ts:line - test_name() - [what it tests]

    ## Success Criteria
    - [ ] [Specific, measurable outcome]
    - [ ] Tests passing
    - [ ] Pre-commit hooks passing
  activeForm: "Adding [deliverable]"
```
