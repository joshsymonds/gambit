# Step ends

A read-only step runs one of the read-only roles (`scout`, `steelman`, `task-reviewer`, `conformance-reviewer`, `integration-reviewer`, `finding-verifier`, `test-runner`). It runs only the schema check, so every step ends in one of the twelve ends below. A kept return is a return the caller reads: the ends `done`, `returned` and `goal_unmet`. Every other end carries no schema-valid return.

No end spends an implementer attempt. The steelman column gives the steelman's action where it differs from the read-only action.

## Step ends

| End | Action for read-only roles | Cost | Steelman |
|---|---|---|---|
| `done` | Read the return and decide as for that role's return. | Nothing spent; no implementer attempt. | Its pass; no rerun. |
| `returned` | The return is blocked and names missing input, which is a brief defect. Correct the brief, then start a fresh step. | One fresh step; no implementer attempt. | Its pass, blocked included; no rerun. |
| `goal_unmet` | Read the kept return and the judge's reason, then decide as for that role's return. | Nothing spent; no implementer attempt. | Its pass; no rerun. |
| `checks_failed` | No kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. |
| `failed` | No kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. |
| `stopped` | The caller stopped it. Record it and act on nothing. | Nothing spent; no fresh step; no implementer attempt. | Record it and act on nothing. |
| `engine_restarted` | No kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. |
| `overtime` | The watch ended the step with no kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. |
| `tool_stuck` | The watch ended the step with no kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. |
| `silent` | The watch ended the step with no kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. |
| `looping` | The watch ended the step with no kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. |
| `wedged` | The watch ended the step with no kept return. Start one fresh step with the same arguments. If that end also has no return, dispatch the role once through the dispatch operation. | One fresh step, then at most one dispatch; no implementer attempt. | Steelman reruns as the read-only action says. |

## Refusals

A `step_start` or other step call can be refused with an error and no id. Two refusals are capacity limits:

- `resource_exhausted`, when the step cap (`--step-cap`) would be passed.
- `-32000` with the message `Server already has 8 tool calls in flight`, when the MCP server refuses a ninth concurrent call.

For either one, wait, then retry the same call. Each wait calls `step_wait` with only ids still running, using the caller's running steps. When none run, wait one minute instead. Then retry the refused call. The work does not leave a gap.

Any other refusal is a brief defect. Record it in the task's `conduct.brief_defects` or in the Decision Log, correct the brief, and retry the call.
