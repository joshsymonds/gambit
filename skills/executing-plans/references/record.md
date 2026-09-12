# The epic record

## Where the record lives

One directory per epic, outside every repository and every workspace: `~/.gambit/<repository-id>/<epic-slug>/`. Nothing is written into a tree under version control, so the epic survives a rebuilt workspace, a discarded branch, and a fresh session.

Derive repository-id from the tree: the basename of the parent of `git rev-parse --path-format=absolute --git-common-dir`, a hyphen, then the first seven characters of the root commit from `git rev-list --max-parents=0 HEAD | tail -1`. Ask for the absolute path format. The bare form prints a relative `.git` at a repository toplevel, whose parent is `.`, so the same repository would resolve one identifier from its toplevel and another from a linked workspace. epic-slug is the epic's kebab-case name, fixed at acceptance.

The directory holds five files:

- `epic.md` — the eight contract sections, frozen at acceptance.
- `decisions.md` — the Decision Log, append-only.
- `state.json` — the head: where this epic stands now.
- `gates/<task-slug>-<attempt>.md` — one gate record per attempt.
- `efforts/<n>.md` — one summary per finished effort.

## The three carriers

`epic.md` is frozen. Intent, Premises with their survival clauses, and Requirements do not change after acceptance. A later assessment becomes a Decision Log line and leaves that text intact.

`state.json` is the head and is rewritten in place. Task status fields flip as work moves, and `next_actions` is rewritten every effort to name what the next reader does first. Keep it under 200 lines; it is the head, not the archive. Detail belongs in the gate and effort files it addresses.

`decisions.md` is append-only. A reversal appends a new line naming the entry it supersedes; no existing line is edited or removed. Each entry carries six fields in this order: id, timestamp, decision, reason, evidence, supersedes.

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
  "tasks": [
    {
      "id": 11,
      "slug": "<task-slug>",
      "subject": "<one line naming the result>",
      "requirement": "R3",
      "owned_files": ["<exact path>"],
      "lineage": {"parent": null, "descendants": [], "split_used": false},
      "rung": "<rung name>",
      "attempts": 1,
      "status": "<pending, dispatched, gated, done, split, or gap>",
      "gate_paths": ["gates/<task-slug>-1.md"]
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
  "next_actions": ["<the first thing the next reader does>"],
  "never_drop": ["<carried fact>"]
}
```

Those top-level keys are the whole head, and every task entry carries exactly the keys shown.

## Decomposition

Three task fields carry decomposition. `requirement` names the contract items the task satisfies, so an unmet Requirement is traceable to the work that covers it. `owned_files` is the exact disjoint path list the task may write. `lineage` records where the task came from: `parent` is the task it was split out of, `descendants` lists the tasks split out of it, and `split_used` records that this task's one split has been spent.

A split parent stays in `tasks` with `split_used` set and its descendants named. Its children each name it as `parent`. The chain is how a reader with no transcript sees that a behavior was already divided once.

## Gates and efforts

Gate and effort files are addressed by path, never inlined into the head. A gate record is written for every attempt at `gates/<task-slug>-<attempt>.md`, and the task's `gate_paths` lists what exists. Each finished effort writes `efforts/<n>.md`: what was built, what integrated, and what the effort left open.

`never_drop` carries the facts that must survive every rewrite of the head: acceptance criteria, error signatures observed, and commands still needed. A fact leaves that list only when the work it guards is complete.

## Write protocol

Write the record before every dispatch and again as each return lands, so the head on disk is never behind the work. Write for a reader with no transcript: name paths absolutely, quote commands exactly, and give each timestamp in full ISO 8601 with its offset. A record that needs the conversation to interpret it has failed its one job.
