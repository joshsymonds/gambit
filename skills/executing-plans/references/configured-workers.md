# Configured Codex Worker Ladder

- [Common async transport](#common-async-transport)
- [Rung 1: initial implementation](#rung-1-initial-implementation)
- [Rung 2: informed same-thread repair](#rung-2-informed-same-thread-repair)
- [Rung 3: fresh reasoning escalation](#rung-3-fresh-reasoning-escalation)
- [Rung 4: terminal maximum-reasoning escalation](#rung-4-terminal-maximum-reasoning-escalation)

Read this reference completely whenever `contracts/executors.md` resolves the Claude
`executing-plans` worker to configured Codex. It defines the fixed ladder for each task:

1. Luna-class implementation through `worker.tool`.
2. Exactly one informed same-thread repair through `worker.reply_tool`.
3. Fresh Sol-class escalation through `escalation.tool`.
4. Terminal maximum-reasoning escalation through `escalation-final.tool`, repeated with
   updated evidence until the task verifies clean.

The concrete model names and settings always come from the validated registry. Do not skip or
reorder a rung; only rung 4 repeats. Never fall back to native Claude after selecting this route.
## Common async transport

Every rung uses a new anonymous `gambit:gambit-wrapper` Agent and the exact relay protocol in
`contracts/async-dispatch.md`; never call an MCP tool synchronously in the orchestrator context.
Before launching a batch, expand `~/.claude/gambit/async-results/` to an absolute path, ensure it
exists, assign one collision-resistant artifact path per call, and record the complete handle
mapping. Emit all ready wrappers together, do useful overlap work, collect each with bounded
`TaskOutput block=true` re-waits, and drain the whole batch before judgment. Never message a
wrapper and never treat a nonterminal wait timeout as failure.

Validate the exact three-line wrapper envelope and exact artifact-path match before reading the
artifact, then delete a successfully validated artifact. The MCP response must have non-empty
string `content`; an initial call must also have a non-empty string `threadId` containing no CR or LF.
Require exactly one worker status in `content`: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`,
or `BLOCKED`. Empty, malformed, missing-status, multi-status, terminal timeout, tool, or protocol
failure stops the configured route immediately without retry, cancellation, or native fallback.

## Rung 1: initial implementation

Launch `worker.tool` with this opaque argument object. Map `approval_policy` to `approval-policy`:

```json
{
  "prompt": "Read <absolute worker contract path> first and follow it exactly.\n\n## Task\n<complete constructed brief from Goal, Implementation, and Success Criteria; never session history>\n\n## Files owned\n<exact allowlist including every artifact, deletion, mode change, and symlink>\n\n## Hidden shared surfaces\n<exact checked surfaces>\n\n## Context\n<needed interfaces and decisions>\n\n## Neighbors\n<concurrent subjects and owned-file allowlists, or None>\n\nEpic requirements and Quality Bar needed by this brief: <verbatim relevant text>\nTest command: <focused command>\nWorkspace: <exact worktree>; shared base: <prior commit or wave-start base>\nReturn exactly one status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.",
  "model": "<worker.model>",
  "cwd": "<exact worker worktree>",
  "sandbox": "<worker.sandbox>",
  "approval-policy": "<worker.approval_policy>",
  "developer-instructions": "You are a subordinate worker assigned exactly one implementation brief. Do not orchestrate, load skills, use nested agents, discover tasks, expand scope, commit, merge, create worktrees, mutate plans, or assign work. Edit only owned files and return one required worker status.",
  "config": {
    "model_reasoning_effort": "<worker.reasoning_effort>",
    "service_tier": "<worker.service_tier>",
    "web_search": "disabled",
    "plugins.\"gambit@personal\".enabled": false,
    "skills.include_instructions": false,
    "orchestrator.skills.enabled": false,
    "features.collab": false,
    "features.multi_agent_v2.enabled": false,
    "features.apps": false
  }
}
```

Retain the validated initial `threadId` with its task mapping. `DONE` advances only after fresh
focused verification and the checkpoint quality gate. Any correctness, scope, missing-context,
verification, or quality defect advances to rung 2 with exact actionable evidence. A wrong brief,
unsettled architecture, or oversized task stops or decomposes under the main workflow instead.

## Rung 2: informed same-thread repair

Launch a new wrapper for `worker.reply_tool` with exactly these wire fields:

```json
{
  "prompt": "Reread <absolute worker contract path> and complete the one informed same-thread repair in the existing worktree. Actionable evidence: <at most 2,000 characters containing the cited defect, missing value, or relevant failing-output excerpt; cite the artifact or log path when longer>. The original brief and prior result are already in this thread; do not require them to be repeated. Repair only in scope, rerun the focused command, and return exactly one required worker status.",
  "threadId": "<validated initial worker threadId>"
}
```

This semantic continuation is the only permitted use of `codex-reply`. It inherits the initial
worker's model, reasoning, service tier, cwd, sandbox, approval, and isolation configuration. Do
not resend the original brief or whole initial `content`, and do not use it to recover a transport
failure. A verified, quality-clean result advances; any remaining semantic, verification, or quality
defect advances to rung 3 with bounded evidence.

## Rung 3: fresh reasoning escalation

Launch `escalation.tool` as a fresh call in the same worktree:

```json
{
  "prompt": "Read <absolute worker contract path> first. Implement the complete original brief in <same worktree>. Initial attempt: <at most 1,000 characters summarizing the relevant result with cited excerpts>. Informed repair: <at most 1,000 characters summarizing the relevant result with cited excerpts>. Remaining evidence: <at most 2,000 characters with the exact defect and relevant failing-output excerpt; cite the artifact or log path when longer>. Rerun the focused command and return exactly one required worker status.",
  "model": "<escalation.model>",
  "cwd": "<same worker worktree>",
  "sandbox": "<escalation.sandbox>",
  "approval-policy": "<escalation.approval_policy>",
  "developer-instructions": "You are the fresh final repair worker for one bounded brief. Do not orchestrate, load skills, use nested agents, expand scope, commit, merge, create worktrees, mutate plans, or assign work. Edit only owned files and return one required worker status.",
  "config": {
    "model_reasoning_effort": "<escalation.reasoning_effort>",
    "web_search": "disabled",
    "plugins.\"gambit@personal\".enabled": false,
    "skills.include_instructions": false,
    "orchestrator.skills.enabled": false,
    "features.collab": false,
    "features.multi_agent_v2.enabled": false,
    "features.apps": false
  }
}
```

Never embed either prior result's whole `content` in the fresh escalation prompt; carry only the
bounded summaries, cited excerpts, and evidence above.

If this fresh escalation does not produce a verified, quality-clean result, advance to rung 4.

## Rung 4: terminal maximum-reasoning escalation

Launch `escalation-final.tool` as a fresh call in the same worktree. The wire is the rung-3 shape
with the `escalation-final` registry values and one additional bounded history field:

```json
{
  "prompt": "Read <absolute worker contract path> first. Implement the complete original brief in <same worktree>. Initial attempt: <at most 1,000 characters summarizing the relevant result with cited excerpts>. Informed repair: <at most 1,000 characters summarizing the relevant result with cited excerpts>. Prior escalations: <at most 1,000 characters per prior escalation attempt summarizing its result with cited excerpts>. Remaining evidence: <at most 2,000 characters with the exact defect and relevant failing-output excerpt; cite the artifact or log path when longer>. Rerun the focused command and return exactly one required worker status.",
  "model": "<escalation-final.model>",
  "cwd": "<same worker worktree>",
  "sandbox": "<escalation-final.sandbox>",
  "approval-policy": "<escalation-final.approval_policy>",
  "developer-instructions": "You are the terminal repair worker for one bounded brief. Do not orchestrate, load skills, use nested agents, expand scope, commit, merge, create worktrees, mutate plans, or assign work. Edit only owned files and return one required worker status.",
  "config": {
    "model_reasoning_effort": "<escalation-final.reasoning_effort>",
    "web_search": "disabled",
    "plugins.\"gambit@personal\".enabled": false,
    "skills.include_instructions": false,
    "orchestrator.skills.enabled": false,
    "features.collab": false,
    "features.multi_agent_v2.enabled": false,
    "features.apps": false
  }
}
```

This rung repeats: when an attempt does not produce a verified, quality-clean result, dispatch
another fresh `escalation-final` call carrying the updated remaining evidence and the bounded
history of every prior attempt. Never repeat with unchanged evidence — each re-dispatch must carry
the new defect, failing output, or missing value from the attempt before it. A defect that recurs
at a later checkpoint re-enters this rung with its recurrence as the new evidence. There is no
human rung; the ladder ends only in a verified, quality-clean result. The epic-level
negative-convergence circuit breaker in the main workflow still applies. Never embed any prior
result's whole `content` in the prompt; carry only the bounded summaries, cited excerpts, and
evidence above.
