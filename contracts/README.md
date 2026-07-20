# Agent classes

gambit dispatches work to subagents. **Every dispatch is a named CLASS with a contract** — never a
bare `general-purpose` agent improvised without one. When a skill needs a subagent it reaches for
one of these classes, passes the class contract by path, and sets an explicit `model:` at the
class's tier (see [models.md](models.md)).

For all seven externally executable roles, [executors.md](executors.md) defines executor
selection independently from class and model-tier selection. A selected executor never changes
the class contract or its authority.

> **Rule: dispatch a contracted class; never spawn a bare generic agent without a contract.**
> A contractless agent has no blast-radius limit, no return protocol, and no tier — the disciplines
> these contracts encode simply evaporate.

> **Transport exception — `wrapper` only:** The async configured-executor wrapper defined by
> [async-dispatch.md](async-dispatch.md) is pure transport, not a contracted class. It reads no
> contract path. The dispatching orchestrator embeds its governing instructions verbatim from that
> contract. This exception grants zero judgment and applies only to the one configured MCP call and
> one artifact write defined there.

**A class is not a `subagent_type`.** Dispatch `subagent_type: "general-purpose"` for steelman / worker / finder / verifier / test-runner, or `subagent_type: "Explore"` for the read-only scout — and attach the class by passing its **contract path** (the agent's first action is to Read it) plus its **model tier**. There is no `subagent_type: "worker"` / `"scout"` / etc.

| Class | Contract | Default tier | Use it when |
|-------|----------|-------------|-------------|
| **steelman** | [steelman.md](steelman.md) | most-capable | fresh read-only design collaboration during bounded discovery and closure |
| **worker** | [worker.md](worker.md) | standard | implementing a task's code for executing-plans |
| **scout** | [scout.md](scout.md) | cheap-or-standard | read-only investigation — find code/patterns/answers and return evidence (brainstorming, executing-plans, debugging) |
| **finder** | `skills/review/reviewers/{conformance,security,quality,performance}.md` | most-capable | reviewing changed code for issues — all four at end-of-epic review; the `quality` finder alone, scoped to one diff, as the `executing-plans` checkpoint gate's escalation reviewer |
| **verifier** | `skills/review/reviewers/verifier.md` | most-capable | kill-or-keep verifying candidate findings |
| **test-runner** | (none — a command + report) | cheap | running a test/build command and reporting its exact output + exit code |

Each contract is read by the subagent in its own fresh context: the dispatcher resolves the path
and passes it, and does **not** read the contract into its own context. Model tiers and the
`~/.claude/gambit/models.json` override are defined once in [models.md](models.md).
