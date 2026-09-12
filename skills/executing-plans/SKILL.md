---
name: executing-plans
description: Takes an epic contract to its released result or evidenced terminal outcome.
when_to_use: Use when an epic record exists and work is ready, when continuing an active epic, or when implementation reveals the next effort. Not for defining a new contract.
user_invokable: true
---

# Executing Plans

## Start

Find the record directory by the rule in `references/record.md` and read its `epic.md`: Intent, Premises and their falsification clauses, Requirements and their named evidence, Must Not Ship, Quality Bar, Approach and Rejected Approaches, Done, Release, and the Decision Log. The contract alone authorizes work. Keep the Intent and Requirements fixed; assess defects by the contract's Quality Bar, not a stronger standard.

Resume the record whose `state.json` names the current epic branch, and only that one. When no record names it, refuse to resume: the run is fresh. A terminal run only shows its stored report; it dispatches nothing and repeats no external action. For an active run, recover from `state.json` the accepted base, candidate revision, tasks and lineages, rung positions and attempts used, split history, gate records, review state, and completed Release actions.

Write every transition to `state.json`, each gate record to `gates/<task-slug>-<attempt>.md`, and each effort report to `efforts/<n>.md`, all before the next dispatch. Mirror each transition through the harness's record-task-state operation so resumption preserves the ladder and review bounds and needs nothing but the record.

Use five harness operations: dispatch a role, record task state, load a stage, isolate a workspace, and end a run. Run Git, Done checks, and Release actions through the harness's shell. On a fresh run, isolate the epic with `git worktree add -b <epic-branch> <epic-workspace> <base>`. Resume in that workspace. Never execute on the main branch.

Read `contracts/models.md` and resolve every dispatched role through the registry at `~/.claude/gambit/models.json`. Look up the role, select its entry or gate-required next rung, and select the rung's dispatch target, using the read-only variant for a read-only role. Use the dispatch operation with the role's contract by absolute path and its complete brief as text. Resolve contract paths from the current installation. The `worker` and `escalation` roles use `contracts/worker.md`; `scout` uses `contracts/scout.md`. There is no fallback dispatch target. If the registry is absent or a role cannot be resolved, record the unresolved role in the Decision Log. Every task requiring it becomes a gap that cites the role. Independent work continues, and the run ends with gaps only when no executable work remains.

Dispatch the `orchestrator` role once per effort, once for review, and once for release. Its brief is the record directory and the effort number; it reads the record for everything else and writes its result back there. Read only the report that dispatch returns. When the registry resolves no `orchestrator` role, the session that loaded this stage performs the effort, review, or release itself under these same rules, inventing no dispatch target and owning the record writes: `state.json` before every dispatch, `gates/<task-slug>-<attempt>.md` for each return, and `efforts/<n>.md` at the effort's end.

## Decompose the next effort

An effort is one round of decomposition, building, and integration. From the unmet Requirements, create every task writable from the tree now, until each unmet Requirement not blocked by a gap has one. Do not author a full task tree. Work needing an unfinished interface or overlapping owned files belongs to a later effort.

Each brief carries these sections in order:

- **Goal:** the concrete result required of this task.
- **Files owned:** every exact repository-relative writable path, including additions and deletions. No directory or glob allowlists.
- **Hidden shared surfaces:** implicit writes such as lockfiles, generated indexes, registries, or snapshots; state none when absent. These grant no ownership.
- **Neighbors:** concurrent tasks and their complete owned-file lists, all off-limits.
- **Implementation:** steps grounded in the current tree and verified interfaces, under the worker contract.
- **Requirements covered:** contract identifiers and their named evidence.
- **Test command:** the task's exact fast check from Done.

Give the brief its workspace and base revision, the applicable contract clauses, and evidence needed to implement without session history. Keep simultaneous tasks' owned-file lists disjoint, including hidden surfaces. Do not manufacture parallelism by separating parts that require one another's unfinished output.

When a brief needs facts, dispatch a read-only `scout` with the bounded question and workspace. Use its `file:line` evidence or NOT FOUND to complete the brief. Decide from the contract and tree, and put each decision and reason in the Decision Log. Observations beyond the contract never become tasks.

## Build each task until good

Isolate each worker in its own workspace from the effort's base, including a single-task effort. Dispatch independent tasks concurrently. A new task starts at the `worker` entry rung, under its contract and brief, test first. Workers change only their owned files and leave every change uncommitted. Only the orchestrator commits. Workers implement; the orchestrator implements only the final attempt the routing below names.

For every return, inspect the complete change set, including staged, unstaged, untracked, deleted, binary, symlink, and mode changes. Read the actual artifacts and fresh RED/GREEN evidence, not just a diff summary or a worker's verdict. Run any missing named check. For a Requirement whose evidence is a rendered result, build or capture that result and look at it yourself; record the observed result against that Requirement. Source inspection is not rendered evidence.

Write this gate record, with exactly these fields:

| Field | Value |
|---|---|
| Task | Task identifier and subject |
| Lineage | Parent and descendants, including whether its one decomposition has occurred |
| Rung | The rung that produced this return |
| Candidate revision | Inspected base and complete change-set evidence; replace with the committed candidate revision after integration |
| Contract items checked | Every applicable Requirement, Must Not Ship entry, and minimal-change obligation, each with its command or inspection, result, and cited evidence |
| Owned-files result | Complete changed-path list checked against the exact allowlist |
| Mechanical-floor result | Evidence for checks, test quality, live code, error handling, and introduced security or data-loss paths |
| Premises touched | Each relevant Premise, evidence, assessment, and consequence of its clause |
| Verdict | DONE or NOT DONE, itemized against the contract |
| Next action | Integration, the next dispatch, decomposition, gap, or catastrophe, with its reason |

The mechanical floor rejects suppressed checks, weakened or tautological tests, dead code, unhandled errors, and reachable security or data-loss failures introduced by the change. Minimal change rejects work the contract did not request, including hardening against unnamed failure modes. Closing an error, security, or data-loss path opened by this change is required. Everything else noticed goes to the Decision Log as an observation, not a defect or work item.

Apply a touched Premise's clause before further building. If false and the Intent survives, record the changed assessment and evidence in the Decision Log, follow the clause's alternative, and revise the affected approach or briefs. Keep the frozen Premise text, its clause, Intent, and Requirements unchanged; continue executable work under the revised design. If the clause says the Intent cannot survive, apply Human boundaries immediately.

Worker returns DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, and BLOCKED are evidence for this gate, not terminal outcomes. Supply missing context from the tree or contract. A concern counts only if evidence establishes a contract defect. An unsatisfied task receives NOT DONE regardless of the worker's return label.

Every NOT DONE record names its cause, and the cause decides the next action. An **exact fix** is one the gate can state completely: an owned path the brief omitted, a value or decision the brief left out, or one named check with its failing output. **Too large** means the return shows the task does not fit one pass. Everything else is a failure the gate cannot reduce to a fix; an unchanged re-dispatch is never the answer to one.

Route each gate deterministically:

1. **DONE:** retain the complete accepted change set for integration.
2. **NOT DONE with an exact fix, on this rung's first attempt:** dispatch the same rung again with the corrected brief, the gate record, the contract path, and the current work. A rung gets two attempts at a task and never a third; a second NOT DONE at that rung routes by its cause below.
3. **NOT DONE, too large:** split the task now into complete smaller tasks covering the same unmet Requirements, whatever its rung. Record the parentage and the consumed split. Each descendant starts at the entry rung under these same rules; descendants never split, and a lineage splits once.
4. **NOT DONE otherwise, below the top rung:** resolve `escalation` for exactly the next rung on this task's ladder. Carry the gate record, complete brief, contract path, and current work into that dispatch. Never move down, skip a rung, or let an agent choose its rung.
5. **NOT DONE at the top rung:** make one final attempt yourself in the task's workspace under `contracts/worker.md`, with the complete history of gate records, and gate that work like any return. If it is NOT DONE, or the lineage has already used this attempt, mark the lineage as a gap: commit its workspace to `gap/<task-slug>`, retain its final gate record, exclude the lineage's work from integration, and continue every independent task. A gap does not end executable work elsewhere.

This step has no separate review dispatch or corrective loop outside the ladder.

## Integrate and repeat

Gate each complete worker change set before combining it. Commit accepted work onto the effort's candidate, one commit per task, and record the committed revision in its gate record. Workers never commit. A gap's work is not candidate material.

For a multi-task effort, read `references/wave-dispatch.md` and run `scripts/integrate_wave.py` by absolute path with its manifest. Use the full Done gate as the manifest gate. The script combines complete worker trees as ordered commits in an isolated candidate and advances the epic only to the exact revision passing that gate. For a single task, create the candidate commit separately from the accepted base, run the same full Done gate, and advance only on green. Preserve the last accepted base until the combined candidate passes.

For a failure appearing only after combination, record the complete routing decision before further investigation: itemized NOT DONE, the responsible lineage and ladder action, the rejected revision retained on `candidate/<effort>` with its failing output, the last accepted base unchanged until the combined candidate passes the full Done gate, and the independent tasks continuing during correction. Assign the failure to its contributing lineage, or create one integration lineage for this effort. An existing contributing lineage continues from the rung it used and the attempts it has spent there; a new integration lineage starts at the entry rung. Keep this ownership for subsequent failures rather than creating fresh lineages to reset the ladder.

Use the build step's second-attempt, split, escalation, final-attempt, and gap rules for that failure. The corrective workspace must contain the failing combination so its tests reproduce the integration defect. Continue independent executable tasks meanwhile. A task's passing fast check cannot substitute for a fresh full Done gate on the corrected combined candidate.

If an integration lineage exhausts, preserve its work and gate as a gap and retain the rejected candidate. Build any remaining candidate from the last accepted base and independent DONE changes, excluding work dependent on the gap, then run its full Done gate. Never advance the accepted base to a rejected revision.

Repeat from decomposition until every Requirement is DONE with its named evidence or is a gap. When no executable work remains, a Requirement depending on a gap becomes a gap citing that dependency. Task completion alone does not establish Requirement completion.

## Review once

Freeze one candidate after the build loop. Load `skills/review/SKILL.md` through the load-a-stage operation and follow it for that candidate. Record that review began so a resume cannot start another discovery pass.

Route contract defects through one correction round using the build step, including its ladder and gap rules. Then perform review closure and fresh full Done checks on the resulting candidate. A finding still open is a review gap; do not open another correction round or restart review. Record gaps and their evidence. Review never releases; release remains this stage's next decision.

## Release

Release is eligible only when every Requirement is DONE, review is clean, and the fresh Done checks pass. Otherwise execute no Release action and proceed to the report with gaps. A clean review cannot authorize a partial release.

For an eligible candidate, execute the Release section's exact actions in order through the shell, against their named targets and intended effects. Record each completed action and evidence immediately. On resume, use that record and inspect postconditions instead of repeating completed external actions.

An action that fails or cannot be confirmed ends the sequence as a release gap. Record the failure and all actions already completed; execute no later action. Report release only when every Release postcondition holds. Before any external action, apply Human boundaries.

## Report and end

Always write the report, including after catastrophe. It contains:

- What was released, or why nothing was released.
- Every decision and compromise with its reason.
- Changed Premise assessments and their evidence.
- Every gap, its gate evidence, and its `gap/<task-slug>` branch where work exists; identify retained `candidate/<effort>` branches too.
- Completed external actions and their observed effects.
- Rungs used by task and lineage.

Record exactly one terminal outcome: **released**, **ended with gaps**, or **stopped on catastrophe**. Store the report with that outcome, then use the harness's end-a-run operation. For each harness, use the end-a-run realization mapped in `README.md`'s Install section. A terminal resume only shows the report.

## Human boundaries

Catastrophe ends the run immediately when either condition holds:

- A Premise is false and its frozen clause says the Intent cannot survive.
- The next action is an irreversible external action that Release does not explicitly authorize by action, target, and intended effect.

Cease building and external actions, record the condition and evidence, report **stopped on catastrophe**, and end the run. Do not continue independent work after catastrophe.

Take no other external action the contract does not name either. A task needing one receives NOT DONE and becomes a gap; independent work continues. Every other decision, approach adjustment, decomposition, escalation, context resolution, validation, or gap is decided and logged. No mid-run question goes to a person.
