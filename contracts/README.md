# Contracts

## What a contract is

A contract is the fixed text a role works under. Every dispatch passes it by absolute path, and the agent reads it in its own context. The brief is the variable part of a dispatch. Contracts name roles and operations, never a harness's tool, a model profile, or a model.

## Roles and their contracts

| Role | Contract | Writes? |
|---|---|---|
| `implementer` | `contracts/implementer.md` | Owned files only |
| `orchestrator` | `skills/executing-plans/SKILL.md` | Record and candidate |
| `scout` | `contracts/scout.md` | No |
| `steelman` | `contracts/steelman.md` | No |
| `task-reviewer` | `skills/review/reviewers/task-reviewer.md` | No |
| `conformance-reviewer` | `skills/review/reviewers/conformance-reviewer.md` | No |
| `integration-reviewer` | `skills/review/reviewers/integration-reviewer.md` | No |
| `finding-verifier` | `skills/review/reviewers/finding-verifier.md` | No |
| `test-runner` | The exact command it is given, run in an isolated workspace | Scratch only |

The `scout`, `steelman`, `task-reviewer`, `conformance-reviewer`, `integration-reviewer`, and `finding-verifier` roles are read-only. Only `implementer` may change owned files. The `test-runner` may write scratch state, and the `orchestrator` writes the record and the candidate.

## The registry

Model profiles and role assignments are defined in `contracts/models.md` and named only in the registry it describes. The Director coordinates the epic; the Orchestrator coordinates an effort. Neither title changes with its model profile.
