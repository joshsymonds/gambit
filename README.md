# Gambit

![Fran and Balthier from Final Fantasy XII](gambit.png)

Structured development workflows for Claude Code using native Tasks.

## What is Gambit?

Gambit combines the polish of [superpowers](https://github.com/obra/superpowers) with the rigor of [hyperpowers](https://github.com/withzombies/hyperpowers), replacing external tooling (beads/bd) with **native Claude Code Tasks**.

**Named after FF12's gambit system** — condition→action rules that let your party run autonomously. That's exactly what these skills provide for Claude.

## Installation

```bash
/plugin marketplace add joshsymonds/gambit
/plugin install gambit@gambit
```

Verify installation:
```bash
/gambit
```

## Core Principles

- **Native Tasks** — No external CLI, just `TaskCreate`/`TaskUpdate`/`TaskList`
- **One-task-then-stop** — Human checkpoints after each task
- **Immutable requirements** — Epic requirements don't change; tasks adapt to reality
- **Evidence over assertions** — Run verification, show output, then claim done
- **Small steps that stay green** — Tests pass between every change

## Skills

| Skill | Command | Purpose |
|-------|---------|---------|
| **using-gambit** | `/gambit` | Session entry, skill discovery |
| **brainstorming** | `/gambit:brainstorming` | Socratic design refinement |
| **executing-plans** | `/gambit:executing-plans` | One-task-at-a-time execution |
| **using-worktrees** | `/gambit:using-worktrees` | Git worktree + devenv setup |
| **finishing-branch** | `/gambit:finishing-branch` | Merge/PR/discard workflow |
| **test-driven-development** | `/gambit:test-driven-development` | RED-GREEN-REFACTOR |
| **verification** | `/gambit:verification` | Evidence before completion |
| **debugging** | `/gambit:debugging` | Systematic root cause analysis |
| **refactoring** | `/gambit:refactoring` | Safe incremental transforms |

## Basic Workflow

1. **Brainstorm** — Refine requirements through questions
2. **Write plan** — Create epic Task with subtasks and dependencies
3. **Execute** — Work one task at a time, stop for review
4. **Verify** — Show evidence before claiming done
5. **Finish** — Merge, PR, or cleanup

## Orchestrated Execution

During `executing-plans`, Claude acts as an **orchestrator**: it dispatches a fresh worker subagent per task instead of writing the code itself, staying free to plan, verify, and checkpoint. Every worker is bound by a shared [worker contract](contracts/worker.md) — build only what the task asks, test-first with evidence, and **stop and report** at the first sign of ambiguity or scope creep rather than guessing. Workers return one of four states (`DONE` / `DONE_WITH_CONCERNS` / `BLOCKED` / `NEEDS_CONTEXT`); the orchestrator routes on it and owns all commits.

Worker models are chosen by capability tier — a cheaper, faster model does the mechanical work, and the orchestrator escalates a blocked task to a stronger one — configurable via `~/.claude/gambit/models.json`.

## Why Not Just Use Superpowers/Hyperpowers?

| Feature | Superpowers | Hyperpowers | Gambit |
|---------|-------------|-------------|--------|
| Worktree setup | ✅ | ❌ | ✅ + devenv |
| Task tracking | Markdown plans | bd/beads CLI | Native Tasks |
| Execution style | Batch (3 at a time) | One-then-stop | One-then-stop |
| Human checkpoints | Between batches | After every task | After every task |
| Resource links | ✅ Work | ❌ Dead links | ✅ Work |

Gambit takes the best of both and uses Claude Code's native Task system instead of external tooling.

## Development Status

🚧 **Work in Progress** — See [PLAN.md](PLAN.md) for the full roadmap.

Currently implemented:
- [x] Plugin structure
- [x] `using-gambit` skill
- [ ] `brainstorming`
- [ ] `executing-plans`
- [ ] ... (see PLAN.md)

## Contributing

PRs welcome. Follow the skill structure in `skills/using-gambit/SKILL.md` as a template.

## License

MIT

## Acknowledgments

Inspired by:
- [obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent
- [withzombies/hyperpowers](https://github.com/withzombies/hyperpowers) by Ryan Stortz
- [steveyegge/beads](https://github.com/steveyegge/beads) by Steve Yegge
