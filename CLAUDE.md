# CLAUDE.md

Gambit is a dual-backend plugin providing structured development workflows for Claude Code and
Codex. Canonical prose lives in `src/`; a deterministic Python renderer assembles the backend
artifacts.

**Installation:** `/plugin marketplace add joshsymonds/gambit && /plugin install gambit@gambit`

## Edit `src/`. Everything else is generated.

```
src/                  # Canonical skills, contracts, backend adapters — EDIT HERE
agents/               # Shipped agent definitions (gambit-wrapper)
tools/                # render_skills.py — the renderer
tests/
skills/               # GENERATED — do not edit
contracts/            # GENERATED — do not edit
plugins/gambit/       # GENERATED — do not edit
```

All three of `skills/`, `contracts/`, and `plugins/gambit/` are build outputs. An edit made in any
of them is silently destroyed by the next `just generate` — this is the easiest way to lose work in
this repo, and `contracts/` is the one people reach for by name.

Run `just generate` after changing `src/`; run `just check` before committing.

**The tests assert exact source phrasings.** `tests/` pins substrings from skill prose (executor
resolution, fail-closed routing, scout dispatch shape). Rewording a sentence can fail a test that
is guarding real behavior — read the assertion before changing either side.

## Backend task state

Claude builds use Claude Code's Task tools as the source of truth.
Codex builds instead use native `update_plan`, with one concise plan step per wave and at most one
wave in progress. The root transcript carries the approved epic contract, the complete worker
briefs, and the checkpoints; concise wave steps never duplicate those records. Legacy repository
task files are ignored and untouched — there is no repository task store or migration.

## Releasing

`just release X.Y.Z` updates all three version manifests, regenerates, runs `just check`, and
commits. Don't bump versions by hand; `.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, and `src/backends/codex/plugin.json` must stay in sync.

It stages only the manifests and the generated trees — **not `src/`**. Commit your source changes
before releasing, or they will be left out of the release commit.

## Where things are owned

- `gambit:writing-skills` owns skill structure and authoring conventions.
- `executing-plans` owns the orchestrator/worker architecture.
- `src/contracts/README.md` owns the agent-class and role enum.
- `src/contracts/models.md` owns model tiers. No concrete model ID belongs in any skill.

Test a skill by invoking it as a subagent before finalizing.
