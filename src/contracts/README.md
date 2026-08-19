# Agent classes

gambit dispatches work to subagents. **Every dispatch is a named CLASS with a contract** — never a
bare `general-purpose` agent improvised without one. When a skill needs a subagent it reaches for
one of these classes, passes the class contract by path, and dispatches the rung its role resolves
to (see [models.md](models.md)).

**The role enum is defined here and nowhere else.** There are six dispatch classes — `steelman`,
`worker`, `scout`, `finder`, `verifier`, `test-runner` — plus one worker re-dispatch role,
`escalation`, which reuses the **worker** contract on a higher rung rather than defining a class of
its own. That is the seven roles [models.md](models.md) resolves. A resolved rung never changes the
class contract or its authority.

> **Rule: dispatch a contracted class; never spawn a bare generic agent without a contract.**

**A class is not a `subagent_type`.** For a model rung, dispatch `subagent_type: "general-purpose"` for steelman / worker / finder / verifier / test-runner, or `subagent_type: "Explore"` for the read-only scout. For an agent rung, dispatch the rung's own `agent` (or `readonly_agent`) and pass no `model:`. Either way, attach the class by passing its **contract path** — the agent's first action is to Read it. There is no `subagent_type: "worker"` / `"scout"` / etc.

Each class dispatches on the rung its role resolves to — defaults: `contracts/models.md`.

| Class | Contract | Use it when |
|-------|----------|-------------|
| **steelman** | [steelman.md](steelman.md) | fresh read-only design collaboration during bounded discovery and closure |
| **worker** | [worker.md](worker.md) | implementing a task's code for executing-plans |
| **scout** | [scout.md](scout.md) | read-only investigation — find code/patterns/answers and return evidence (brainstorming, executing-plans, debugging) |
| **finder** | `skills/review/reviewers/{conformance,security,quality,performance}.md` | reviewing changed code for issues — all four at end-of-epic review; the `quality` finder alone, scoped to one diff, as the `executing-plans` checkpoint gate's escalation reviewer |
| **verifier** | `skills/review/reviewers/verifier.md` | kill-or-keep verifying candidate findings |
| **test-runner** | (none — a command + report) | running a test/build command and reporting its exact output + exit code |

`escalation` re-dispatches the **worker** contract on the next rung up the worker ladder; it is a
role, not a separate class.

Every default entry rung, every ladder, and the
`${CLAUDE_CONFIG_DIR:-$HOME/.claude}/gambit/models.json` config that overrides them are defined
once in [models.md](models.md).
