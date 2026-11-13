# Epic and task templates

Use the record-task-state operation. Fill every field from the goal, decisions, and research before creating executable work. The epic body is one document: the decision line, then exactly the ten sections below in order. Its Decision Log is attached record context, outside that body. Write the record per `skills/executing-plans/references/record.md`.

Rows in "What will be true when done" are the Requirements (R ids). Rows in "What I'm assuming" are the Premises (P ids). Rows in "What could go wrong" are the failure cases (F ids). Entries under "What we won't do" are the Must Not Ship entries.

### Epic record

```markdown
# [Epic name]

[One sentence: what is approved.] Level of care: [limited, serious, or severe]. Decisions needed: [n, or none].

## What you asked for
[One to three plain sentences: the desired end state and reason, in the person's terms. Never a solution.]

## What could go wrong, and how much we care
| If this happened | How bad | What we do |
|---|---|---|
| F1 [A failure in the past tense, as the person would experience it] | [limited, serious, or severe] | [prevent, reduce, recover, or accept]: [the one thing done about it] |
Level of care: [the worst row's rating], set by [Fn].

## Things you did not ask for
| Where | What | Why | Cost |
|---|---|---|---|
| [R, P, or F id; a mechanism; a check; or a release step] | [the addition beyond the person's words] | [why it is there] | [new files, infrastructure, external systems, or check runtime] |

## What will be true when done
| Must be true | How we'll know |
|---|---|
| R1 [Atomic, testable outcome] | [named test or observable result, and the exact command] |

## What I'm assuming
| Assumption | If wrong |
|---|---|
| P1 [Falsifiable fact, with evidence] | Intent [survives; the design consequence / cannot survive; the reason] |

## What we won't do
- [Forbidden outcome or non-goal]. [Why it is excluded.]

## How, and why not the other ways
[One paragraph: the chosen shape, interfaces, data flow, and reason, grounded in cited research.]
| Alternative | Why not | Reconsider when |
|---|---|---|
| [Alternative] | [the reason it loses] | [the condition that changes that reason, or never] |

## What leaves this machine or can't be undone
| Step | Target | Undo |
|---|---|---|
| 1 [Exact action], so [intended effect] | [exact repository, branch, service, or destination] | [how to reverse it, or none] |
Then: [observable facts that must all hold before reporting release].

## Decisions I need from you
| Question | Options | I recommend | Because |
|---|---|---|---|
| [Open choice] | [realistic options] | [one option] | [the reason] |

## Checks the machines run
Done: [exact task fast check with its setup and working directory]; [the integrated candidate's full gate, in order].
Evidence: [the tests and observable results named under How we'll know].
Steps: [read-only: schema check; implementer: schema check, then head, ancestry, clean and owned from the task base revision, then the gate, named in `.orrery/project.toml` or defined by this contract as an absolute argv, no shell, under the heavy-command wrapper's absolute path, through the project's development-environment entry if tools live only there, with its needs and limit in seconds.] A Decision Log line changes them for steps started after it.
Quality Bar: Failing, low-quality, or bad code is unacceptable, but failure to meet a mythic platonic ideal of code or cover literally every imaginable edge case is NOT itself a defect. This bar is FIXED for every epic; write it verbatim — never elicit it, strengthen it, or make it a per-project preference. A defect is exactly one of: a Requirement's named evidence not met; a Must Not Ship entry present; a change outside the task's owned files; a change the contract did not ask for; a violation of the implementer contract's mechanical floor (a suppressed check, a weakened or tautological test, dead code, an unhandled error); an assertion its declared gate finds does not hold; or a security or data-loss failure with a reachable precondition that the change itself introduces. Everything else the orchestrator or a reviewer notices is an observation — it may be recorded in the Decision Log and the report; it never becomes work during the run. The craftsmanship asked of the implementer is one line: simple, foundational, secure; match the surrounding code.
Review gate: [NAME] | agent: [read-only agent file] | limit: [seconds] | must: [assertion] | must not: [assertion]
```

`Review gate:` lines are optional, one per declared gate.

After acceptance, "Decisions I need from you" reads `None`, then the settled decisions by id. Acceptance freezes What you asked for, the assumptions with their If-wrong clauses, and the Requirements. Keep later assessments in the Decision Log, never rewriting frozen text.

### Task brief

Supply the workspace, base revision, and applicable contract clauses with this body. Keep Goal plus Acceptance plus Constraints under 250 words total. It carries no implementation steps, code, or diffs. Create only work grounded in the tree now.

```markdown
## Goal
[One concrete result required by the contract.]

## Files owned
- [Exact repository-relative path, including each addition or deletion. No globs or directory allowlists.]

## Hidden shared surfaces
[Lockfiles, generated indexes, registries, snapshots, and other implicit writes. State None when absent. They grant no ownership; list every edit in Files owned.]

## Neighbors
[Every concurrent task and its complete owned-file list, all off-limits. State None for a single task.]

## Anchors
[Verified source and test anchors at the base revision, as path:symbol:line.]

## Acceptance
[Name an existing test or reproduction with its expected result, or state behavioral criteria for the failing test written first.]

## Constraints
[The level of care with the row that set it. Each applicable failure row quoted with its What we do, so no id arrives without its text. Applicable What we won't do entries, scope, and safety limits.]

## Requirements covered
- R1: [Requirement text and its named evidence.]

## Test command
Test command: [exact task fast check from Checks the machines run].
Gate: [step route only: the gate NAME from Steps].
```

### Effort brief

The Director writes an effort's brief only once dependency-ready, from the accepted base. Objective plus Interfaces plus Binding contract stay under 250 words excluding lists.

```markdown
## Objective
[Quote each covered Requirement with its named evidence.]

## Partition
[List owned files; name concurrent efforts' files as off-limits.]

## Interfaces
[List interfaces published or consumed, in order.]

## Binding contract
[The level of care with the row that set it, each applicable failure row with its What we do, applicable What we won't do entries, If-wrong clauses, the Quality Bar, and Decision Log entries touching these files.]

## Base
[Accepted base; epic `<repository-id>/<epic-slug>`; `effort/<epic-slug>-<n>`; checks; head's `efforts_admitted`; gate names; absolute `gates.toml`.]

## Report shape
[Cap the report at 400 words.]
```

Tasks are pending executable children of the epic, never blocked by it. Owned-file lists are disjoint within the effort. Author tasks needing unfinished interfaces once they exist.
