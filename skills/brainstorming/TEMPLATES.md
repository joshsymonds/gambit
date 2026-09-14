# Epic and task templates

Use the record-task-state operation. Fill every field from the goal, decisions, and research before creating executable work. The epic body contains exactly the eight sections below. Its Decision Log is attached record context, outside that body. The Design Ledger stays in the design transcript. The epic body, its Decision Log, and the task state are also written to the epic's record directory as `skills/executing-plans/references/record.md` specifies.

### Epic record

```markdown
## Intent
[One paragraph stating the desired end state and why it is wanted, without prescribing a solution.]

## Premises
- P1: [Falsifiable fact, with evidence.] If false, the Intent [survives with the stated design consequence / cannot survive, for this reason].

## Requirements
- R1: [Atomic, testable outcome or explicit constraint.] Evidence: [named test or observable result and exact command that establishes it].

## Must Not Ship
- [Forbidden outcome or non-goal.] Reason: [why it must be excluded].

## Quality Bar
Failing, low-quality, or bad code is unacceptable, but failure to meet a mythic platonic ideal of code or cover literally every imaginable edge case is NOT itself a defect. This bar is FIXED for every epic; write it verbatim — never elicit it, strengthen it, or make it a per-project preference. A defect is exactly one of: a Requirement's named evidence not met; a Must Not Ship entry present; a change outside the task's owned files; a change the contract did not ask for; a violation of the worker contract's mechanical floor (a suppressed check, a weakened or tautological test, dead code, an unhandled error); or a security or data-loss failure with a reachable precondition that the change itself introduces. Everything else the orchestrator or a reviewer notices is an observation — it may be recorded in the Decision Log and the report; it never becomes work during the run. The craftsmanship asked of the worker is one line: simple, foundational, secure; match the surrounding code.

## Approach and Rejected Approaches
Chosen: [Shape, interfaces, data flow, and reason, grounded in cited research.]
Rejected: [Alternative and reason.] Reconsider only if [specific condition changes that reason].

## Done
- Task fast check: [exact command, including required setup and working directory].
- Integrated candidate full gate: [exact commands in order, including required setup].

## Release
1. Action: [exact action]. Target: [exact repository, branch, service, or destination]. Intended effect: [observable result].
2. [Next action with its target and effect, if needed.]
Postconditions: [observable facts and checks that must all hold before reporting release].
```

Acceptance freezes Intent, Premises and their survival clauses, and Requirements. Keep subsequent assessments in the Decision Log without rewriting the frozen text. Each log entry states the decision or assumption, its reason and evidence, and any affected finding or contract identifier.

### Task brief

Supply the task's workspace, base revision, and applicable contract clauses alongside this body. Keep Goal plus Acceptance plus Constraints under 250 words total. This brief carries no implementation steps, code, or diffs. Create only work grounded in the tree now.

```markdown
## Goal
[One concrete result required by the contract.]

## Files owned
- [Exact repository-relative path, including each addition or deletion. No globs or directory allowlists.]

## Hidden shared surfaces
[Lockfiles, generated indexes, registries, snapshots, and other implicit writes checked. State None when absent. These grant no ownership; every intended edit also belongs in Files owned.]

## Neighbors
[Every concurrent task and its complete owned-file list, all off-limits. State None for a single task.]

## Anchors
[Verified source and test anchors at the base revision, written as path:symbol:line.]

## Acceptance
[Name an existing test or reproduction with its expected result, or state behavioral criteria for the failing test written first.]

## Constraints
[State the applicable contract, scope, and safety limits.]

## Requirements covered
- R1: [Requirement text and its named satisfying evidence.]

## Test command
Test command: [exact task fast check from Done].
```

### Effort brief

The Director writes one effort brief per effort. Objective plus Interfaces plus Binding contract stay under 250 words excluding lists.

```markdown
## Objective
[Quote each covered Requirement with its named evidence.]

## Partition
[List owned files and name concurrent efforts' files as off-limits.]

## Interfaces
[List interfaces published or consumed, in their order.]

## Binding contract
[List applicable Must Not Ship entries, Premise clauses, the Quality Bar, and Decision Log entries touching these files.]

## Base
[Give the accepted base, branch `effort/<epic-slug>-<n>`, and check commands.]

## Report shape
[Cap the report at 400 words.]
```

Tasks are pending executable children of the epic, never blocked by it. Owned-file lists are disjoint within the effort. Leave tasks requiring unfinished interfaces for execution to author when those interfaces exist.
