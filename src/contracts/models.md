# Model-tier resolution

Every agent gambit dispatches runs at an explicit model **tier** chosen by its role. Tiers are
resolved at dispatch — never inherited from the session — so a cheap role doesn't silently run on
the expensive orchestrator model.

## Roles and default tiers

| Role | Default tier | Why |
|------|-------------|-----|
| `steelman` (design collaborator) | most-capable | strengthen and challenge architecture without implementation authority |
| `finder` (review reviewers) | most-capable | recall ceiling — a missed finding is unrecoverable, no verifier recovers it |
| `verifier` (review verifier) | most-capable | code/security verification is as hard as finding; a cheap verifier rubber-stamps coherent-but-wrong findings and over-refutes real ones |
| `worker` (implementation) | standard | mechanical work from a clear brief |
| `escalation` (blocked worker) | most-capable | re-dispatch a worker that blocked needing more reasoning |
| `scout` (read-only Explore) | cheap-or-standard | output is cheaply checkable — the orchestrator spot-checks the cited `file:line` |
| `wrapper` (async transport relay) | standard | pure transport relay, zero judgment — one configured MCP call plus one artifact write, and failure handling that must stay honest rather than fabricate an envelope |
| `test-runner` | cheap | objective oracle (exit code) |

Tier words map to the harness model **aliases**: most-capable → `"opus"`, standard → `"sonnet"`,
cheap → `"haiku"`. The orchestrator is the session model (often `"fable"`) and is never named here.

## Resolution at dispatch

The orchestrator sets `model:` to the tier's **alias** (`"sonnet"` / `"opus"` / `"haiku"`); gambit
names no concrete model. WHICH concrete model an alias maps to is controlled OUTSIDE gambit —
identically on the Anthropic API and on Amazon Bedrock:

1. **Native env vars (primary, recommended).** `ANTHROPIC_DEFAULT_SONNET_MODEL`,
   `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, `ANTHROPIC_DEFAULT_FABLE_MODEL`
   set what each alias resolves to; `ANTHROPIC_MODEL` sets the orchestrator/session model. Point them
   at full IDs (Anthropic IDs locally; full Bedrock inference-profile IDs under
   `CLAUDE_CODE_USE_BEDROCK=1`). Switching a whole tier to a new generation is a ONE-env-var change —
   no gambit edit.
2. **Alias auto-advance.** If you don't pin, an alias maps to the provider's current recommended model
   and advances when you UPDATE the Claude Code CLI. **On Bedrock an unpinned alias lags** (e.g.
   `sonnet` → an older Sonnet) and may not be enabled in your account — so on Bedrock, pin via the
   env vars in (1).
3. **Optional per-role override** — `~/.claude/gambit/models.json`, needed ONLY when a role must use a
   different model than its tier's alias (e.g. `verifier` ≠ `finder` though both are most-capable).
   Shape (any subset): `{ "steelman": "<id>", "worker": "<id>", "escalation": "<id>", "finder":
   "<id>", "verifier": "<id>", "scout": "<id>", "wrapper": "<id>", "test-runner": "<id>" }`. The
   orchestrator reads it and passes the value **verbatim** to `model:`. Absent / missing key → use
   the tier alias (resolved per 1–2). Most setups don't need this file — the native env vars cover
   per-tier pinning on both API and Bedrock.

## Hard rules

- **Model-tier selection is separate from executor selection.** The tier above controls native
  Claude dispatch. A configured external executor supplies its own model from
  [executors.md](executors.md); neither registry selects or rewrites the other.
- **Always set `model:` explicitly** to the tier alias (or an override value). An omitted model — or
  `model: "inherit"` — silently inherits the expensive session/orchestrator model.
- **Never set `CLAUDE_CODE_SUBAGENT_MODEL`.** It is top-precedence and forces EVERY dispatched
  subagent onto one model, collapsing all role tiers. Pin per-line models via the
  `ANTHROPIC_DEFAULT_*_MODEL` env vars instead.
- **No concrete model ID lives in a skill or contract.** gambit emits only tier aliases; exact IDs
  come from the env vars or the optional `models.json`.
- **No cheap verifier for code/security review.** Verifying a subtle/security finding needs the same
  deep reasoning as finding it; a weak verifier gets gamed by a strong finder's coherent errors.
