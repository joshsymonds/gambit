# Step ends

A read-only step runs one of the read-only roles (`scout`, `steelman`, `task-reviewer`, `conformance-reviewer`, `integration-reviewer`, `finding-verifier`, `test-runner`). It runs only the schema check, so every read-only step ends in one of the twelve ends below. An implementer step (the writing role, schema `contracts/schemas/implementer.json`) ends in the same twelve ends and is read in the last two columns. A kept return is a return the caller reads: the ends `done`, `returned` and `goal_unmet`. Every other end carries no schema-valid return.

No read-only end spends an implementer attempt. The steelman column gives the steelman's action where it differs from the read-only action. The two implementer columns give the implementer's action and attempt cost for the same end.

## Step ends

| End | Action for read-only roles | Cost | Steelman | Implementer action | Implementer attempt |
|---|---|---|---|---|---|
| `done` | Read the return and decide as for that role's return. | Nothing spent; no implementer attempt. | Its pass; no rerun. | Read the return. Its checks and `commit` are gate evidence: inspect, task-review, and decide. | Spends the one that ran; nothing more. |
| `returned` | The return is blocked and names missing input, which is a brief defect. Correct the brief, then start a fresh step. | One fresh step; no implementer attempt. | Its pass, blocked included; no rerun. | A return with status `needs_context` or `blocked`: gate it as today's NEEDS_CONTEXT or BLOCKED return, routed by the build step. | Attempt cost as that routing step spends; a re-brief for a brief defect spends none. |
| `goal_unmet` | Read the kept return and the judge's reason, then decide as for that role's return. | Nothing spent; no implementer attempt. | Its pass; no rerun. | Read the kept return and the judge's reason, and gate it as a done return. | Spends the one that ran; nothing more. |
| `checks_failed` | No kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. | NOT DONE: an execution failure whose signature is the end with its failed check. Routing step 1 continues it as a fresh step. | The one that ran is spent. |
| `failed` | No kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. | No kept return. Start one fresh step with the same arguments, at the task base revision. If that end also has no return, route it as an execution failure. | Spends none for the replacement. |
| `stopped` | The caller stopped it. Record it and act on nothing. | Nothing spent; no fresh step; no implementer attempt. | Record it and act on nothing. | The caller stopped it. Record it and act on nothing. | Spends none. |
| `engine_restarted` | No kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. | No kept return. Start one fresh step with the same arguments, at the task base revision. If that end also has no return, route it as an execution failure. | Spends none for the replacement. |
| `overtime` | The watch ended the step with no kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. | The watch ended the step with no kept return. NOT DONE: an execution failure whose signature is the end with its reason. Routing step 1 continues it as a fresh step. | The one that ran is spent. |
| `tool_stuck` | The watch ended the step with no kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. | The watch ended the step with no kept return. NOT DONE: an execution failure whose signature is the end with its reason. Routing step 1 continues it as a fresh step. | The one that ran is spent. |
| `silent` | The watch ended the step with no kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. | The watch ended the step with no kept return. NOT DONE: an execution failure whose signature is the end with its reason. Routing step 1 continues it as a fresh step. | The one that ran is spent. |
| `looping` | The watch ended the step with no kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. | The watch ended the step with no kept return. NOT DONE: an execution failure whose signature is the end with its reason. Routing step 1 continues it as a fresh step. | The one that ran is spent. |
| `wedged` | The watch ended the step with no kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. | The watch ended the step with no kept return. NOT DONE: an execution failure whose signature is the end with its reason. Routing step 1 continues it as a fresh step. | The one that ran is spent. |

## Implementer steps

An implementer step is a writing step with schema `contracts/schemas/implementer.json` and done value `done`. Its checks are the schema, then `head`, `ancestry`, `clean`, `owned`, then the gate (orrery v0.14.0, `docs/contract.md`, "Step lifecycle", Checks and Ends).

Every fresh implementer step, a replacement or a continuation, passes `revision` as the task base: the task's `dispatch.revision`, never the workspace HEAD. The owned check then diffs from the task base, so an earlier unchecked commit in the workspace cannot pass it (orrery v0.14.0 `internal/enginehost/stepgit.go`, `stepGitOwnedCheck`).

## Refusals

A `step_start` or other step call can be refused with an error and no id. The refusals below apply to implementer step calls too. Two refusals are capacity limits:

- `resource_exhausted`, when the step cap (`--step-cap`) would be passed.
- `-32000` with the message `Server already has 8 tool calls in flight`, when the MCP server refuses a ninth concurrent call.

For either one, wait, then retry the same call. Each wait calls `WaitSteps` with only ids still running, using the caller's running steps. When none run, wait one minute instead. Then retry the refused call. The work does not leave a gap.

Any other refusal is a brief defect. Record it in the task's `conduct.brief_defects` or in the Decision Log, correct the brief, and retry the call.
