---
name: using-gambit
description: Use only when the user explicitly asks Gambit to route a concrete software task and has not already named a public workflow owner.
---

# Using Gambit

Route only an explicit request for Gambit workflow selection. Do not activate this router automatically.

## Owner Precedence

Choose exactly one owner; first match wins:

1. `executing-plans` — an active approved epic.
2. `debugging` — a concrete bug or unexpected behavior.
3. `review` — an explicit independent review.
4. `finishing-branch` — integration, merge, or pull-request work.
5. `writing-skills` — skill authoring or modification.
6. `brainstorming` — new or uncontracted design and planning.

Once selected, stop routing and follow that owner.

`test-driven-development` (TDD), `verification`, `refactoring`, `testing-quality`, and `task-refinement` are internal mechanics, not workflow owners. Parallelism is an implementation detail inside the selected owner.
