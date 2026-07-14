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
built-in fallback. Concrete model and reasoning choices live in Codex agent
profiles, not in skills. See [models.md](models.md).

## Portable and profile-aware dispatch

Spawn metadata is hidden by default in Codex 0.144.3. A portable dispatch uses
only `task_name`, `message`, and `fork_turns: "none"`. It omits `agent_type`;
the binding contract named in the self-contained message still defines the
class, and Codex uses its built-in default spawning behavior.

Gambit's Nix configuration sets `hide_spawn_agent_metadata = false`. On that
profile-aware surface, a call may also set `agent_type` to the named class. An
installed class wins; otherwise select the built-in fallback in the table
above. Never add `model`, `reasoning_effort`, or `service_tier` to skill
examples.

Both forms use `fork_turns: "none"`. Gambit worker and reviewer briefs already
contain their complete context, so inheriting root-session turns adds noise and
breaks the isolation promised by the class contract.

Read contracts in the subagent's fresh context. The dispatcher passes their
absolute paths but does not load their full text into the long-lived main
context.
