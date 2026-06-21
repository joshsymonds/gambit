# Agent classes

gambit dispatches work to subagents. **Every dispatch is a named CLASS with a contract** — never a
bare `general-purpose` agent improvised without one. When a skill needs a subagent it reaches for
one of these classes, passes the class contract by path, and sets an explicit `model:` at the
class's tier (see [models.md](models.md)).

> **Rule: dispatch a contracted class; never spawn a bare generic agent without a contract.**
> A contractless agent has no blast-radius limit, no return protocol, and no tier — the disciplines
> these contracts encode simply evaporate.

| Class | Contract | Default tier | Use it when |
|-------|----------|-------------|-------------|
| **worker** | [worker.md](worker.md) | standard | implementing a task's code (executing-plans; parallel-agents fix-workers) |
| **scout** | [scout.md](scout.md) | cheap-or-standard | read-only investigation — find code/patterns/answers and return evidence (brainstorming, executing-plans, debugging) |
| **finder** | `skills/review/reviewers/{conformance,security,quality,performance}.md` | most-capable | reviewing changed code for issues |
| **verifier** | `skills/review/reviewers/verifier.md` | most-capable | kill-or-keep verifying candidate findings |
| **test-runner** | (none — a command + report) | cheap | running a test/build command and reporting its exact output + exit code |

Each contract is read by the subagent in its own fresh context: the dispatcher resolves the path
and passes it, and does **not** read the contract into its own context. Model tiers and the
`~/.claude/gambit/models.json` override are defined once in [models.md](models.md).
