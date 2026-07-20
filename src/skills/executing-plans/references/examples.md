# Executing Plans Examples

## Handling Obstacles Correctly

When blocked, check the epic before switching approaches:

```
1. Hit obstacle: OAuth library doesn't support PKCE
2. Re-read epic → "Approaches Considered" shows:
   "Implicit flow - REJECTED BECAUSE: security risk"
3. PKCE is different from implicit flow → safe to explore
4. Ask user before switching: "Library X doesn't support PKCE.
   Should I try library Y, or use a different approach?"
```

**Wrong:** "PKCE doesn't work, let me just use implicit flow" (REJECTED approach)

<!-- gambit-backend:claude -->
## Creating the Next Task Based on Learnings
<!-- /gambit-backend -->
<!-- gambit-backend:codex -->
## Authoring the Next Worker Brief Based on Learnings
<!-- /gambit-backend -->

After completing "Set up OAuth config", you discover the framework has built-in session middleware:

```
<!-- gambit-backend:claude -->
TaskCreate
  subject: "Integrate with existing session middleware"
  description: |
<!-- /gambit-backend -->
<!-- gambit-backend:codex -->
Present in the checkpoint as "Worker Brief: Integrate with existing session middleware":
<!-- /gambit-backend -->
    ## Goal
    Use framework's built-in session middleware instead of custom implementation.

    ## Files owned
    - src/middleware/session.ts
    - tests/middleware/session.test.ts

    ## Hidden shared surfaces
    - None (no manifest, generated registry, route table, or snapshot changes)

    ## Neighbors
    - None (single-task wave)

    ## Implementation
    1. Study existing middleware: src/middleware/session.ts:15-40
    2. Write test: auth token stored in session correctly
    3. Integrate OAuth token storage with existing session
    4. Verify: session persists across requests

    ## Success Criteria
    - [ ] OAuth tokens stored via existing session middleware
    - [ ] No duplicate session logic
    - [ ] Tests passing
<!-- gambit-backend:claude -->
  activeForm: "Integrating session middleware"
<!-- /gambit-backend -->
```
<!-- gambit-backend:codex -->

Then replace the complete ordered plan, preserving prior wave statuses:

```
SessionPlanWrite
  plan:
    - step: "Wave 1: Configure OAuth"
      status: completed
    - step: "Wave 2: Integrate existing session middleware"
      status: pending
```
<!-- /gambit-backend -->

<!-- gambit-backend:claude -->
This task would not have been correct if planned upfront — it reflects what you actually found.
<!-- /gambit-backend -->
<!-- gambit-backend:codex -->
This worker brief would not have been correct if drafted upfront — it reflects what you actually found.
<!-- /gambit-backend -->
