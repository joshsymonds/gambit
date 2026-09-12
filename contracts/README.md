# Contracts

## What a contract is

A contract is the fixed text a role works under. Every dispatch passes it by absolute path, and the agent reads it in its own context. The brief is the variable part of a dispatch. Contracts name roles and operations, never a harness's tool, a rung, or a model.

## Roles and their contracts

| Role | Contract | Writes? |
|---|---|---|
| `worker` | `contracts/worker.md` | Owned files only |
| `escalation` | `contracts/worker.md` | Owned files only |
| `orchestrator` | `skills/executing-plans/SKILL.md` | Record and candidate |
| `scout` | `contracts/scout.md` | No |
| `steelman` | `contracts/steelman.md` | No |
| `finder` | Reviewer files under `skills/review/reviewers/` | No |
| `verifier` | Reviewer files under `skills/review/reviewers/` | No |
| `test-runner` | The exact command it is given, run in an isolated workspace | Scratch only |

The `scout`, `steelman`, `finder`, and `verifier` roles are read-only. Only `worker` and `escalation` may change owned files. The `test-runner` may write scratch state only, and the `orchestrator` writes the record and the candidate.

## The registry

Rungs, entry rungs, and ladders are defined in `contracts/models.md` and named only in the registry it describes.
