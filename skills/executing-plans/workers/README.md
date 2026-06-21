# Worker Briefs

Language-specific style contracts that the `executing-plans` orchestrator loads into a
dispatched `general-purpose` worker. This mirrors how the `review` skill specializes
generic agents with `reviewers/*.md`: the worker reads its brief by path in fresh context,
the orchestrator never reads the brief into its own context.

## Brief format

Each `<lang>.md` is **style rules only** — idiomatic patterns plus a "Never Do" list — with:

- **No YAML frontmatter.** These are not declared agents.
- **No `model:` field.** Model is chosen by the orchestrator at dispatch (see below), never
  baked into the brief.
- A short process header reminding the worker to follow `gambit:test-driven-development` and
  `gambit:verification`, and to **not commit** (the orchestrator commits at the checkpoint).

To add a language: drop in `<lang>.md` following the same shape and add its extension(s) to the
language-inference table below.

## Model-tier resolution

The orchestrator (the session model — whatever you launched, e.g. an orchestrator-class model)
is **never named** in any skill or brief. Only the *worker* and *escalation* models are resolved,
and only by **tier**, so nothing here drifts when model IDs change or a new generation ships that
postdates the orchestrator's training data.

Resolution order at every dispatch:

1. Read `~/.claude/gambit/models.json` if it exists. Shape:
   ```json
   { "worker": "<token>", "escalation": "<token>" }
   ```
   Each value is passed **verbatim** to the Task `model:` parameter. A value may be a stable tier
   alias (`"sonnet"`, `"opus"`, `"haiku"`) that the Claude Code harness maps to the current
   generation, or an exact model-id string (`"<exact-model-id>"`) when you want to pin one.
   Because the value is transcribed from config, the orchestrator can target a model it has no
   training knowledge of — it copies the token, it does not recall it.
2. If the file is absent, unreadable, malformed, or missing a key, fall back to defaults:
   - `worker` → `"sonnet"`
   - `escalation` → `"opus"`

Hard rules:

- **Always set `model:` explicitly.** An omitted model — or `model: "inherit"` — silently inherits
  the expensive session model, defeating the whole point.
- **No concrete model ID lives in a skill or brief.** Defaults are tier aliases; exact IDs only ever
  come from the user's `models.json`.

## Language inference

The orchestrator picks a brief from the task's **target files** (the files the task says it will
create or modify):

| Extension / path                                         | Brief            |
|----------------------------------------------------------|------------------|
| `.go`                                                    | `go.md`          |
| `.py`                                                    | `python.md`      |
| `.ts`, `.tsx`                                            | `typescript.md`  |
| `.rb`                                                    | `ruby.md`        |
| `.sh`, `.bash`, `Dockerfile`, `.github/workflows/*.yml`  | `devops.md`      |

- **Primary language** = the language of the most target files. Tie-break: the file with the most
  changes; failing that, the first target file listed in the task.
- **No matching brief** → dispatch a generic worker with **no brief** (still an explicit `model:`,
  still the TDD + verification instruction).

> Only `go.md` exists today; the other four briefs are ported in a later task. Inferring a language
> whose brief is not yet present is treated as "no matching brief" until that brief lands.
