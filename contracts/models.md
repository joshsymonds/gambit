# Roles and model profiles

## Roles

| Role | Does | Writes? | Contract |
|---|---|---|---|
| `implementer` | Implements one task under its contract and brief, test first. | Yes, owned files only. | `contracts/implementer.md` |
| `orchestrator` | Runs one effort, final review, or release from the record. | Yes, record and candidate. | `skills/executing-plans/SKILL.md` |
| `scout` | Finds facts in the tree and returns `file:line` evidence or NOT FOUND. | No. | `contracts/scout.md` |
| `steelman` | Runs one discovery pass and at most one closure pass on an agreed design. | No. | `contracts/steelman.md` |
| `task-reviewer` | Reviews one task's complete change against its brief and contract. | No. | `skills/review/reviewers/task-reviewer.md` |
| `conformance-reviewer` | Reviews the final candidate against the overall contract. | No. | `skills/review/reviewers/conformance-reviewer.md` |
| `integration-reviewer` | Reviews cross-task interactions and shared interfaces in the final candidate. | No. | `skills/review/reviewers/integration-reviewer.md` |
| `finding-verifier` | Independently confirms or drops a reported defect, or checks its closure. | No. | `skills/review/reviewers/finding-verifier.md` |
| `test-runner` | Executes a command needing writable scratch state in an isolated workspace. | Yes, scratch only. | The command it is given. |

The Director is the session coordinating the epic, not another dispatch role. The Orchestrator coordinates an effort. Stage names describe when work happens; role names describe responsibility; model profiles describe execution settings.

## Model profiles

A model profile selects a model and reasoning effort. Its writing and read-only agent variants select tool access; read-only instructions are not operating-system containment. Every role has one entry model profile. Profiles are not an escalation ladder.

Every dispatch uses the role's entry profile. An implementer gets at most two attempts against a complete brief; the second carries the failing evidence from its gate record. A re-brief correcting the orchestrator's brief spends no attempt, and each split descendant starts with its own two. Routing between attempts belongs to `skills/executing-plans/SKILL.md`. An agent never changes its own profile. Splitting preserves the lineage; it does not select a stronger model.

After the implementer's attempts are spent, the Orchestrator makes one final attempt itself under `contracts/implementer.md`, gated like any return. If it fails, the lineage is a gap.

## The registry

Model profiles are named in one place shared by both harnesses: `~/.claude/gambit/models.json`, rendered by harness configuration.

`profiles` maps each profile name to one of these shapes:

- `{"agent": <name>, "readonly_agent": <name>}` names dispatch targets the harness resolves by name.
- `{"model": <alias>}` names a model alias for the dispatch operation.

`roles` maps each role name to `{"entry": <profile>, "readonly": true?}`, where `?` marks an optional key. Skills and contracts name roles, never concrete models or profile identifiers.

## Resolving a dispatch

1. Look up the role in the registry.
2. Select its entry model profile.
3. Select that profile's agent, its read-only variant for a read-only role, or its model alias.
4. Dispatch with the role's contract by absolute path and its brief as text.

Nothing is supplied implicitly. If the registry is missing or cannot resolve a role, record it in the Decision Log. Every task needing that role becomes a gap citing it. Independent work continues. The run ends with gaps only when no executable work remains. Without an `orchestrator` role, the loading session performs the effort itself.
