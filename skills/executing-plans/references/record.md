# The epic record

## Where the record lives

One directory per epic, outside every repository and every workspace: `~/.gambit/<repository-id>/<epic-slug>/`. Nothing is written into a tree under version control, so the epic survives a rebuilt workspace, a discarded branch, and a fresh session.

Derive repository-id from the tree: the basename of the parent of `git rev-parse --path-format=absolute --git-common-dir`, a hyphen, then the first seven characters of the root commit from `git rev-list --max-parents=0 HEAD | tail -1`. Ask for the absolute path format. The bare form prints a relative `.git` at a repository toplevel, whose parent is `.`, so the same repository would resolve one identifier from its toplevel and another from a linked workspace. epic-slug is the epic's kebab-case name, fixed at acceptance.

The directory holds the epic-level files and one directory per effort:

- `epic.md` — the eight contract sections, frozen at acceptance.
- `decisions.md` — the Director-level Decision Log, append-only.
- `state.json` — the head: where this epic stands now.
- `gates/<task-slug>-<attempt>.md` — one gate record per attempt.
- `efforts/<n>/` — one directory per effort. Each effort directory contains:
  - `efforts/<n>/brief.md` — the accepted brief for that effort.
  - `efforts/<n>/state.json` — that effort's tasks, dispatched child identity, workspace, revision, lineage, and the head's `max_efforts` and `efforts_admitted` at admission.
  - `efforts/<n>/gates/<task-slug>-<attempt>.md` — one gate record per attempt in that effort.
  - `efforts/<n>/decisions.md` — the effort-local Decision Log, append-only.
  - `efforts/<n>/report.md` — what the effort built, integrated, and left open.

## The three carriers

`epic.md` is frozen. Intent, Premises with their survival clauses, and Requirements do not change after acceptance. A later assessment becomes a Decision Log line and leaves that text intact.

`state.json` is the head and is rewritten in place. Task status fields flip as work moves, and `next_actions` is rewritten every effort to name what the next reader does first. Keep it under 200 lines; it is the head, not the archive. Detail belongs in the gate and effort files it addresses.

`decisions.md` is append-only and Director-level only. Every decision made within an effort belongs in that effort's `efforts/<n>/decisions.md`. A reversal appends a new line naming the entry it supersedes; no existing line is edited or removed. Each entry carries six fields in this order: id, timestamp, decision, reason, evidence, supersedes.

```text
- DL7 | 2026-02-04T11:20:06+00:00 | <decision> | reason: <why> | evidence: <file:line, finding id, or command> | supersedes: DL3
```

Write `supersedes: none` when the entry reverses nothing.

## state.json

```json
{
  "repository_id": "<repository-id>",
  "epic_slug": "<epic-slug>",
  "epic_branch": "epic/<epic-slug>",
  "workspace": "<absolute epic workspace>",
  "accepted_base": "<revision the current effort started from>",
  "candidate_revision": "<integrated candidate, or null>",
  "effort": 2,
  "max_efforts": 3,
  "efforts_admitted": 2,
  "done": ["<each task fast check from the contract's Done section, verbatim>"],
  "tasks": [
    {
      "id": 11,
      "slug": "<task-slug>",
      "subject": "<one line naming the result>",
      "requirement": "R3",
      "owned_files": ["<exact path>"],
      "lineage": {"parent": null, "descendants": [], "split_used": false},
      "profile": "<model profile name>",
      "attempts": 1,
      "status": "<pending, dispatched, gated, done, split, or gap>",
      "gate_paths": ["gates/<task-slug>-1.md"],
      "dispatch": {
        "child": null,
        "workspace": null,
        "revision": null
      },
      "conduct": {
        "brief_defects": ["<validator-reported defect>"],
        "violations_prevented": ["<violation prevented by routing>"],
        "violations_escaped": ["<violation that escaped routing>"],
        "routing_history": [
          {
            "signature": "<routing signature>",
            "step": "<routing step>",
            "attempt": 1
          }
        ],
        "outcome": "<pending, done, gap, or split>",
        "cost": {"turns": null, "tokens": null}
      }
    }
  ],
  "review": {"started": false, "candidate": null, "ledger": []},
  "release": {
    "actions": [
      {
        "action": "<exact action>",
        "target": "<repository, branch, or destination>",
        "effect": "<observable result>",
        "completed_at": null,
        "evidence": null
      }
    ]
  },
  "efforts": [
    {
      "n": 2,
      "branch": "effort/<epic-slug>-<n>",
      "workspace": "<absolute effort workspace>",
      "child": "<dispatched child identity or null>",
      "revision": "<effort revision>",
      "status": "<effort status>",
      "report": "efforts/<n>/report.md"
    }
  ],
  "next_actions": ["<the first thing the next reader does>"],
  "never_drop": ["<carried fact>"]
}
```

Those top-level keys are the whole head, and every task entry carries exactly the keys shown. `max_efforts` is the effort ceiling named in the frozen contract's Done section: a positive integer copied into the head at acceptance, bounding how many effort identities the run may admit; the head carries that value and never changes it. `efforts_admitted` counts every effort identity the Director has admitted so far, including concurrent partitions and review or release correction efforts; resuming an existing effort admits nothing. Both are copied into every effort brief's Base field and every `efforts/<n>/state.json`, and neither changes on resume. A head lacking `max_efforts` admits no effort: the run ends with gaps naming the missing ceiling. Each task's `dispatch` object carries exactly `child`, `workspace`, and `revision`; `child` and `revision` are strings or null, and `workspace` is an absolute path string or null. Write this object before dispatching the task's implementer, and keep all three values null until then. Each task's `conduct` object carries exactly `brief_defects`, `violations_prevented`, `violations_escaped`, `routing_history`, `outcome`, and `cost`. The first three are lists of strings from validation and routing; `routing_history` is a list of objects carrying exactly `signature`, `step`, and `attempt`; `outcome` is `pending`, `done`, `gap`, or `split`; and `cost` carries integer or null `turns` and `tokens`. Each effort entry carries exactly `n`, `branch`, `workspace`, `child`, `revision`, `status`, and `report`.

New task entries use `profile`. The validator also reads an existing `rung` field as the same assignment and accepts `--entry-rung` as an alias for `--entry-profile`. Conflicting values are rejected. Do not rewrite frozen records, evidence, attempt counts, or lineage merely to update terminology.

## Decomposition

Three task fields carry decomposition. `requirement` names the contract items the task satisfies, so an unmet Requirement is traceable to the work that covers it. `owned_files` is the exact disjoint path list the task may write. `lineage` records where the task came from: `parent` is the task it was split out of, `descendants` lists the tasks split out of it, and `split_used` records that this task's one split has been spent.

A split parent stays in `tasks` with `split_used` set and its descendants named. Its children each name it as `parent`. The chain is how a reader with no transcript sees that a behavior was already divided once.

## Gates and efforts

Gate records and effort history are addressed by path, never inlined into the head. A gate record is written for every attempt at `gates/<task-slug>-<attempt>.md`, and the task's `gate_paths` lists what exists. Each effort directory has its own `brief.md`, `state.json`, `gates/<task-slug>-<attempt>.md`, `decisions.md`, and `report.md` under `efforts/<n>/`. Its `state.json` carries the effort's tasks, dispatched child identity, workspace, revision, lineage, `max_efforts`, and `efforts_admitted`. Its `report.md` records what was built, what integrated, and what the effort left open.

The top-level `decisions.md` is Director-level only. Effort-local decisions are appended to `efforts/<n>/decisions.md`. Reopen history files by path and read only the needed section; never read a history file whole.

`never_drop` carries the facts that must survive every rewrite of the head: acceptance criteria, error signatures observed, and commands still needed. A fact leaves that list only when the work it guards is complete.

## Write protocol

Write the record before every dispatch and again as each return lands, so the head on disk is never behind the work. Write for a reader with no transcript: name paths absolutely, quote commands exactly, and give each timestamp in full ISO 8601 with its offset. A record that needs the conversation to interpret it has failed its one job.
