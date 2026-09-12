---
name: brainstorming
description: Turns an idea, bug report, or goal file into an epic contract and its first executable effort.
when_to_use: Use when defining work from a new idea, investigating a bug before planning its fix, or starting from a goal file. Not for executing an existing epic contract.
user_invokable: true
---

# Brainstorming

Own the contract stage. Read `README.md` in full as the design authority. Research, resolve the design, and create the contract before implementation. Use the harness's operations to dispatch roles, record task state, and load stages, rather than naming its tools.

Give a complete, ordered answer before optional elaboration. A request to describe what you produce and do calls for a worked scenario, not live execution. Mark that frame once, complete the research within the scenario, and show its concrete findings followed by the full contract and ready briefs. The research, file paths, commands, and tasks must form one consistent repository scenario and respect every supplied fact. Do not substitute a live-tools disclaimer, promises of later research, or empty section names for the requested records. Described dispatches and acceptance are events in the scenario, not claims that live actions occurred. Keep it concise: summarize dispatch inputs and print the contract and briefs once.

## Inputs

Begin with the person's idea, bug report, or the complete goal file. Preserve the requested scope. Establish the desired end state and why it matters before choosing mechanisms.

In conversation, the person resolves contract-stage choices and accepts the contract. With a goal file, the orchestrator stands in for the person throughout this stage: answer every question from the goal and research, choose a scope-preserving answer wherever evidence leaves a choice, and record each assumption with its reason in the Decision Log. Never ask a person, wait for input, or leave an unresolved question for someone to answer. Accept the completed contract on the goal file's behalf and continue automatically.

Collect decisions and their reasons for the epic's attached Decision Log. Keep it outside the contract's eight-section body. When a decision concerns a steelman finding, name the finding ID in the log entry.

## Research

Read `contracts/models.md`. Resolve each role through its registry, starting at the role's entry rung and selecting the read-only variant for read-only roles. Pass the role's contract by absolute path and its complete brief as text through the dispatch operation. Resolve paths from the installed tree. Follow the registry contract when a role cannot be resolved; never invent a dispatch target.

Dispatch a read-only `scout` under `contracts/scout.md` with the repository root and bounded questions. Establish existing implementation patterns, interfaces, tests, contribution commands, release conventions, constraints, and scale. Require `file:line` evidence or `NOT FOUND`, with coverage limitations. Inspect enough to choose between approaches, not merely list them. Research supplies facts; it cannot add requirements.

For a bug, make this evidence chain explicit and complete:

1. Give the scout the report and observed failure as clues to verify. Have it identify the exact reproduction command or smallest sequence and trace the root cause with causal `file:line` evidence, including what would falsify that cause. A suspected file or stack frame is not a verified diagnosis.
2. If reproduction writes build artifacts, fixtures, a cache, or other state, dispatch `test-runner` with the exact command in an isolated workspace. It writes scratch state only and returns the command and output. The scout does not execute writable reproduction.
3. Reconcile that output with the scout's causal evidence. Turn the verified root cause into a falsifiable Premise with its explicit Intent-survival clause.
4. Make the verified reproduction the first task's failing test. Name that same reproduction and its expected corrected result as a Requirement's satisfying evidence, with the exact check. Carry the observed failure into the brief so the worker begins from RED.

This is research for a fix, not the fix itself. Do not patch the bug, write implementation, or hand the investigation to another stage.

## Questions in prose

Only in conversation, ask two to four questions per round. Each carries context, realistic options, and a recommendation with its reason. Use ordinary prose for every question. Stop questioning when scope, constraints, existing patterns, and scale are understood.

In a goal-file run, perform the same inquiry yourself. Record the answer, its supporting goal text or research, and any assumption with its reason in the Decision Log. Resolve uncertainty by a choice that preserves the goal, not by creating a request for input.

## Approaches and design

Compare two or three credible approaches. Recommend one using the research and Intent. Record why each alternative loses and the specific condition under which it should be reconsidered.

Present the design in digestible sections covering the relevant components, interfaces, data flow, errors, and tests. In conversation, settle the design with the person. For a goal file, settle it from the goal and research and log the decisions.

Decompose for isolation: each unit has a clear purpose, known interfaces, and independently testable behavior. Cut features, abstractions, and hardening the Requirements do not demand. Chosen mechanisms belong in Approach unless the request explicitly requires them. Never add a Requirement to justify a preferred task.

## Steelman

Run exactly one discovery pass on the agreed design, before accepting the contract or creating its executable tasks. Read `contracts/steelman.md`. Dispatch the `steelman` role fresh and read-only under that contract, resolved through `contracts/models.md`.

Supply a self-contained Design Packet using the receiver contract's exact fields, in order: Intent; Premises; Requirements; Must Not Ship; Approach and Rejected Approaches; Done; Release; Unresolved decisions. Include each field's required evidence, survival clauses, reasons, commands, actions, and postconditions. Write `None` for genuinely absent unresolved decisions. The fixed Quality Bar goes in the epic contract; it is not an additional packet field. Discovery receives this packet without prior steelman output.

Read its status and every finding. Freeze a transcript-local Design Ledger retaining every finding ID with exactly one disposition: `ADOPTED`, `REJECTED` with a reason, `OPEN`, or `DEFERRED` with a boundary. It is design context, never task state or an independent source of Requirements. Reflect the findings to the person present in conversation. In a goal-file run, decide every named choice yourself from the goal and research. Record every decision, reason, and affected finding ID in the Decision Log, including a choice already made but not yet written down. Incorporate adopted conclusions into the packet without expanding scope.

Use at most one closure pass to check revisions. Its only inputs are the revised self-contained packet, the frozen ledger verbatim, and a concise delta. Closure checks adopted and open findings and concerns introduced by the delta. Rejected and deferred findings stay closed.

After a non-`READY` closure, finish by revising the packet without another steelman call or locking the contract with the residual explicitly recorded as accepted risk. Prefer the named scope-preserving correction when it resolves the residual. Log the chosen outcome and continue; neither outcome waits. In a goal-file run, the orchestrator makes this choice itself. The bound is one discovery and at most one closure for the design, including resumed work. It cannot be extended or started over.

## The contract

Create the epic record through the record-task-state operation from the finalized design and decisions. Read `TEMPLATES.md` and `skills/executing-plans/references/record.md`. Emit the full contract, with exactly these sections in this order:

1. **Intent:** one paragraph stating the desired end state and reason, never a solution.
2. **Premises:** falsifiable facts. Every one states whether the Intent survives if false and the consequence of that clause.
3. **Requirements:** immutable, atomic, testable outcomes. Every one names the specific evidence and check that satisfies it.
4. **Must Not Ship:** forbidden outcomes and non-goals, each with its reason.
5. **Quality Bar:** copy the complete paragraph from README verbatim. Output the paragraph itself, not a summary, reference, or promise to copy it. Never customize it.
6. **Approach and Rejected Approaches:** chosen shape and reason, with each rejected alternative's reason and reconsideration condition.
7. **Done:** exact commands for each task's fast check and the integrated candidate's full gate, including required setup.
8. **Release:** exact ordered actions, each naming its target and intended effect, followed by the observable postconditions required before reporting release.

In live execution, bind evidence links, file paths, commands, and release targets from inspected evidence before task creation. Do not present guesses as verified facts: an assumption can settle an open design choice, but cannot establish that an invented file exists. In a worked scenario, use the findings established by its research. In both cases, show finished records, not section names or promises to populate them.

In conversation, present the complete contract for acceptance and settle requested changes here. With a goal file, accept it yourself on that file's behalf. Record acceptance and freeze Intent, Premises with their survival clauses, and Requirements. Later changes of assessment belong in the Decision Log, leaving those clauses intact. The contract alone authorizes the work that follows.

At acceptance, and in addition to the record-task-state operation, write the epic's record directory `~/.gambit/<repository-id>/<epic-slug>/` as `skills/executing-plans/references/record.md` specifies: the frozen eight-section contract to `epic.md`, every Decision Log entry to `decisions.md` in its append-only line format, and the head to `state.json`. Derive repository-id from the tree by that reference's rule, never from a workspace name. The record carries this epic for a reader holding no transcript.

## The first effort

Create every task writable from the tree now for the first effort, with complete briefs. Cover each unmet Requirement that has executable work now; leave work needing unfinished interfaces for later decomposition. Never produce a full future task tree or split one behavior just to create parallel work.

Use the task template's fields in order: Goal, Files owned, Hidden shared surfaces, Neighbors, Implementation, Requirements covered, Test command. Supply the workspace, base revision, applicable contract clauses, verified `file:line` anchors, test-first instructions, and exact task check from Done. Each brief must be executable without conversation history or questions.

Give every concurrent task a disjoint exact owned-file list, including tests, additions, deletions, and implicit writes. Hidden shared surfaces and neighbors grant no ownership. Put work with overlapping files into one coherent task or leave it for a later effort. For bugs, the first brief carries the verified reproduction as its failing test and maps it to the Requirement's evidence.

Record tasks as pending and ready. Associate them with the epic without making the epic a blocker: it is their contract container, not a prerequisite that must complete first. State the task state left behind and keep the Decision Log attached to the epic.

Write that same task state into the record's `state.json` before handing off: each task's id, slug, subject, requirement, owned_files, lineage, rung, attempts, status, and gate_paths, with `next_actions` naming what the next reader does first and `never_drop` carrying the acceptance criteria, observed error signatures, and commands still needed.

## Handoff

After acceptance and first-effort creation, load `skills/executing-plans/SKILL.md` by reading it and following it. Carry the accepted epic, Decision Log, and ready task briefs. Execution follows the same contract regardless of its source.

The person in conversation may choose to stop at the contract instead; settle that choice during this conversational stage. A goal-file run always hands off automatically, with no closing question or wait. When describing the stage without implementing, show this as the next load-a-stage operation and leave the described first effort ready.
