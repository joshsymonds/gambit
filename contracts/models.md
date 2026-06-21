# Model-tier resolution

Every agent gambit dispatches runs at an explicit model **tier** chosen by its role. Tiers are
resolved at dispatch — never inherited from the session — so a cheap role doesn't silently run on
the expensive orchestrator model.

## Roles and default tiers

| Role | Default tier | Why |
|------|-------------|-----|
| `finder` (review reviewers) | most-capable | recall ceiling — a missed finding is unrecoverable, no verifier recovers it |
| `verifier` (review verifier) | most-capable | code/security verification is as hard as finding; a cheap verifier rubber-stamps coherent-but-wrong findings and over-refutes real ones |
| `worker` (implementation) | standard | mechanical work from a clear brief |
| `escalation` (blocked worker) | most-capable | re-dispatch a worker that blocked needing more reasoning |
| `scout` (read-only Explore) | cheap-or-standard | output is cheaply checkable — the orchestrator spot-checks the cited `file:line` |
| `test-runner` | cheap | objective oracle (exit code) |

Tier words map to the harness's current generation: most-capable → `"opus"`, standard → `"sonnet"`,
cheap → `"haiku"` (or whatever the user pins). The orchestrator is the session model and is never
named here.

## Resolution at dispatch

1. Read `~/.claude/gambit/models.json` if present. Shape (any subset of keys):
   ```json
   { "worker": "<token>", "escalation": "<token>", "finder": "<token>",
     "verifier": "<token>", "scout": "<token>", "test-runner": "<token>" }
   ```
   Pass the value **verbatim** to the Task `model:` parameter — a tier alias (`"sonnet"`, `"opus"`,
   `"haiku"`) the harness maps to the live generation, or an exact model id to pin one. Because the
   value is transcribed from config, the orchestrator can target a model it has no training
   knowledge of — it copies the token, it does not recall it.
2. If the file is absent or a key is missing, fall back to the default-tier table above.

## Hard rules

- **Always set `model:` explicitly.** An omitted model — or `model: "inherit"` — silently inherits
  the expensive session model.
- **No concrete model ID lives in a skill or contract.** Defaults are tier aliases; exact IDs only
  ever come from `~/.claude/gambit/models.json`.
- **No cheap verifier for code/security review.** Verifying a subtle/security finding needs the same
  deep reasoning as finding it; a weak verifier gets gamed by a strong finder's coherent errors.
