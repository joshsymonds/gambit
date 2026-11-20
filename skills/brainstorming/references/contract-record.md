# Contract record route

This route keeps the contract in Orrery's record from its first presentation. Each change goes out as a new version. Acceptance is recorded in Orrery, and the epic is created from the accepted version.

## When the route applies

The route applies when the session has the `contract_propose` tool, which `orrery mcp` serves. The route uses `contract_propose`, `contract_revise`, `contract_accept`, `contract_set_aside`, `contract_reopen`, and `epic_create`.

Without the contract tools, brainstorming runs as before, and nothing in this reference applies.

## Proposing

Call `contract_propose` when the contract is first presented for acceptance, after the steelman's dispositions are in it.

Compose `epic.md` and `contract.json` in the epic's record directory, `~/.gambit/<repository-id>/<epic-slug>/`, as `skills/executing-plans/references/record.md` specifies. The model composes both from the finalized design. Neither file is parsed into the other.

`contract.json` holds one JSON object. The object is the contract in Orrery's `EpicContract` protobuf JSON field names, the shape `contract_propose` reads, plus an optional `decisions` array. Its `id` is `<repository-id>/<epic-slug>`, and the call uses the same `id`.

Run `python3 skills/brainstorming/scripts/compare_contract.py <record>/contract.json <record>/epic.md`, where `<record>` is the record directory. On exit 0, call `contract_propose` with the `id`, the absolute path of `contract.json`, and `words`.

`contract_propose` stores version 1 in state `proposed`.

## Revising

Each later change edits `contract.json` and `epic.md`, and `skills/brainstorming/scripts/compare_contract.py` runs on the two. The changed contract goes out with `contract_revise` before it is presented.

`contract_revise` takes `id`, the absolute path of `contract.json`, and `words`. The `words` say what changed. The tool appends the file as the next version.

## Comparing

Run `skills/brainstorming/scripts/compare_contract.py` before every `contract_propose` and every `contract_revise`. A run with exit 0 means the data and the document agree, and the call may go out.

Exit 1 means a difference. The script names each difference in its output. Correct the data or the document, and run the script again.

Exit 2 means an input file is unreadable. The script names the file. Fix the file, and run the script again.

While the script exits non-zero, nothing is sent.

## Decisions

Each open choice under "Decisions I need from you" is an entry of the `decisions` array in the version. Each row under "Things you did not ask for" that the person decides to keep or strike is an entry too.

Each entry has these fields. `id` is `D` and a number. `question`, `options`, `recommendation`, and `reason` hold the decision's text. `row` names the F, R, or P id that the decision concerns, and is empty when none. `answer` is empty while the choice is open.

Write each `answer` when its choice is settled. An answer changes the contract, so it goes out as a revision under Revising.

`contract_accept` refuses while any `answer` is empty. Settle every decision before accepting.

## Acceptance

At acceptance, `epic.md` and `contract.json` already hold the newest version. The rest of the record directory is written as `skills/brainstorming/SKILL.md` states.

In conversation, when the person accepts, call `contract_accept` with `id` and the person's words. It moves the contract to `accepted` at its newest version.

Acceptance made elsewhere, by the owner in Orrery's apps or by another session, arrives as an event. An `<orrery-event kind="action">` block whose id begins `contract:<id>:` says who `accepted it` and at which version. The stage continues from that event.

When the person sets the contract aside, call `contract_set_aside` with `id` and the person's words. The stage stops.

An `<orrery-event kind="action">` block whose first line says `set it aside` stops the stage the same way.

Call `contract_reopen` with `id` and `words` to reopen a set-aside contract. It moves the contract back to `proposed`, and the stage resumes.

An `<orrery-event kind="action">` block whose first line says `reopened it` resumes the stage the same way.

With a goal file, no person accepts. The orchestrator answers every decision itself, revises the contract with those answers, and calls `contract_accept` with `id` and `words` that say the goal file accepted it. Then the stage continues to The epic.

## The epic

Once the record reads accepted, call `epic_create` with the contract's `id`. `epic_create` refuses a contract that is not accepted.

Call `epic_create` with `base` set to the repository's `HEAD`, the commit the epic starts from.

`epic_create` takes `decisions` as an array of objects, one for each Decision Log entry, each with its `id` and `text`.

Orrery runs the epic, and the conversation that made the contract steers it. `executing-plans` is not loaded.
