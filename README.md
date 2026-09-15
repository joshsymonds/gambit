# Gambit

One copy of text that takes a contract to a released result.

## Purpose

Gambit is a contract-to-release loop for coding agents. A person or a goal file supplies an idea. Gambit turns it into a contract, builds it, reviews it once, releases it, and reports. An orchestrator model runs the loop on a harness that provides five operations: dispatch a role, record task state, load a stage, isolate a workspace, end a run. Claude Code and Pi both provide them.

The loop exists to deliver autonomously, cheaply, and convergently. Autonomously: between the contract and the report nobody is asked anything. Cheaply: the fastest capable model does the work, and a stronger one is used only when evidence shows the cheaper one cannot. Convergently: done is a binary judgment against the contract, so work stops when the contract is satisfied and never grows past it.

A person is present at exactly three moments: writing the contract, reading the report, and a catastrophe. Everything else the orchestrator decides and records.

## Principles

1. **The contract is the only input.** Every task, gate, review, and release action traces to a line in the contract. Nothing else authorizes work.
2. **Done is binary and judged only against the contract.** A task is DONE or NOT DONE, itemized against the Requirements, Must Not Ship, owned files, the mechanical floor, and minimal change. There is no score, no "mostly", and no opinion of what would be better.
3. **Cheapest capable model first.** Work starts on its role's entry rung, and routing between attempts is by failure signature: same-thread continuation with the failing output, a re-brief when the brief was wrong, a split when behaviors are separable, then the orchestrator's own attempt, then a gap, never a stronger model.
4. **Minimal change.** Nothing the contract did not ask for. A change the contract did not ask for is a defect, and so is hardening against a failure mode it does not name. The one exception is the mechanical floor of the change itself: an error, security, or data-loss path that the change opens is the worker's to close.
5. **No human mid-run except catastrophe.** The loop never asks for approval, confirmation, or direction between the contract and the report.
6. **Record, don't ask.** A decision, a compromise, a changed assessment, or a gap goes to the Decision Log and the report. It never becomes a question.
7. **One process.** A contract written in conversation and a contract written from a goal file enter the same loop. The loop never learns which.
8. **Read-only roles never write.** Scout, steelman, finder, and verifier inspect and report. Only a worker changes the tree — the orchestrator only for its own final attempt when routing reaches it — and only the orchestrator commits.
9. **One text, five operations, any harness.** Skills name operations, never a harness's tool. A harness that lacks an operation is fixed outside gambit.

## The Contract

The contract is the epic record, eight sections. Everything after it is measured against it.

- **Intent.** One paragraph: the desired end state and the reason it is wanted. Never a solution. *"Users can sign in with a passkey, because password resets are a third of support load."*
- **Premises.** The facts the Intent depends on. Each is falsifiable and says whether the Intent survives if it is false. Both are frozen at acceptance; a changed assessment goes to the Decision Log. *"P1: the auth service owns session issuance. If false, the Intent survives; the design changes."*
- **Requirements.** Immutable, atomic, testable. Each names the evidence that satisfies it. *"R1: a registered passkey signs in without a password. Evidence: `test_passkey_login` green."*
- **Must Not Ship.** Anti-patterns and non-goals, each with its reason. *"No password fallback on the passkey path (reason: it reopens the reset load)."*
- **Quality Bar.** The fixed defect definition below.
- **Approach and Rejected Approaches.** The chosen shape, and each rejected alternative with the condition for revisiting it.
- **Done.** The exact commands whose green output means done: a task's fast check and the integrated candidate's full gate.
- **Release.** The exact actions in order, each naming its target and intended effect, and the postconditions that must hold before release is reported; from *open a pull request* to *tag, publish, deploy*.

The Quality Bar, verbatim in every contract:

> Failing, low-quality, or bad code is unacceptable, but failure to meet a mythic platonic ideal of code or cover literally every imaginable edge case is NOT itself a defect. This bar is FIXED for every epic; write it verbatim — never elicit it, strengthen it, or make it a per-project preference. A defect is exactly one of: a Requirement's named evidence not met; a Must Not Ship entry present; a change outside the task's owned files; a change the contract did not ask for; a violation of the worker contract's mechanical floor (a suppressed check, a weakened or tautological test, dead code, an unhandled error); or a security or data-loss failure with a reachable precondition that the change itself introduces. Everything else the orchestrator or a reviewer notices is an observation — it may be recorded in the Decision Log and the report; it never becomes work during the run. The craftsmanship asked of the worker is one line: simple, foundational, secure; match the surrounding code.

## The Loop

1. **Contract.** `brainstorming` turns the idea into the epic record: research, questions in prose, approaches, a design, one steelman discovery pass and at most one closure, then the contract and the first effort. The only conversational stage.
2. **Decompose the next effort.** The Director partitions the accepted Requirements into dependency-cohesive efforts with ownership exclusive among concurrent efforts, dispatches each to a fresh orchestrator on its own branch, and merges finished efforts in completion order before one full gate. The orchestrator of an effort creates every task writable now, one behavior each, with disjoint owned-file lists. Never a full tree.
3. **Build each task until good.** A worker on the entry rung works in an isolated workspace under the worker contract and a brief. Routing between attempts is by failure signature: same-thread continuation with the failing output, a re-brief when the brief was wrong, a split when behaviors are separable, then the orchestrator's own attempt, then a gap, never a stronger model. The orchestrator writes the gate record, binary and itemized against the contract, noting any Premise the work bears on; a false Premise triggers its clause. When the orchestrator's own attempt fails, the lineage is a **gap**: its work is not integrated; everything not depending on it continues.
4. **Integrate and repeat.** The full Done gate runs on the combined candidate. A failure found only after combination is a NOT DONE record owned by the contributing lineage, or by one integration lineage per effort, under the same rules; the rejected candidate stays on `candidate/<effort>` over the last accepted base. Repeat from step 2 until every Requirement is DONE or a gap; when no executable work remains, a Requirement depending on a gap becomes one citing it.
5. **Review once.** `review` inspects one frozen candidate, corrects confirmed findings until closure passes, and never releases.
6. **Release.** Only when every Requirement is DONE and review is clean. The actions run in order, each recorded when complete; one that fails or cannot be confirmed stops the sequence as a release gap. Reported only when every postcondition holds.
7. **Report.** Always: what was released or why not, every decision with its reason, changed premise assessments, gaps and their `gap/<task-slug>` branches, completed external actions, rungs used.

A run ends in one terminal outcome: **released**, **ended with gaps**, or **stopped on catastrophe**. Resuming a terminal run only shows the report.

Artifacts: the epic record with its Decision Log, briefs, gate records, the branches above.

## Human Boundaries

**Start.** A person, or a goal file standing in for one, is present for `brainstorming`: the questions, the design, the steelman findings, and the contract. When the contract is accepted the conversation ends. With a goal file, `brainstorming` answers its own questions from the goal and its research, records each assumption in the Decision Log, never asks or waits, and accepts the contract itself.

**End.** A person reads the report. Decisions, compromises, gaps, and completed release actions are all there, with reasons. If the outcome is *ended with gaps*, the person decides what the gaps mean; the loop does not.

**Catastrophe.** The orchestrator stops the run, writes the report, and names one of two conditions:

- a Premise is false and its clause says the Intent cannot survive; or
- the next action is an irreversible external action that the Release section does not explicitly authorize by action, target, and intended effect.

No other external action the contract does not name is taken either: a task that needs one is NOT DONE and becomes a gap. Only the irreversible case stops the run.

Everything else needs no approval: repairs, approach changes within the Approach, scope-preserving decomposition, routing between attempts, validation runs, recording a gap, a worker's BLOCKED or NEEDS_CONTEXT return (which is gate evidence, never a question), and every Release action the contract names. A skill that asks for permission for any of these is defective.

## Roles and the Ladder

| Role | Does | Writes? |
|---|---|---|
| orchestrator | decomposes an effort into tasks, dispatches workers, gates every return, commits accepted work | commits only; edits only for its own final attempt |
| worker | implements one task under the worker contract (`contracts/worker.md`) and a brief, test first | yes, owned files only |
| scout | finds facts in the tree, `file:line` or NOT FOUND | no |
| steelman | one discovery pass and at most one closure pass on an agreed design | no |
| finder | one review dimension on the frozen candidate | no |
| verifier | adversarially confirms or drops each finding | no |
| test-runner | executes a command that needs writable scratch state, in an isolated workspace | scratch only |

The worker has its entry rung only. Routing between attempts is by failure signature: same-thread continuation with the failing output, a re-brief when the brief was wrong, a split when behaviors are separable, then the orchestrator's own attempt, then a gap, never a stronger model. A rung is a model at an effort level, in a writing variant and a read-only variant.

The worker contract is the fixed text every worker works under: test first, owned files only, the mechanical floor, minimal change, and the four returns DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED. A brief carries Goal, Files owned, Hidden shared surfaces, Neighbors, Anchors, Acceptance, Constraints, Requirements covered, and Test command. A gate record carries the task and its lineage, the rung, the candidate revision, every contract item checked with its command and result, the owned-files and mechanical-floor results, any Premise touched, the verdict, and the next action.

A worker leaves its changes uncommitted in its own workspace. The orchestrator reads the complete change set, gates it, commits it onto the effort's candidate, and records that revision in the gate record. An exhausted lineage's workspace is committed to `gap/<task-slug>` instead.

Rungs are named in one place, the registry at `~/.claude/gambit/models.json`, which the harness's configuration renders. Skills and contracts name roles, never rungs and never a model.

## Skills

A skill exists only if it owns a stage of the loop or is a mechanic the loop calls. Every section of a skill serves a loop step or a principle; a section that serves neither is deleted.

Owners:

- `brainstorming` — step 1. Its research step is also the bug path: the scout identifies the reproduction command and the root cause with `file:line`; the test-runner executes the reproduction when it needs writable state; the root cause becomes a Premise, and the reproduction becomes the first task's failing test and a Requirement's evidence.
- `executing-plans` — steps 2 through 7: decompose, build, gate, integrate, call review, release, report.
- `review` — step 5, correcting under the build step's routing until closure passes.

Every other skill in the tree is kept only if it owns a stage or is a mechanic one of the owners calls; otherwise it is deleted, and the Decision Log records which.

Deleted: `finishing-branch`, `test-driven-development`, `verification`, `debugging`. Their responsibilities live in the worker contract (test first), the gate and review (evidence), and brainstorming's bug path (reproduce before patch).

## Install

Gambit is one tree of skills and contracts. A harness runs it by providing five operations:

| Operation | Claude Code | Pi |
|---|---|---|
| Dispatch a role | Agent tool with the rung's agent | Agent tool (pi-subagents) with the rung's agent file |
| Record task state | Task API | Task API (pi-tasks) |
| Load a stage | read `skills/<name>/SKILL.md` and follow it | same, or the skill's slash command |
| Isolate a workspace | `git worktree add`, run by the orchestrator | same |
| End a run | the report; the session ends | the report, then `goal_complete` for *released* or `goal_end` for the other two outcomes |

Every command the orchestrator itself runs — `git`, the Done checks, the Release actions — goes through the harness's shell; both harnesses provide one.

**Claude Code.** Add the plugin from this repository's marketplace entry (`.claude-plugin/marketplace.json`), install the rung agent files your registry names under `~/.claude/agents/`, and write `~/.claude/gambit/models.json`. The nix-config module that does all three is the reference.

**Pi.** Point `skills` at this repository's `skills/` directory and enable pi-tasks, pi-subagents, and pi-goal. Set pi-goal's response-limit and no-progress pauses to null; a run that pauses for a person is not a gambit run. pi-goal accepts *ended with gaps* and *stopped on catastrophe* as terminal only through a terminal-outcome extension: a `goal_end` tool taking `outcome` (`ended_with_gaps` or `stopped_on_catastrophe`) and the report text, after which the goal is terminal and a resume only shows the report. Until the harness installs one, Pi is not supported for goal runs. Render the same rung agent files in pi-subagents frontmatter. The registry is shared.

**Verify.** From a scratch repository: read a skill, create and read back a task, dispatch a read-only rung and receive its result, create a worktree with git. On Pi, additionally run one goal to *released* and one to *ended with gaps* and confirm each terminates.
