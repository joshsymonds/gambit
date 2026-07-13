# Codex agent-profile resolution

Gambit assigns work by role. Prefer an installed custom Codex agent with the
matching role; otherwise use Codex's built-in `explorer`, `worker`, or
`default` agent as described below. Agent configuration owns concrete model
and reasoning settings—skills never pin a model ID.

| Gambit role | Codex agent fallback | Purpose |
|---|---|---|
| `finder` | `default` | Deep review where missed findings are costly |
| `verifier` | `default` | Independent confirmation or refutation |
| `worker` | `worker` | Focused implementation from a complete brief |
| `escalation` | `default` | Retry only after adding context or stronger reasoning |
| `scout` | `explorer` | Read-only codebase discovery with file:line evidence |
| `test-runner` | `worker` | Objective test execution and concise reporting |

## Hard rules

- Never encode a concrete model ID in a skill or contract.
- Never retry the same unchanged prompt with the same agent profile.
- A verifier must be capable of reasoning at least as deeply as the finder.
- Use read-only sandboxing for scouts, finders, and verifiers when the active
  Codex surface supports per-agent sandbox configuration.
- Custom profiles belong under `~/.codex/agents/` or project `.codex/agents/`;
  Gambit consumes them by role but does not overwrite personal model choices.
