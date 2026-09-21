---
name: brainstorming
description: Turns an idea, bug report, or goal file into an epic contract and its first executable effort.
when_to_use: Use when defining work from a new idea, investigating a bug before planning its fix, or starting from a goal file. Not for executing an existing epic contract.
user_invokable: true
---

# Brainstorming

Own the contract stage. Read `README.md` in full as the design authority. Research, resolve the design, and create the contract before implementation. Use the harness's operations to dispatch roles, record task state, and load stages, rather than naming its tools.

Give a complete, ordered answer before optional elaboration. A request to describe what you produce and do calls for a worked scenario, not live execution. Mark that frame once, complete the research within the scenario, and show its concrete findings, then the full contract and ready briefs, all forming one consistent repository scenario that respects every supplied fact. Do not substitute a live-tools disclaimer, promises of later research, or empty section names for the requested records. Described dispatches and acceptance are events in the scenario, not claims that live actions occurred. Summarize dispatch inputs and print the contract and briefs once.

## Inputs

Begin with the person's idea, bug report, or the complete goal file. Preserve the requested scope. Establish the desired end state and why it matters before choosing mechanisms.

In conversation, the person resolves contract-stage choices and accepts the contract. With a goal file, the orchestrator stands in for the person throughout this stage: answer every question from the goal and research, choose a scope-preserving answer wherever evidence leaves a choice, and record each assumption with its reason in the Decision Log. Treat every Premise, every fact resolved after a `NOT FOUND`, and every substitute for missing research as an assumption with its own Decision Log entry and reason, and cite that entry by id beside the Premise. Never ask a person, wait for input, or leave an unresolved question for someone to answer. Accept the completed contract on the goal file's behalf and continue automatically.

Collect decisions and their reasons for the epic's attached Decision Log. Keep it outside the contract's body. When a decision concerns a steelman finding, name the finding ID in the log entry.

## Research

Read `contracts/models.md`. Resolve each role through its registry, starting at the role's entry model profile and selecting the read-only variant for read-only roles. Pass the role's contract by absolute path and its complete brief as text through the dispatch operation. Resolve paths from the installed tree. Follow the registry contract when a role cannot be resolved; never invent a dispatch target.

Dispatch a read-only `scout` under `contracts/scout.md` with the repository root and bounded questions. Establish existing implementation patterns, interfaces, tests, contribution commands, release conventions, constraints, and scale. Require `file:line` evidence or `NOT FOUND`, with coverage limitations. Inspect enough to choose between approaches, not merely list them. Research supplies facts; it cannot add requirements.

For a bug, make this evidence chain explicit and complete:

1. Give the scout the report and observed failure as clues to verify. Have it return the exact reproduction command as a command line and trace the root cause with causal `file:line` evidence, including what would falsify that cause. A suspected file or stack frame is not a verified diagnosis.
2. If reproduction writes build artifacts, fixtures, a cache, or other state, dispatch `test-runner` with the exact command in an isolated workspace. It writes scratch state only and returns the command and output. The scout does not execute writable reproduction.
3. Reconcile that output with the scout's causal evidence. Turn the verified root cause into a falsifiable Premise with its explicit Intent-survival clause.
4. Make the verified reproduction the first task's failing test. Name that same reproduction and its expected corrected result as a Requirement's satisfying evidence, with the exact check. Carry the observed failure into the brief so the implementer begins from RED.

This is research for a fix, not the fix itself. Do not patch the bug, write implementation, or hand the investigation to another stage.

## Questions in prose

Only in conversation, ask two to four questions per round. Each carries context, realistic options, and a recommendation with its reason. Use ordinary prose for every question. Stop questioning when scope, constraints, existing patterns, and scale are understood.

Before comparing approaches, ask two things in the person's own terms. The use cases: who does what with the result. The failure cases: what could go wrong that they would mind, and how bad each would be, rated limited, serious, or severe as `TEMPLATES.md` defines them. These answers fill the failure table and set the level of care; a stake you inferred rather than heard is an assumption and is written as one. Never ask how many efforts to admit: execution runs until the work ships or every lineage is exhausted.

In a goal-file run, perform the same inquiry yourself from the goal text and research. Record each answer, its support, and any assumption with its reason in the Decision Log. Resolve uncertainty by a choice that preserves the goal, never by a request for input.

## Approaches and design

Compare two or three credible approaches. Recommend one using the research and Intent. Record why each alternative loses and when to reconsider it.

Present the design in digestible sections covering the relevant components, interfaces, data flow, errors, and tests. In conversation, settle the design with the person. For a goal file, settle it from the goal and research and log the decisions.

Decompose for isolation: each unit has a clear purpose, known interfaces, and independently testable behavior. Cut features, abstractions, and hardening the Requirements do not demand. Chosen mechanisms belong in Approach unless the request explicitly requires them. Never add a Requirement to justify a preferred task.

Proportionality failure is a contract-drafting failure: overdesign, excess robustness, nitpicking, or added features without material benefit to the requested product. Ground the standard of care in the user's stated audience, stakes, scale, and constraints, carried into Intent. The level of care is the worst rating in the failure table, and a rating authorizes no work by itself: each row's What we do is the only work it adds. Apply this before drafting and when adopting steelman findings. Preserve explicit requirements and the fixed Quality Bar.

## Steelman

Run exactly one discovery pass on the agreed design, before accepting the contract or creating its executable tasks. Read `contracts/steelman.md`. Dispatch the `steelman` role fresh and read-only under that contract, resolved through `contracts/models.md`.

Supply the draft document as the Design Packet, using the receiver contract's exact fields, in order: What you asked for; What could go wrong, and how much we care; Things you did not ask for; What will be true when done; What I'm assuming; What we won't do; How, and why not the other ways; What leaves this machine or can't be undone; Decisions I need from you; Checks the machines run. Include each field's required evidence, ratings, survival clauses, reasons, commands, actions, and postconditions. Write `None` for genuinely absent decisions. Discovery receives this packet without prior steelman output.

Read its status and every finding. Freeze a transcript-local Design Ledger retaining every finding ID with exactly one disposition: `ADOPTED`, `REJECTED` with a reason, `OPEN`, or `DEFERRED` with a boundary. It is design context, never task state or an independent source of Requirements. Reflect the findings to the person present in conversation. Record every decision, reason, and affected finding ID in the Decision Log, including a choice already made but not yet written down. No finding stays `OPEN` in a goal-file run: decide each Design Ledger finding and record its reason in the Decision Log. Before acceptance, show the steelman's returned status and every finding; never assert it as done without that result. Incorporate adopted conclusions into the packet without expanding scope.

Use at most one closure pass to check revisions. Its only inputs are the revised self-contained packet, the frozen ledger verbatim, and a concise delta. Closure checks adopted and open findings and concerns introduced by the delta. Rejected and deferred findings stay closed.

After a non-`READY` closure, finish by revising the packet without another steelman call or locking the contract with the residual explicitly recorded as accepted risk. Prefer the named scope-preserving correction when it resolves the residual. Log the chosen outcome and continue; neither outcome waits. The bound is one discovery and at most one closure, including resumed work; it cannot be extended or started over.

## The contract

Create the epic record through the record-task-state operation from the finalized design and decisions. Read `TEMPLATES.md` and `skills/executing-plans/references/record.md`. Emit the full contract: the decision line, then exactly these sections in this order:

1. **What you asked for:** the Intent: one to three plain sentences stating the desired end state and reason, in the person's terms, never a solution.
2. **What could go wrong, and how much we care:** the failure table: each row an F id, a failure in the past tense, its rating, and its What we do; below it, the level of care and the row that set it.
3. **Things you did not ask for:** every Requirement, mechanism, check, or release step that traces to no sentence of the person's, with why and its cost.
4. **What will be true when done:** the Requirements, immutable, atomic, and testable. Every row names the specific evidence and check that satisfies it.
5. **What I'm assuming:** the Premises, falsifiable facts with evidence. Every If-wrong cell states whether the Intent survives and the consequence; in a goal-file run, every row also cites its Decision Log entry by id.
6. **What we won't do:** the Must Not Ship entries, forbidden outcomes and non-goals, each with its reason.
7. **How, and why not the other ways:** the chosen shape and reason in one paragraph, then each alternative with why it loses and the condition for reconsidering it.
8. **What leaves this machine or can't be undone:** exact ordered steps, each naming the action and its intended effect, its target, and how to undo it, with `none` where it cannot be undone; then the postconditions required before reporting release.
9. **Decisions I need from you:** every open choice with options and a recommendation, or `None`.
10. **Checks the machines run:** the exact commands for each task's fast check and the integrated candidate's full gate, the evidence named above, and the complete Quality Bar paragraph from README verbatim on one line starting `Quality Bar:`. Output the paragraph itself, not a summary, reference, or promise to copy it. Never customize it.

In live execution, bind evidence links, file paths, commands, and release targets from inspected evidence before task creation. Do not present guesses as verified facts: an assumption can settle an open design choice, but cannot establish that an invented file exists. In a worked scenario, use its research findings. In both cases, show finished records, not section names or promises to populate them.

In conversation, present the complete document for acceptance and settle requested changes here. With a goal file, first check that every assumption the research produced, including each fact resolved after a `NOT FOUND` and each question you answered yourself, has its Decision Log entry, and log any missing one; then accept the contract yourself on that file's behalf. Record acceptance and freeze Intent, Premises with their survival clauses, and Requirements. Later changes of assessment belong in the Decision Log, leaving those clauses intact. The contract alone authorizes the work that follows.

At acceptance, also write the epic's record directory `~/.gambit/<repository-id>/<epic-slug>/` as `skills/executing-plans/references/record.md` specifies: the frozen document to `epic.md`, every Decision Log entry to `decisions.md` in its append-only line format, and the head to `state.json`, carrying `efforts_admitted` at zero. Derive repository-id from the tree by that reference's rule, never from a workspace name. The record carries this epic for a reader holding no transcript.

## The document

The contract is one document the person reads in a sitting, in the order they need it. The decision line comes first: what is approved, the level of care, and how many decisions are still open. Write every section in plain language for the person, not the implementer: one idea per sentence, no term a reader outside the repository would need explained, tables where rows compare.

Rate each failure row before any mitigation is chosen, as the person would experience it. Limited means they recover in minutes and lose nothing but time. Serious means recovery takes real effort or money, or someone else is affected. Severe means the loss cannot be undone, harms someone else, or exposes a secret or a system. The worst row sets the level of care; a rating authorizes no work, and each row's What we do, starting prevent, reduce, recover, or accept, is the only work the row adds. The table has no likelihood column, and the level-of-care line carries no effort ceiling: execution admits efforts until the work ships or every lineage is exhausted, so the contract never rations them.

Trace every Requirement, mechanism, check, and release step to a sentence of the person's request or goal file. Whatever traces to nothing goes in "Things you did not ask for" with its reason and cost: new files, infrastructure (a machine, service, harness, script, or corpus), external systems touched, and check runtime. In conversation, the person decides each row individually before accepting, and each decision is a Decision Log entry; striking a row removes it with the evidence and commands that depended on it. With a goal file, decide each row yourself from the goal and research, log each decision with its reason, and continue. An empty table means nothing was added. Execution treats infrastructure outside the accepted approach and these rows as unauthorized.

Each release step names its action and its effect in one cell, and its Undo may say none; a step with no undo is the irreversible action the catastrophe rule watches. "Decisions I need from you" holds every open choice before acceptance and reads `None` after it.

The content above "Checks the machines run" fits forty lines when wrapped at 100 columns, counting table rows and prose only; headings, header rows, rule rows, and blank lines do not count. An epic that overflows is split into two epics that together keep the full scope; never trim a Requirement or a failure row to fit.

## The first effort

Create every task writable from the tree now for the first effort, with complete briefs. Cover each unmet Requirement that has executable work now; leave work needing unfinished interfaces for later decomposition. Never produce a full future task tree or split one behavior just to create parallel work.

Use the task template's fields in order: Goal, Files owned, Hidden shared surfaces, Neighbors, Anchors, Acceptance, Constraints, Requirements covered, Test command. Supply the workspace, base revision, applicable contract clauses, verified `path:symbol:line` anchors, and the acceptance condition (an existing test or reproduction with its expected result, or the behavioral criteria for the failing test the implementer writes first). Keep Goal plus Acceptance plus Constraints under 250 words total. Constraints carries the level of care with the row that set it and each applicable failure row quoted with its What we do, so no implementer receives an id without its text. This brief carries no implementation steps, code, or diffs. Each brief must be executable without conversation history or questions.

Give every concurrent task a disjoint exact owned-file list, including tests, additions, deletions, and implicit writes. Hidden shared surfaces and neighbors grant no ownership. Put work with overlapping files into one coherent task or leave it for a later effort. For bugs, the first brief carries the verified reproduction as its failing test and maps it to the Requirement's evidence.

Record tasks as pending and ready, associated with the epic as their contract container, never as a blocker that must complete first. State the task state left behind and keep the Decision Log attached to the epic.

Write that same task state into the record's `state.json` before handing off: each task's id, slug, subject, requirement, owned_files, lineage, profile, attempts, status, and gate_paths, with `next_actions` naming what the next reader does first and `never_drop` carrying the acceptance criteria, observed error signatures, and commands still needed.

## Handoff

After acceptance and first-effort creation, load `skills/executing-plans/SKILL.md` by reading it and following it. Carry the accepted epic, Decision Log, and ready task briefs. Execution follows the same contract regardless of its source.

The person in conversation may choose to stop at the contract instead; settle that here. A goal-file run always hands off automatically, with no closing question or wait. When describing the stage without implementing, show this as the next load-a-stage operation and leave the described first effort ready.
