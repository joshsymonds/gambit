<!-- gambit-backend:claude -->
# Epic and Task Templates

Full templates for creating epics and first tasks. SKILL.md has condensed versions — use these for complete output.
<!-- /gambit-backend -->
<!-- gambit-backend:codex -->
# Epic Contract and Worker Brief Templates

Full templates for drafting the epic contract and first-wave worker briefs before user review, then presenting the approved records in the root transcript. SKILL.md has condensed versions. Only concise wave summaries belong in the native plan.
<!-- /gambit-backend -->

## Epic Template

```
<!-- gambit-backend:claude -->
TaskCreate
  subject: "Epic: [Feature Name]"
  description: |
<!-- /gambit-backend -->
<!-- gambit-backend:codex -->
Draft for user review as "Epic: [Feature Name]":
<!-- /gambit-backend -->
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
    The highest professional standard — code a master engineer would be proud to ship: elegant,
    complete, and built on a superb foundation. This bar is FIXED for every epic; write it
    verbatim — never elicit it, weaken it, or make it a per-project preference. It governs how
    well the required work is built — craftsmanship, not scope: it never licenses doing less than
    the Requirements demand, only doing it well. Project-specific prohibitions belong in
    Anti-Patterns, not here. It sits on top of the mechanical floor the worker contract already
    enforces (no suppression, no weakened tests, no dead code). The orchestrator at each
    checkpoint and the reviewers judge every diff against these standards:
    - Elegant: the simplest design that fully solves the problem — no abstraction, layer, or
      option the requirements don't demand, and none they do demand left out.
    - Idiomatic: reads like the code around it — same naming, structure, and conventions.
    - Complete: handles the real edge and error cases, not just the happy path; no stubs, TODOs,
      or "good enough for now" left behind.
    - Minimal surface: nothing exported or generalized beyond what the requirements need.
    - Self-documenting: names say what things are; comments only where the WHY isn't obvious.

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
<!-- gambit-backend:claude -->
  activeForm: "Planning [feature name]"
<!-- /gambit-backend -->
```

### Anti-Pattern Examples

```
- NO localStorage tokens (reason: httpOnly prevents XSS token theft)
- NO new user model (reason: must integrate with existing db/models/user.ts)
- NO mocking OAuth in integration tests (reason: defeats purpose of testing real flow)
- NO Socket.IO (reason: user confirmed mobile clients use raw WebSocket)
- NO separate WebSocket port (reason: deployment complexity, firewall rules)
```

<!-- gambit-backend:claude -->
## First Task Template
<!-- /gambit-backend -->
<!-- gambit-backend:codex -->
## First-Wave Worker Brief Template
<!-- /gambit-backend -->

```
<!-- gambit-backend:claude -->
TaskCreate
  subject: "Add [specific deliverable]"
  description: |
<!-- /gambit-backend -->
<!-- gambit-backend:codex -->
Draft for user review as "Worker Brief: Add [specific deliverable]":
<!-- /gambit-backend -->
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
<!-- gambit-backend:claude -->
  activeForm: "Adding [deliverable]"
<!-- /gambit-backend -->
```
<!-- gambit-backend:codex -->

For a fresh epic, obtain explicit user approval of the complete draft contract and every complete first-wave worker brief. Only after approval, present the full approved contract and every complete first-wave brief in the root transcript, then initialize the complete ordered wave list. A parallel first wave is one step regardless of its worker count:

```
SessionPlanWrite
  plan:
    - step: "Wave 1: Add [concise deliverable summary]"
      status: pending
```
<!-- /gambit-backend -->
