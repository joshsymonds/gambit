# Codex agent-profile resolution

Gambit skills select classes; they never select concrete models or reasoning
effort. Prefer an installed custom Codex agent with the matching class;
otherwise use Codex's built-in `explorer`, `worker`, or `default` agent as
described below. Agent-profile configuration owns model and reasoning settings.

| Gambit class | Codex agent fallback | Purpose |
|---|---|---|
| `steelman` | `default` | Fresh read-only design collaboration |
| `finder` | `default` | Deep review where missed findings are costly |
| `verifier` | `default` | Independent confirmation or refutation |
| `worker` | `worker` | Focused implementation from a complete brief |
| `escalation` | `default` | Retry only after adding context or stronger reasoning |
| `scout` | `explorer` | Read-only codebase discovery with file:line evidence |
| `test-runner` | `worker` | Objective test execution and concise reporting |

## Hard rules

- Executor selection is separate from model and fallback selection. The Claude-side external
  executor registry does not participate in native Codex dispatch.
- Never encode a concrete model ID in a skill or contract.
- Never encode a concrete reasoning effort in a skill or contract.
- Never retry the same unchanged prompt with the same agent profile.
- A verifier must be capable of reasoning at least as deeply as the finder.
- Use read-only sandboxing for steelmen, scouts, finders, and verifiers when the active
  Codex surface supports per-agent sandbox configuration.
- Custom profiles belong under `~/.codex/agents/` or project `.codex/agents/`;
  Gambit consumes them by class but does not overwrite personal model choices.
