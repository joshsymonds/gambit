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

Read `contracts/models.md`. Resolve each role through its registry, starting at the role's entry model profile and selecting its read-only variant for `conformance-reviewer`, `integration-reviewer`, and `finding-verifier`. Pass role contracts by absolute path from the current installation. An unresolved role is recorded in the Decision Log; work requiring it becomes a gap, while independent executable work continues. Do not substitute a dispatch target.

## Final review

Dispatch these two read-only roles concurrently, each with its contract by absolute path:

- The `conformance-reviewer` role under `skills/review/reviewers/conformance-reviewer.md` checks Requirements, Must Not Ship, owned files, minimal change, cross-document consistency, and named workload evidence.
- The `integration-reviewer` role under `skills/review/reviewers/integration-reviewer.md` checks cross-task interfaces, ordering, shared surfaces, and introduced security, data-loss, and resource failures.

Pass the frozen revisions, workspace, complete change set, task briefs and owned-file lists, task-review evidence, Requirements with their named evidence, Must Not Ship, Quality Bar, and Done commands as data. Both reviewers inspect the final candidate and surrounding code without editing it. Task review does not replace either final pass.

A candidate finding carries an identifier, a claim, `file:line` on the frozen candidate, an admissibility source, and a concrete verify-by step. Admit it only when it cites one of:

- A Requirement whose named evidence is not met.
- A Must Not Ship entry present.
- A Quality Bar defect: a change outside owned files; work the contract did not ask for; a suppressed check, weakened or tautological test, dead code, or unhandled error; or a security or data-loss failure with a reachable precondition introduced by this change.

Everything else is an observation. Record it in the Decision Log or report with the reason it is not a defect. Even a verified observation creates no task, Requirement, milestone, or correction work. Cheapness, robustness preferences, and hypothetical future needs do not authorize work or a request for direction.

## Finding verification

Dispatch one read-only `finding-verifier` per admissible candidate under `skills/review/reviewers/finding-verifier.md`. Pass that candidate, its verify-by step, the frozen revisions, and the contract data. The finding verifier independently gathers fresh evidence and confirms or drops the candidate. A claim it cannot confirm, including one it cannot reproduce on the frozen revision, is dropped. Record the reason; do not make dropped claims correction work.

For checks needing writable scratch state, dispatch `test-runner` in an isolated workspace at the revision being checked and return its command, revision, and output to the verifier. Neither reviewers nor finding verifiers write files or perform corrections.

Freeze all confirmed findings into one ledger. Every entry retains its identifier, claim, contract citation, `file:line`, verify-by step, and confirming evidence. Record dropped claims separately. Ledger membership and claims are fixed; correction and closure may attach evidence and status but cannot add findings.

## Correction

Turn each confirmed ledger finding into a correction task citing its identifier and contract defect. Send these tasks through the build step in `skills/executing-plans/SKILL.md`, Loop step 3. Start each implementer on the entry model profile in an isolated workspace based on the frozen candidate, under `contracts/implementer.md` and a complete brief with exact owned files and the named check. Only implementers edit; only the orchestrator gates and commits their accepted changes.

For each return, write the binary gate record with its contract-item evidence, owned-files and mechanical-floor results, Premises touched, lineage, model profile, candidate revision, verdict, and next action. Route each NOT DONE through the build step's failure signature routing in `skills/executing-plans/SKILL.md`, Loop step 3. Keep exhausted work on its gap branch, outside the candidate, and continue independent tasks. After each correction effort, run Closure against the resulting candidate. Continue correction until each finding's lineage is DONE or exhausted as a review gap. If the ledger is empty, create no correction tasks.

## Closure

After each correction effort, dispatch a `finding-verifier` per ledger finding with the same contract path, its frozen ledger entry, and the resulting candidate revision. Re-check only that finding against the candidate. Do not dispatch final reviewers again or broaden discovery to newly noticed issues.

For every identifier, attach fresh closure evidence. Close it only when the original defect is proven resolved. A finding that remains confirmed, or whose resolution cannot be established, stays open for another correction effort while its lineage can continue. If its lineage is exhausted while it remains open, record it as a **review gap**. Preserve its original contract citation and location, the closure result, correction task and gate evidence, and any gap branch.

Then run the full Done gate fresh on that exact candidate, even if entry checks were green or the ledger is empty. Record the commands and output. Failed or unavailable Done evidence prevents a clean result and is recorded as a review gap. Continue Correction only for findings whose lineage can continue; otherwise retain the review gap. Record additional observations without expanding the ledger.

## Return

Return the frozen and corrected revisions, ledger with closure evidence, fresh Done results, decisions and observations, and any review gaps to the calling orchestrator.

Return **clean** only when the required review completed, every ledger finding is closed, and the fresh full Done gate is green. Otherwise return the review gaps and the reason nothing can be released. A finding still open after its lineage is exhausted is a **review gap**; the orchestrator records the report and ends the run with the terminal outcome **ended with gaps**.

Review never releases, performs Release actions, opens a pull request, or hands off to any integration or finishing step. Returning evidence to its caller is its final action. No result becomes a question to a person.
