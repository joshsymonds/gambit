# Codex agent classes

Gambit dispatches work through named classes with binding contracts. Never
improvise a bare agent when a class exists. Resolve the contract path, pass it
to the subagent, and require the subagent to read it first.

> Dispatch a contracted class; never spawn a bare generic agent without a contract.

| Class | Contract | Codex fallback | Use it when |
|---|---|---|---|
| **worker** | [worker.md](worker.md) | `worker` | Implementing one bounded task |
| **scout** | [scout.md](scout.md) | `explorer` | Read-only discovery with file:line evidence |
| **finder** | `skills/review/reviewers/{conformance,security,quality,performance}.md` | `default` | Independent issue discovery |
| **verifier** | `skills/review/reviewers/verifier.md` | `default` | Kill-or-keep verification of candidate findings |
| **test-runner** | Command plus report contract | `worker` | Running an objective test/build oracle |

An installed custom agent with the class name takes precedence over the
fallback. Concrete model and reasoning choices live in Codex agent profiles,
not in skills. See [models.md](models.md).

Read contracts in the subagent's fresh context. The dispatcher passes their
absolute paths but does not load their full text into the long-lived main
context.
