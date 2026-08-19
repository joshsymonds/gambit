# Rung and role resolution

Every agent gambit dispatches runs on an explicit **rung** selected by its **role**. Rungs are
resolved at dispatch — never inherited from the session — so a cheap role never silently runs on
the expensive orchestrator model.

- A **rung** is one dispatchable step of capability: either a named subagent, or a harness model alias.
- A **role** is the job gambit needs done. Each role names an `entry` rung plus an ordered `ladder`
  of rungs to climb when the work does not clear.

[README.md](README.md) owns the role enum — the roles named below are the ones it defines. This
file owns rung and role resolution: which rung each role enters on, the ladder it climbs, and how
each rung shape is dispatched. No skill names a rung, an agent, or a model of its own.

## Configuration

Rungs and roles are declared in one JSON file:

```
${CLAUDE_CONFIG_DIR:-$HOME/.claude}/gambit/models.json
```

Expand it with that exact fallback. `CLAUDE_CONFIG_DIR` is unset in a default profile, so the file
normally resolves to `$HOME/.claude/gambit/models.json`.

### Schema

```json
{
  "rungs": {
    "<name>": {"agent": "<subagent_type>", "readonly_agent": "<subagent_type>"},
    "<name>": {"model": "<sonnet|opus|haiku|fable>"}
  },
  "roles": {
    "<role>": {"entry": "<rung>", "ladder": ["<rung>", ...], "readonly": true|absent}
  }
}
```

`rungs` maps each rung name to exactly one of two shapes:

- **Agent rung** — `agent` is the `subagent_type` to dispatch. `readonly_agent` is the
  `subagent_type` to dispatch instead when the caller needs a read-only agent.
- **Model rung** — `model` is one harness model alias: `sonnet`, `opus`, `haiku`, or `fable`.

`roles` maps each role name to its `entry` rung, its ordered `ladder` (lowest rung first), and an
optional `readonly` flag. A role whose `ladder` is absent has the implicit ladder `["<entry>"]` and
never escalates past its entry rung. `readonly` absent means the role may write.

## Dispatch

Resolve `role → rung`, then dispatch by the rung's shape:

| Rung shape | Dispatch |
|---|---|
| `{"agent": ...}` | `subagent_type: "<agent>"`, and **no `model:` parameter at all** |
| `{"agent": ..., "readonly_agent": ...}` for a read-only caller | `subagent_type: "<readonly_agent>"`, and **no `model:` parameter at all** |
| `{"model": ...}` | `subagent_type: "general-purpose"` — or `subagent_type: "Explore"` for a scout — with `model: "<alias>"` |

A role marked `readonly: true`, and every advisory dispatch (scout, steelman, finder, verifier),
uses `readonly_agent`. Everything else uses `agent`. A rung that declares `agent` but no
`readonly_agent` uses that same `agent` for read-only callers.

**Never put a foreign model id in a `model:` parameter.** The Agent tool's `model:` is enum-locked
to `sonnet`, `opus`, `haiku`, and `fable`. Anything else is not rejected — it is **silently
substituted**, so the dispatch succeeds and quietly runs on a model you did not choose, with no
error to notice. Agent rungs exist precisely to reach a non-enum model: that model is configured
inside the named agent, never passed through `model:`. So an agent rung carries no `model:` at all,
and every `model:` value gambit emits is one of those four aliases.

**Always set `model:` explicitly on a model rung.** An omitted `model:` — or `model: "inherit"` —
silently inherits the expensive orchestrator model.

**Never set `CLAUDE_CODE_SUBAGENT_MODEL`.** It is top-precedence and forces EVERY dispatched
subagent onto one model, collapsing every rung. Pin per-alias models with the
`ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`,
and `ANTHROPIC_DEFAULT_FABLE_MODEL` environment variables instead.

**On Bedrock an unpinned alias lags** — it resolves to an older generation than the same alias on
the Anthropic API, and that model may not even be enabled in your account. Under
`CLAUDE_CODE_USE_BEDROCK=1`, pin each alias to a full inference-profile ID with the environment
variables above rather than relying on alias auto-advance.

**No concrete model ID lives in a skill or contract.** gambit emits alias rungs and agent names;
exact IDs come from the config file, the agent definitions, or those environment variables.

## Built-in defaults

When the config file is absent, unreadable, or invalid, resolve every role from this built-in table
instead. An **absent** file is the ordinary case and needs no comment. An **invalid** file — bad
JSON, an unknown rung reference, a rung with neither `agent` nor `model` — falls back to these same
defaults *and* prints a visible one-line warning in the transcript naming the file and the exact
parse or validation error, so a broken config is never silently obeyed as if it were missing.

| Role | Entry rung | Ladder | Read-only |
|---|---|---|---|
| `worker` | `opus` | `opus` → `fable` | no |
| `escalation` | `fable` | `fable` | no |
| `scout` | `sonnet` | `sonnet` | yes |
| `steelman` | `fable` | `fable` | yes |
| `finder` | `fable` | `fable` | yes |
| `verifier` | `fable` | `fable` | yes |
| `test-runner` | `sonnet` | `sonnet` | no |

The built-in rungs are model rungs only — `opus`, `sonnet`, `haiku`, and `fable`, each resolving to
its own alias. gambit ships **no** agent-rung default: an agent name is environment-specific, and a
name that does not exist in the running harness would dispatch nothing. An agent rung exists only
because an operator declared one in the config file.

## Rung and ladder invariants

- **The orchestrator selects the entry rung.** It uses the role's default entry, or a HIGHER rung on
  the role's ladder when the task brief states difficulty that warrants it — never below the role's
  entry.
- **A dispatched agent never selects or changes its own rung.** A worker cannot promote itself, ask
  for a bigger model, or decline the rung it was given. Rung selection belongs to the orchestrator
  alone.
- **Never re-dispatch the same rung on unchanged evidence.** A repeat with nothing new added is the
  same call twice; something must change first.
- **Each escalation step moves UP the ladder**, carrying the updated evidence the previous rung
  produced — the cited defect, the failing output, the missing value.
- **The top rung repeats.** At the ladder's last rung, re-dispatch that same rung with updated
  evidence, again and again, until the defect clears. There is no human rung. For the roles that
  escalate — `worker` and `escalation` — the terminal rung is native Claude by config design, which
  is what preserves the 100%-solve invariant measured in the tiltyard ladder experiments (recorded
  outside this repo). An advisory or test-running role whose `ladder` is its entry rung alone never
  escalates at all.

## Roles

| Role | What it dispatches | Why its default entry |
|---|---|---|
| `steelman` (design collaborator) | read-only design collaboration during bounded discovery and closure | strengthens and challenges architecture without implementation authority |
| `finder` (review reviewers) | read-only audit of changed code | recall ceiling — a missed finding is unrecoverable, no verifier recovers it |
| `verifier` (review verifier) | read-only kill-or-keep of candidate findings | verifying a subtle or security finding is as hard as finding it; a weak verifier rubber-stamps coherent-but-wrong findings and over-refutes real ones |
| `worker` (implementation) | one bounded task from a complete brief | mechanical work from a clear brief, with the ladder above it for what the brief could not anticipate |
| `escalation` (blocked worker) | a re-dispatch of the worker contract carrying updated evidence | the rung a worker's defect climbs to; never selected by the worker itself |
| `scout` (read-only investigation) | bounded `file:line` discovery | output is cheaply checkable — the orchestrator spot-checks the cited `file:line` |
| `test-runner` | one exact command plus its report | objective oracle (exit code) |

**Scout escalation.** Enter `scout` one rung above its entry — when its ladder has one — for a
question about code flow, architectural intent, or "where else does this pattern appear": anything
where a confident but incomplete `NOT FOUND` would be acted on as if it were exhaustive. Citation
spot-checks catch a wrong answer; they do not catch an omitted path. A single-fact lookup stays at
the entry rung. Under the built-in defaults the scout ladder is one rung, so this matters only once
an operator configures a taller one.

**No cheap verifier for code or security review.** Verifying a subtle finding needs the same depth
as finding it; a weak verifier gets gamed by a strong finder's coherent errors.
