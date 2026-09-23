---
name: executing-plans
description: Takes an epic contract to its released result or evidenced terminal outcome.
when_to_use: Use when an epic record exists and work is ready, when continuing an active epic, or when implementation reveals the next effort. Not for defining a new contract.
user_invokable: true
---

# Executing Plans

## Start

Find the record directory by the rule in `references/record.md` and read its `epic.md`, the decision line, all ten sections, and the Decision Log. The contract alone authorizes work. Keep the Intent ("What you asked for") and Requirements ("What will be true when done") fixed; assess defects by the contract's Quality Bar, not a stronger standard. The level of care on the failure table's line and each failure row's What we do are the only guarding work the contract asks for; a rating by itself authorizes none.

Resume the record whose `state.json` names the current epic branch, and only that one; without one, the run is fresh. A terminal run only shows its stored report; it dispatches nothing and repeats no external action. For an active run, recover from `state.json` the accepted base, candidate revision, tasks and lineages, profile assignments and attempts used, split history, gate records, review state, and completed Release actions.

After compaction or resume, reload by role: the Director reloads `epic.md`, `decisions.md` by pointer, `state.json`, and the latest `efforts/<n>/report.md`; the Orchestrator reloads its effort brief and `efforts/<n>/state.json`; an implementer reloads its brief. Replace a lost child only after confirmed termination, attempts unchanged; reject an orphan return whose child identity or revision mismatches the recorded entry.

Write `state.json` before each dispatch and after each return; write each gate record to `gates/<task-slug>-<attempt>.md` before the next dispatch. Mirror each transition through the harness's record-task-state operation.

Use five harness operations: dispatch a role, record task state, load a stage, isolate a workspace, and end a run. Run Git, Done and Release through the shell. Isolate fresh epics with `git worktree add -b <epic-branch> <epic-workspace> <base>`. Never execute on main.

Read `contracts/models.md`; resolve roles through `~/.claude/gambit/models.json`. Select each entry model profile and its dispatch target, read-only variant for read-only roles. Pass the complete brief and contract's absolute path from the current installation: `contracts/implementer.md` for `implementer`, `contracts/scout.md` for `scout`. No fallback: log unresolved roles; every task requiring one becomes a gap citing it. Independent work continues; end with gaps only when no executable work remains.

Dispatch the `orchestrator` role once for review and once for release. Its brief is the record directory and the stage name; it reads the record for everything else and writes its result there. Read only the report that dispatch returns. When the registry resolves no `orchestrator` role, the session that loaded this stage performs the review or release itself under these same rules, inventing no dispatch target and owning the record writes.

## Director

The session that loaded this stage is the Director. From the accepted Requirements, build the change's dependency graph. Freeze shared interfaces as efforts that land first. Partition the remaining work into dependency-cohesive efforts with ownership exclusive among concurrent efforts, as many as the graph allows, and log the partition in the Director Decision Log; it creates no brief, task, or owned-file list.

An effort is dependency-ready once every effort it depends on has merged into the accepted base. Write an effort's brief only when it becomes dependency-ready, from the accepted base at that moment. Store it at `efforts/<n>/brief.md` with effort state at `efforts/<n>/state.json`. Each brief carries these fields in order:

- **Objective:** Requirements quoted with their named evidence.
- **Partition:** exact owned files; concurrent efforts' files are off-limits.
- **Interfaces and order:** frozen shared interfaces, dependencies, and landing order.
- **Binding contract:** the level of care with the row that set it, each applicable failure row quoted with its What we do, applicable Must Not Ship entries, Premise clauses, Quality Bar, and Decision Log entries touching its files.
- **Base:** accepted revision, branch `effort/<epic-slug>-<n>`, workspace, exact check commands, and the head's `efforts_admitted`.
- **Report shape:** required report lines and the `efforts/<n>/report.md` destination.

Admit an effort, whether a partition, a review correction, or a release correction, whenever an unmet Requirement, an open review finding, or a failed release action has executable work, incrementing the head's `efforts_admitted` before its dispatch and copying that count into the brief's Base field and `efforts/<n>/state.json`; resuming an existing effort admits nothing. There is no ceiling on efforts. End with gaps only when no executable work remains because every remaining lineage is exhausted or blocked by a gap, naming each unmet Requirement and the lineage that exhausted.

Before admitting any effort after the first, and whenever a report names new infrastructure, log one Director decision on whether the work adds infrastructure unnamed by the accepted approach, the accepted additions table ("Things you did not ask for"), or an accepted Decision Log proposal. That decision authorizes an in-repository, reversible addition such as a script, harness, fixture, or corpus that an unmet Requirement needs. A new machine, service, or external system is unauthorized; its dependent Requirements become gaps citing it.

Dispatch every dependency-ready effort concurrently to a fresh orchestrator in its own worktree, first persisting the child identity, workspace, revision, and lineage in the head's efforts entry. When a report reveals a defect in the effort brief, log the Director's error, correct the brief, and dispatch a fresh orchestrator. Merge each finished effort branch into the epic branch in completion order and run the full Done gate on the merged epic after each merge. On green, advance the accepted base to that revision, then brief and dispatch every effort now dependency-ready, including work a report left open; on red, follow `references/wave-dispatch.md`. Fold report lines into the head; take no other tree action. When the registry resolves no `orchestrator` role, the Director performs each effort itself under the orchestrator rules above, inventing no dispatch target and owning the effort's record writes.

For an effort dispatch, the orchestrator input is the effort brief and code only, never the record. It decomposes into as many disjoint-file tasks as the behaviors allow and dispatches every independent task concurrently. It writes tasks, gates, and effort-local decisions under `efforts/<n>/` and returns `efforts/<n>/report.md` in under 400 words.

## Decompose the next effort

An effort is one round of decomposition, building, and integration. From the unmet Requirements, create every task writable from the tree now, until each unmet Requirement not blocked by a gap has one. Work needing an unfinished interface or overlapping owned files belongs to a later effort.

Each brief carries these sections in order:

- **Goal:** the concrete result required of this task.
- **Files owned:** every exact repository-relative writable path, including additions and deletions. No directory or glob allowlists.
- **Hidden shared surfaces:** implicit writes such as lockfiles, generated indexes, registries, or snapshots; state none when absent. These grant no ownership.
- **Neighbors:** concurrent tasks and their complete owned-file lists, all off-limits.
- **Anchors:** exact current-tree file and line locations, interfaces, and evidence that ground the task.
- **Acceptance:** the named observable evidence that establishes the covered Requirements.
- **Constraints:** the level of care with the row that set it, each applicable failure row quoted with its What we do, and the applicable Must Not Ship entries and contract limits. Goal plus Acceptance plus Constraints stay under 250 words and contain no implementation steps, code, or diffs.
- **Requirements covered:** contract identifiers and their named evidence.
- **Test command:** the task's exact fast check from "Checks the machines run".

A task is one behavior with one failing test, at most three files including the test, every edit location known at brief time, and no change to an interface consumed by unowned files. Repetitive mechanical multi-file changes lift only the file cap. An atomic interface task may exceed three files when its interface and consumers must change together to stay green, and the exception is logged. Oversize splits before dispatch. Interface tasks land first. An implementer that reports a separable second behavior triggers a split. A task found oversize after dispatch splits at its next routing decision, before any further dispatch, interface task first, as that lineage's one split.

Give the brief its workspace, base revision, applicable contract clauses, and evidence sufficient without session history; keep simultaneous owned-file lists disjoint, including hidden surfaces.

When a brief needs facts, dispatch a read-only `scout` with the bounded question and workspace and complete the brief from its `file:line` evidence or NOT FOUND. Decide from the contract and tree, logging each decision and reason. Observations beyond the contract never become tasks.

## Build each task until good

Isolate each implementer in its own workspace from the effort's current base, including a single-task effort. Before every implementer dispatch, run `scripts/validate_dispatch.py` by absolute path against brief and record; dispatch only on exit 0, append exit 1 defects to `conduct.brief_defects`, and include `Brief: <absolute path>`, `Workspace: <absolute path>`, `Record: <absolute state.json path>`, and `Task: <id>` in prompt. A new task starts at the `implementer` entry model profile, under its contract and brief, test first. Only the orchestrator commits, and it implements only the final attempt the routing below names.

Inspect every return's complete staged, unstaged, untracked, deleted, binary, symlink, and mode changes. Read artifacts and fresh RED/GREEN evidence, not summaries or verdicts; run missing checks. Build or capture rendered Requirement evidence, inspect it, and record the observation.

After inspection and before the verdict, dispatch one read-only `task-reviewer` under `skills/review/reviewers/task-reviewer.md`: workspace, base, complete task change set, brief, covered Requirements, Must Not Ship, Quality Bar, and named check. Dispatch one read-only `finding-verifier` per admissible candidate under `skills/review/reviewers/finding-verifier.md`, with isolated `test-runner` reproductions as needed. A confirmed finding makes the verdict NOT DONE, routed below. Record drops and observations without tasks. Review correction deltas against their ledger citations; pre-existing defects outside them remain observations and never expand the ledger.

Write this gate record relative to the run's record directory, which for an effort is `efforts/<n>/`: `gates/<task-slug>-<attempt>.md`, with exactly these fields:

| Field | Value |
|---|---|
| Task | Task identifier and subject |
| Lineage | Parent and descendants, including whether its one decomposition has occurred |
| Model profile | The model profile that produced this return |
| Candidate revision | Inspected base and complete change-set evidence; replace with the committed candidate revision after integration |
| Contract items checked | Every applicable Requirement, failure row's What we do, Must Not Ship entry, and minimal-change obligation, each with its command or inspection, result, and cited evidence |
| Owned-files result | Complete changed-path list checked against the exact allowlist |
| Mechanical-floor result | Evidence for checks, test quality, live code, error handling, and introduced security or data-loss paths, plus a conduct assessment: files touched against the allowlist, dispatch inputs, state written before dispatch, and prevented and escaped violations appended to the task's conduct |
| Task review | Reviewer and verifier profiles, candidate claims, confirmed/dropped findings, and evidence paths |
| Premises touched | Each relevant Premise, evidence, assessment, and consequence of its clause |
| Verdict | DONE or NOT DONE, itemized against the contract |
| Next action | Integration, the next dispatch, decomposition, gap, or catastrophe, with its reason |

The mechanical floor rejects suppressed checks, weakened or tautological tests, dead code, unhandled errors, and reachable security or data-loss failures introduced by the change. Minimal change rejects work the contract did not request, including hardening against a failure mode no failure row names or beyond what its What we do says. Closing an error, security, or data-loss path opened by this change is required. Everything else noticed is a Decision Log observation, not a defect or work item.

Apply a touched Premise's If-wrong clause ("What I'm assuming") before further building. If false and the Intent survives, record the changed assessment and evidence in the Decision Log, follow the clause's alternative, and revise the affected approach or briefs. Keep the frozen Premise text, its clause, Intent, and Requirements unchanged; continue executable work under the revised design. If the clause says the Intent cannot survive, apply Human boundaries immediately.

Implementer returns DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, and BLOCKED are gate evidence, not terminal outcomes. Supply missing context from tree or contract. Concerns require evidence of contract defects; unsatisfied tasks are NOT DONE regardless of their return labels.

Every NOT DONE record names its cause. Its failure signature is the normalized failing check plus its first assertion or error line, persisted in task `state.json` with the step reached. An implementer has two attempts against a complete brief: its first dispatch and one continuation. A re-brief for the orchestrator's brief defect spends no attempt, and each split descendant starts with its own two. Take step 1 while an attempt remains and each other step once per distinct signature; repeats advance. Catastrophe applies only when evidence contradicts a Premise or Requirement.

1. **Execution failure against a complete brief:** hand the failing output back to the same implementer thread.
2. **Gate finding the brief wrong:** re-brief a fresh implementer and log an orchestrator error.
3. **Separable behaviors:** split them once per lineage, preserving the same unmet Requirements across complete descendants.
4. **The orchestrator's own attempt:** make the attempt in the task's workspace under `contracts/implementer.md`, with the complete history of gate records. If it fails, the lineage is a gap on `gap/<task-slug>`, independent work continues, and the run ends with gaps naming the Requirement as unsatisfied as written.

When a gate finding names an exact edit smaller than the brief that would describe it, the orchestrator applies it directly, logs it with the gate that named it, and counts no attempt. Beyond task review above, this routing sequence has no separate review dispatch or corrective loop.

## Integrate and repeat

Every accepted implementer change set, including a single task, lands only through `scripts/integrate_wave.py`, run by absolute path with a manifest as `references/wave-dispatch.md` describes and the full Done gate as its gate. The script makes one commit per task and advances the effort only on green; record each committed revision in its gate record and `state.json`. A gap's work is not candidate material. A wave integrates gated tasks without waiting for tasks still in routing, which then move to the new base as that reference describes.

For a failure appearing only after combination, record the complete routing decision before further investigation: itemized NOT DONE, the responsible lineage, the routing step reached, and the attempts spent there; the rejected revision retained on `candidate/<effort>` with its failing output, the last accepted base unchanged until the combined candidate passes the full Done gate, and the independent tasks continuing during correction. Assign the failure to its contributing lineage or one integration lineage for this effort. An existing contributing lineage continues from the routing step reached and the attempts it has spent there; a new integration lineage starts at the entry model profile. Keep this ownership for subsequent failures; never reset attempts with fresh lineages.

Use the build step's failure-signature routing for that failure. The corrective workspace must contain the failing combination so its tests reproduce the integration defect. A task's passing fast check cannot substitute for a fresh full Done gate on the corrected combined candidate.

If an integration lineage exhausts, preserve its work and gate as a gap and retain the rejected candidate. Build any remaining candidate from the last accepted base and independent DONE changes, excluding work dependent on the gap, then run its full Done gate. Never advance the accepted base to a rejected revision.

Write the effort's report to `efforts/<n>/report.md` when the effort ends. Repeat from decomposition until every Requirement is DONE with its named evidence or is a gap. When no executable work remains, a Requirement depending on a gap becomes a gap citing that dependency. Task completion alone does not establish Requirement completion.

## Review once

Freeze one candidate after the build loop and follow `skills/review/SKILL.md` for it through the load-a-stage operation. Record that review began so a resume cannot start another discovery pass.

Route each contract defect through the build step's failure-signature routing. Correct the candidate and re-run closure until closure passes, using the attempt and gap rules. A finding is a review gap only when no executable work remains for it. Review never releases; release remains this stage's next decision.

## Release

Release is eligible only when every Requirement is DONE, review is clean, and the fresh Done checks pass. Otherwise execute no Release action and proceed to the report with gaps. A clean review cannot authorize a partial release.

For an eligible candidate, execute the exact steps of "What leaves this machine or can't be undone" in order through the shell, against their named targets and intended effects; the postconditions after `Then:` are the Release postconditions. Record each completed action and evidence immediately. On resume, inspect postconditions from that record instead of repeating completed external actions.

An action that fails within the repository's own authority, including its tests, CI configuration, or build, opens a correction effort under the build step's failure-signature routing. Correct the failure, run its check, and Release resumes at the first action whose postcondition no longer holds; when every earlier postcondition still holds, that is the failed action, and no action whose postcondition holds is repeated. An action outside that authority that fails, or whose postcondition cannot be confirmed, is a release gap; a failure not shown to lie outside that authority is corrected as inside it. Record the failure and all actions already completed; execute no later action. Report release only when every Release postcondition holds. Before any external action, apply Human boundaries.

## Report and end

Always write the report, including after catastrophe. It contains:

- What was released, or why nothing was released.
- Every decision and compromise with its reason.
- Changed Premise assessments and their evidence.
- Every gap, its gate evidence, and its `gap/<task-slug>` branch where work exists; identify retained `candidate/<effort>` branches too.
- Completed external actions and their observed effects.
- For each task, whether it was DONE on its first attempt at the `implementer` entry model profile, every routing step it used, and its lineage.
- Implementer first-pass rate divides first-attempt DONE tasks by all tasks beside per-task-family conduct metrics from `scripts/report_metrics.py`: brief defects, violations prevented and escaped, routing steps, outcomes, cost, with raw numerators and denominators. If below 80%, flag decomposition.

Record exactly one terminal outcome: **released**, **ended with gaps**, or **stopped on catastrophe**. Store the report with that outcome, then use the harness's end-a-run operation as `README.md`'s Install section maps it.

## Human boundaries

Catastrophe ends the run immediately when either condition holds:

- A Premise is false and its frozen clause says the Intent cannot survive.
- The next action is an irreversible external action that the release steps do not explicitly authorize by action, target, and intended effect.

Cease building and external actions, record the condition and evidence, report **stopped on catastrophe**, and end the run. Do not continue independent work after catastrophe.

Take no other external action the contract does not name either. A task needing one receives NOT DONE and becomes a gap; independent work continues. Every other decision, adjustment, decomposition, context resolution, validation, or gap is decided and logged. No mid-run question goes to a person.
