# Epic Contract and Worker Brief Templates

Full templates for drafting the epic contract and first-wave worker briefs before user review, then presenting the approved records in the root transcript. SKILL.md has condensed versions. Only concise wave summaries belong in the native plan.

## Epic Template

```
Draft for user review as "Epic: [Feature Name]":
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

    ## Delivery Constraints
    - Convergence circuit breaker: STOP autonomous continuation when two consecutive checkpoints
      retire no success criterion or named blocker, or when remaining work grows at both
      checkpoints. Report the evidence and require explicit user approval before changing scope,
      architecture, or the delivery budget.
    - Repair ceiling: one implementation attempt plus at most two repair attempts for the same
      defect. If the second repair fails, or the same defect recurs at a later checkpoint, STOP and
      revisit the architecture or worker brief with the user.
    - Scope growth: every newly discovered worker must map to an immutable requirement, an open
      review-ledger finding, or a failing declared validation gate. Anything else is proposed scope,
      not automatically authorized work.

    ## Validation Strategy
    - Focused worker command: [fast exact command each worker runs for its owned behavior]
    - Wave/component gate: [exact command run once on the integrated wave]
    - Release acceptance: [exact expensive end-to-end/system command, including freshness setup]
    - Acceptance budget: [normally one fresh run after implementation and architecture/scope
      preflight; name any additional allowed diagnostic run and what question it answers]

    ## Open Questions
    - [uncertainties to resolve during implementation]
    - [decisions deferred to execution phase]
```

### Anti-Pattern Examples

```
- NO localStorage tokens (reason: httpOnly prevents XSS token theft)
- NO new user model (reason: must integrate with existing db/models/user.ts)
- NO mocking OAuth in integration tests (reason: defeats purpose of testing real flow)
- NO Socket.IO (reason: user confirmed mobile clients use raw WebSocket)
- NO separate WebSocket port (reason: deployment complexity, firewall rules)
```

## First-Wave Worker Brief Template

```
Draft for user review as "Worker Brief: Add [specific deliverable]":
    ## Goal
    [What this task delivers — one clear outcome]

    ## Files owned
    [Exact repository-relative path allowlist. List every tracked or untracked text or binary
    artifact, deletion, symlink, and executable-mode change this worker may deliver. No globs or
    directories.]
    - exact/path/to/source.ext
    - exact/path/to/test.ext

    ## Hidden shared surfaces
    [Name implicit collision surfaces checked while forming the wave: lockfiles/manifests,
    generated code or indexes, migration sequences, registries/barrels, route tables, snapshot
    directories. Write `None` only after checking. Any surface this task will edit must also appear
    in Files owned; overlapping ownership moves the task to another wave.]

    ## Neighbors
    [For a parallel wave, give every concurrent worker's subject and exact Files owned allowlist;
    all are off-limits. For a single-task wave, write `None (single-task wave)`.]
    - [neighbor subject] — exact allowlist: [path/a, path/b] (off-limits)

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

    Test command: [exact focused worker command for this task]
```

For a fresh epic, obtain explicit user approval of the complete draft contract and every complete first-wave worker brief. Only after approval, present the full approved contract and every complete first-wave brief in the root transcript, then initialize the complete ordered wave list. A parallel first wave is one step regardless of its worker count:

```
SessionPlanWrite
  plan:
    - step: "Wave 1: Add [concise deliverable summary]"
      status: pending
```
