---
name: review
description: Judges the completed candidate against the epic contract.
when_to_use: Use for the end-of-epic review called by executing-plans, or when asked to review completed work against its epic record. Not for building tasks or releasing.
user_invokable: true
---

# Review

Produce the complete ordered actions and result from the supplied facts before explanation. When asked to describe rather than execute, complete that description without running actions; never defer or decline it. Decisions and gaps become records, never questions to a person.

## Freeze

Read the epic record. Freeze the candidate revision at entry and identify its base revision and the complete changes between them. Inspect exactly that frozen candidate against its Requirements, Must Not Ship, and fixed Quality Bar.

Do not follow the branch tip. Additional commits landing during review are excluded from inspection and from the correction base. Reviewing those commits would require a later review, which the loop never runs for this epic. The only successor considered here is the corrected candidate produced from the frozen candidate by this review's ledger tasks.

Read `contracts/models.md`. Resolve each role through its registry, starting at the role's entry rung and selecting its read-only variant for `finder` and `verifier`. Pass role contracts by absolute path from the current installation. An unresolved role is recorded in the Decision Log; work requiring it becomes a gap, while independent executable work continues. Do not substitute a dispatch target.

## Finders

Dispatch the `finder` role once for each dimension, concurrently. Each receives its contract by absolute path:

- `skills/review/reviewers/conformance.md`: Requirements, Must Not Ship, owned files, and minimal change.
- `skills/review/reviewers/security.md`: security and data-loss failures introduced by the change.
- `skills/review/reviewers/quality.md`: the worker contract's mechanical floor.
- `skills/review/reviewers/performance.md`: contract-named workload evidence and resource failures covered by the Quality Bar.

Pass the frozen revisions, workspace, change set, task owned-file lists, Requirements with their named evidence, Must Not Ship, Quality Bar, and Done commands as data. Each finder reads its own contract and inspects the frozen candidate without editing it.

A candidate finding carries an identifier, a claim, `file:line` on the frozen candidate, an admissibility source, and a concrete verify-by step. Admit it only when it cites one of:

- A Requirement whose named evidence is not met.
- A Must Not Ship entry present.
- A Quality Bar defect: a change outside owned files; work the contract did not ask for; a suppressed check, weakened or tautological test, dead code, or unhandled error; or a security or data-loss failure with a reachable precondition introduced by this change.

Everything else is an observation. Record it in the Decision Log or report with the reason it is not a defect. Even a verified observation creates no task, Requirement, milestone, or correction work. Cheapness, robustness preferences, and hypothetical future needs do not authorize work or a request for direction.

## Verifier

Dispatch the read-only `verifier` role with the absolute path to `skills/review/reviewers/verifier.md`. Pass every admissible candidate, its verify-by step, the frozen revisions, and the contract data. The verifier independently gathers fresh evidence and confirms or drops each candidate. A claim it cannot confirm, including one it cannot reproduce on the frozen revision, is dropped. Record the reason; do not make dropped claims correction work.

For checks needing writable scratch state, dispatch `test-runner` in an isolated workspace at the revision being checked and return its command, revision, and output to the verifier. Neither finder nor verifier writes files or performs corrections.

Freeze all confirmed findings into one ledger. Every entry retains its identifier, claim, contract citation, `file:line`, verify-by step, and confirming evidence. Record dropped claims separately. Ledger membership and claims are fixed; correction and closure may attach evidence and status but cannot add findings.

## Correction

Turn each confirmed ledger finding into a correction task citing its identifier and contract defect. Send these tasks through the build step in `skills/executing-plans/SKILL.md`, Loop step 3. Start each worker on the entry rung in an isolated workspace based on the frozen candidate, under `contracts/worker.md` and a complete brief with exact owned files and the named check. Only workers edit; only the orchestrator gates and commits their accepted changes.

For each return, write the binary gate record with its contract-item evidence, owned-files and mechanical-floor results, Premises touched, lineage, rung, candidate revision, verdict, and next action. Route each NOT DONE by the build step's rules: a second attempt on the same rung only for a named exact fix, a split for a task too large, escalation otherwise, one final attempt by the orchestrator after the top rung, then a gap. Keep exhausted work on its gap branch, outside the candidate, and continue independent tasks. After each correction effort, run Closure against the resulting candidate. Continue correction until each finding's lineage is DONE or exhausted as a review gap. If the ledger is empty, create no correction tasks.

## Closure

After each correction effort, dispatch the verifier with the same contract path, the frozen ledger, and the resulting candidate revision. Re-check only the ledger's findings against that candidate. Do not dispatch finders again or broaden discovery to newly noticed issues.

For every identifier, attach fresh closure evidence. Close it only when the original defect is proven resolved. A finding that remains confirmed, or whose resolution cannot be established, stays open for another correction effort while its lineage can continue. If its lineage is exhausted while it remains open, record it as a **review gap**. Preserve its original contract citation and location, the closure result, correction task and gate evidence, and any gap branch.

Then run the full Done gate fresh on that exact candidate, even if entry checks were green or the ledger is empty. Record the commands and output. Failed or unavailable Done evidence prevents a clean result and is recorded as a review gap. Continue Correction only for findings whose lineage can continue; otherwise retain the review gap. Record additional observations without expanding the ledger.

## Return

Return the frozen and corrected revisions, ledger with closure evidence, fresh Done results, decisions and observations, and any review gaps to the calling orchestrator.

Return **clean** only when the required review completed, every ledger finding is closed, and the fresh full Done gate is green. Otherwise return the review gaps and the reason nothing can be released. A finding still open after its lineage is exhausted is a **review gap**; the orchestrator records the report and ends the run with the terminal outcome **ended with gaps**.

Review never releases, performs Release actions, opens a pull request, or hands off to any integration or finishing step. Returning evidence to its caller is its final action. No result becomes a question to a person.
