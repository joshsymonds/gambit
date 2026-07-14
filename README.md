# Gambit

![Fran and Balthier from Final Fantasy XII](gambit.png)

Structured development workflows for Claude Code and Codex.

## What is Gambit?

Gambit combines the polish of [superpowers](https://github.com/obra/superpowers) with the rigor of [hyperpowers](https://github.com/withzombies/hyperpowers). Claude uses native Tasks; Codex uses the native plan owned by the root Codex task, with one plan step per Gambit wave.

**Named after FF12's gambit system** — condition→action rules that let your party run autonomously. That's exactly what these skills provide for coding agents.

## Installation — Claude Code

```bash
/plugin marketplace add joshsymonds/gambit
/plugin install gambit@gambit
```

Verify installation:
```bash
/gambit
```

## Installation — Codex

```bash
codex plugin marketplace add joshsymonds/gambit
codex plugin add gambit@gambit
```

Restart Codex, then invoke a skill explicitly with `$gambit:using-gambit` or
let Codex select one from its description.

## Backend Assembly

Canonical skill prose and contracts live under `src/`. Run `just generate` to
assemble the committed `skills/` (Claude) and `plugins/gambit/skills/` (Codex) trees.
Backend-specific mechanics live under `src/backends/`; generated files are not
edited directly. `just check` rejects stale output and backend vocabulary leaks.

### Codex session ownership

Each root Codex task owns exactly one Gambit plan. Native `update_plan` is the
only way Gambit mutates that plan. The approved epic contract, complete worker
briefs, and checkpoint history remain in the root transcript; plan steps are
concise wave summaries. A parallel wave is still one in-progress step, with
each worker represented by its native subagent thread.

Resuming the same task continues its plan. `/new` starts empty. `/fork` copies
the plan and transcript context at the fork point, after which parent and fork
evolve independently. Missing plan state may be reconstructed only from the
same root session's approved contract and latest checkpoint. If native plan
mutation is unavailable, Gambit stops and asks the user instead of falling back
to repository state. Legacy Git-local Gambit state is ignored, left untouched,
and never migrated. Goals can authorize continuation hooks, but they are not
plan storage and Gambit does not create them automatically.

## Core Principles

- **Backend-native task state** — Claude uses native Tasks; Codex uses its root task's native session plan
- **One-wave-then-stop** — Human checkpoints after each serial or parallel wave
- **Immutable requirements** — Epic requirements don't change; tasks adapt to reality
- **Evidence over assertions** — Run verification, show output, then claim done
- **Small steps that stay green** — Tests pass between every change

## Skills

| Skill | Claude | Codex | Purpose |
|-------|--------|-------|---------|
| **using-gambit** | `/gambit` | `$gambit:using-gambit` | Session entry, skill discovery |
| **brainstorming** | `/gambit:brainstorming` | `$gambit:brainstorming` | Socratic design refinement |
| **executing-plans** | `/gambit:executing-plans` | `$gambit:executing-plans` | One-wave-at-a-time execution |
| **finishing-branch** | `/gambit:finishing-branch` | `$gambit:finishing-branch` | Merge/PR/discard workflow |
| **test-driven-development** | `/gambit:test-driven-development` | `$gambit:test-driven-development` | RED-GREEN-REFACTOR |
| **verification** | `/gambit:verification` | `$gambit:verification` | Evidence before completion |
| **debugging** | `/gambit:debugging` | `$gambit:debugging` | Systematic root cause analysis |
| **refactoring** | `/gambit:refactoring` | `$gambit:refactoring` | Safe incremental transforms |

## Basic Workflow

1. **Brainstorm** — Refine requirements through questions
2. **Approve contract and first wave** — Lock the epic requirements and initialize the backend-native plan
3. **Execute** — Work one wave at a time, stop for review
4. **Verify** — Show evidence before claiming done
5. **Finish** — Merge, PR, or cleanup

## Orchestrated Execution

During `executing-plans`, the active agent acts as an **orchestrator**: it dispatches a fresh worker subagent per work item instead of writing the code itself, staying free to plan, verify, and checkpoint. Every worker receives a self-contained brief and is bound by a shared worker contract — build only what the brief asks, never inspect or mutate orchestration state, test-first with evidence, and **stop and report** at the first sign of ambiguity or scope creep rather than guessing. Workers return one of four states (`DONE` / `DONE_WITH_CONCERNS` / `BLOCKED` / `NEEDS_CONTEXT`); the orchestrator routes on it and owns all commits.

Backend adapters choose appropriate worker roles. Claude resolves model tiers through `contracts/models.md`; Codex resolves built-in or custom agent profiles through `codex-contracts/models.md`.

## Why Not Just Use Superpowers/Hyperpowers?

| Feature | Superpowers | Hyperpowers | Gambit |
|---------|-------------|-------------|--------|
| Worktree setup | ✅ | ❌ | Automatic per epic (native `EnterWorktree`) |
| Task tracking | Markdown plans | bd/beads CLI | Native Tasks or native Codex session plans |
| Execution style | Batch (3 at a time) | One-then-stop | One-then-stop |
| Human checkpoints | Between batches | After every task | After every wave |
| Resource links | ✅ Work | ❌ Dead links | ✅ Work |

Gambit takes the best of both while adapting task and agent mechanics to each backend.

## Development Status

Gambit currently ships 13 generated skills for both Claude Code and Codex.

## Contributing

PRs welcome. Edit canonical sources under `src/`, then run `just check`.

## License

MIT

## Acknowledgments

Inspired by:
- [obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent
- [withzombies/hyperpowers](https://github.com/withzombies/hyperpowers) by Ryan Stortz
- [steveyegge/beads](https://github.com/steveyegge/beads) by Steve Yegge
