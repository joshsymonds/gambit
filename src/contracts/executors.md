<!-- gambit-backend:claude -->
# External executor registry

Claude-backed Gambit may override the native executor for all eight contracted execution roles by
reading `~/.claude/gambit/executors.json`. The registry is optional. It selects an executor only;
the class contract, authority, model tier, and workflow semantics remain unchanged.

All eight contracted execution roles may be configured: `steelman`, `worker`, `escalation`,
`escalation-final`, `scout`, `finder`, `verifier`, and `test-runner`. A configured `worker`
requires configured `escalation` and `escalation-final` entries so the executing-plans repair
ladder cannot silently change executor families at its later rungs.

## Canonical schema

The file is one JSON object whose keys are roles. Each role is optional except that `worker`
requires `escalation`. Validate the complete object against this schema, not merely the requested
role:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "steelman": {
      "type": "object",
      "properties": {
        "executor": { "const": "codex" },
        "tool": {
          "type": "string",
          "pattern": "^mcp__[A-Za-z0-9_-]+__[A-Za-z0-9_-]+$"
        },
        "model": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$",
          "not": {
            "enum": [
              "inherit",
              "default",
              "haiku",
              "sonnet",
              "opus",
              "fable",
              "cheap",
              "cheap-or-standard",
              "standard",
              "most-capable"
            ]
          }
        },
        "reasoning_effort": {
          "type": "string",
          "enum": [
            "none",
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
            "max",
            "ultra"
          ]
        },
        "sandbox": { "const": "read-only" },
        "approval_policy": {
          "type": "string",
          "enum": ["untrusted", "on-request", "never"]
        },
        "web_search": { "const": "live" }
      },
      "required": [
        "executor",
        "tool",
        "model",
        "reasoning_effort",
        "sandbox",
        "approval_policy",
        "web_search"
      ],
      "additionalProperties": false
    },
    "scout": {
      "type": "object",
      "properties": {
        "executor": { "const": "codex" },
        "tool": {
          "type": "string",
          "pattern": "^mcp__[A-Za-z0-9_-]+__[A-Za-z0-9_-]+$"
        },
        "model": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$",
          "not": {
            "enum": [
              "inherit",
              "default",
              "haiku",
              "sonnet",
              "opus",
              "fable",
              "cheap",
              "cheap-or-standard",
              "standard",
              "most-capable"
            ]
          }
        },
        "reasoning_effort": {
          "type": "string",
          "enum": [
            "none",
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
            "max",
            "ultra"
          ]
        },
        "sandbox": { "const": "read-only" },
        "approval_policy": {
          "type": "string",
          "enum": ["untrusted", "on-request", "never"]
        }
      },
      "required": [
        "executor",
        "tool",
        "model",
        "reasoning_effort",
        "sandbox",
        "approval_policy"
      ],
      "additionalProperties": false
    },
    "worker": {
      "type": "object",
      "properties": {
        "executor": { "const": "codex" },
        "tool": {
          "type": "string",
          "pattern": "^mcp__[A-Za-z0-9_-]+__[A-Za-z0-9_-]+$"
        },
        "reply_tool": {
          "type": "string",
          "pattern": "^mcp__[A-Za-z0-9_-]+__codex-reply$"
        },
        "model": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$",
          "not": {
            "enum": [
              "inherit",
              "default",
              "haiku",
              "sonnet",
              "opus",
              "fable",
              "cheap",
              "cheap-or-standard",
              "standard",
              "most-capable"
            ]
          }
        },
        "reasoning_effort": {
          "type": "string",
          "enum": [
            "none",
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
            "max",
            "ultra"
          ]
        },
        "service_tier": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$",
          "not": { "enum": ["inherit", "default"] }
        },
        "sandbox": {
          "type": "string",
          "enum": ["read-only", "workspace-write", "danger-full-access"]
        },
        "approval_policy": {
          "type": "string",
          "enum": ["untrusted", "on-request", "never"]
        }
      },
      "required": [
        "executor",
        "tool",
        "reply_tool",
        "model",
        "reasoning_effort",
        "service_tier",
        "sandbox",
        "approval_policy"
      ],
      "additionalProperties": false
    },
    "escalation": {
      "type": "object",
      "properties": {
        "executor": { "const": "codex" },
        "tool": {
          "type": "string",
          "pattern": "^mcp__[A-Za-z0-9_-]+__[A-Za-z0-9_-]+$"
        },
        "model": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$",
          "not": {
            "enum": [
              "inherit",
              "default",
              "haiku",
              "sonnet",
              "opus",
              "fable",
              "cheap",
              "cheap-or-standard",
              "standard",
              "most-capable"
            ]
          }
        },
        "reasoning_effort": {
          "type": "string",
          "enum": [
            "none",
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
            "max",
            "ultra"
          ]
        },
        "sandbox": {
          "type": "string",
          "enum": ["read-only", "workspace-write", "danger-full-access"]
        },
        "approval_policy": {
          "type": "string",
          "enum": ["untrusted", "on-request", "never"]
        }
      },
      "required": [
        "executor",
        "tool",
        "model",
        "reasoning_effort",
        "sandbox",
        "approval_policy"
      ],
      "additionalProperties": false
    },
    "escalation-final": {
      "type": "object",
      "properties": {
        "executor": { "const": "codex" },
        "tool": {
          "type": "string",
          "pattern": "^mcp__[A-Za-z0-9_-]+__[A-Za-z0-9_-]+$"
        },
        "model": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$",
          "not": {
            "enum": [
              "inherit",
              "default",
              "haiku",
              "sonnet",
              "opus",
              "fable",
              "cheap",
              "cheap-or-standard",
              "standard",
              "most-capable"
            ]
          }
        },
        "reasoning_effort": {
          "type": "string",
          "enum": [
            "none",
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
            "max",
            "ultra"
          ]
        },
        "sandbox": {
          "type": "string",
          "enum": ["read-only", "workspace-write", "danger-full-access"]
        },
        "approval_policy": {
          "type": "string",
          "enum": ["untrusted", "on-request", "never"]
        }
      },
      "required": [
        "executor",
        "tool",
        "model",
        "reasoning_effort",
        "sandbox",
        "approval_policy"
      ],
      "additionalProperties": false
    },
    "finder": {
      "type": "object",
      "properties": {
        "executor": { "const": "codex" },
        "tool": {
          "type": "string",
          "pattern": "^mcp__[A-Za-z0-9_-]+__[A-Za-z0-9_-]+$"
        },
        "model": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$",
          "not": {
            "enum": [
              "inherit",
              "default",
              "haiku",
              "sonnet",
              "opus",
              "fable",
              "cheap",
              "cheap-or-standard",
              "standard",
              "most-capable"
            ]
          }
        },
        "reasoning_effort": {
          "type": "string",
          "enum": [
            "none",
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
            "max",
            "ultra"
          ]
        },
        "sandbox": { "const": "read-only" },
        "approval_policy": {
          "type": "string",
          "enum": ["untrusted", "on-request", "never"]
        },
        "web_search": { "const": "live" }
      },
      "required": [
        "executor",
        "tool",
        "model",
        "reasoning_effort",
        "sandbox",
        "approval_policy",
        "web_search"
      ],
      "additionalProperties": false
    },
    "verifier": {
      "type": "object",
      "properties": {
        "executor": { "const": "codex" },
        "tool": {
          "type": "string",
          "pattern": "^mcp__[A-Za-z0-9_-]+__[A-Za-z0-9_-]+$"
        },
        "model": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$",
          "not": {
            "enum": [
              "inherit",
              "default",
              "haiku",
              "sonnet",
              "opus",
              "fable",
              "cheap",
              "cheap-or-standard",
              "standard",
              "most-capable"
            ]
          }
        },
        "reasoning_effort": {
          "type": "string",
          "enum": [
            "none",
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
            "max",
            "ultra"
          ]
        },
        "sandbox": { "const": "read-only" },
        "approval_policy": {
          "type": "string",
          "enum": ["untrusted", "on-request", "never"]
        }
      },
      "required": [
        "executor",
        "tool",
        "model",
        "reasoning_effort",
        "sandbox",
        "approval_policy"
      ],
      "additionalProperties": false
    },
    "test-runner": {
      "type": "object",
      "properties": {
        "executor": { "const": "codex" },
        "tool": {
          "type": "string",
          "pattern": "^mcp__[A-Za-z0-9_-]+__[A-Za-z0-9_-]+$"
        },
        "model": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$",
          "not": {
            "enum": [
              "inherit",
              "default",
              "haiku",
              "sonnet",
              "opus",
              "fable",
              "cheap",
              "cheap-or-standard",
              "standard",
              "most-capable"
            ]
          }
        },
        "reasoning_effort": {
          "type": "string",
          "enum": [
            "none",
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
            "max",
            "ultra"
          ]
        },
        "sandbox": {
          "type": "string",
          "enum": ["read-only", "workspace-write", "danger-full-access"]
        },
        "approval_policy": {
          "type": "string",
          "enum": ["untrusted", "on-request", "never"]
        }
      },
      "required": [
        "executor",
        "tool",
        "model",
        "reasoning_effort",
        "sandbox",
        "approval_policy"
      ],
      "additionalProperties": false
    }
  },
  "dependentRequired": { "worker": ["escalation", "escalation-final"] },
  "additionalProperties": false
}
```

`executor` is always the literal `codex`. `tool` is the fully qualified MCP tool name. `model` is
a concrete external-config model value, never a placeholder, inherited value, or Gambit tier
alias. `reasoning_effort` accepts exactly `none`, `minimal`, `low`, `medium`, `high`, `xhigh`,
`max`, or `ultra`; `approval_policy` accepts exactly `untrusted`, `on-request`, or `never`.
Worker `reply_tool` names the same Codex MCP server's `codex-reply` tool, and `service_tier` is a
concrete Codex configuration value such as `fast`. Worker, escalation, escalation-final, and
test-runner `sandbox` accept exactly `read-only`, `workspace-write`, or `danger-full-access`. Steelman and finder require
`web_search: "live"` and `sandbox: "read-only"`; scout and verifier require `sandbox:
"read-only"`. Worker, escalation, escalation-final, scout, verifier, and test-runner forbid `web_search`
through `additionalProperties: false`; their configured wires disable it explicitly.

## Validation and resolution

For every contracted execution role, use this deterministic sequence:

1. Missing registry file: use native execution.
2. JSON parse or duplicate-key failure: stop immediately. Reject duplicate JSON object keys before
   schema validation by parsing the existing file while preserving duplicate-key errors. A repeated
   role is therefore invalid rather than last-value-wins. Report the parsing error and do not
   dispatch the requested class.
3. Schema validation failure: stop immediately. Validate the entire parsed registry against the
   canonical schema. Unknown roles, unknown fields, missing fields, and invalid values invalidate
   the entire registry. Do not ignore an invalid unrequested entry. Report the validation error and
   do not dispatch the requested class.
4. When `worker` is present, split `worker.tool` and `worker.reply_tool` at their final `__`. Their
   complete prefixes before that separator must be byte-identical. A mismatch means the reply tool
   belongs to a different MCP server namespace: stop as an invalid whole registry before dispatch.
5. Valid registry, requested role absent: use native execution.
6. Valid registry, requested role present: select the configured Codex executor and invoke exactly
   its configured fully qualified MCP tool with its configured model, reasoning effort, sandbox,
   approval policy, and, when present, web-search value.
7. Configured Codex call fails: stop immediately. Preserve and report the call failure; do not retry
   natively.

Never infer executor selection from MCP tool availability. Availability cannot opt a role into
Codex and cannot repair an invalid registry. Never silently fall back from configured Codex to
native Claude. Missing configuration selects native execution; broken configured execution fails
closed.

Executor selection is independent of model-tier selection. Native execution resolves the class's
tier through [models.md](models.md). Configured Codex execution uses the concrete model stored in
this external registry. No provider-specific concrete model ID belongs in Gambit skills or
contracts.

## Configured scout wire

When a workflow resolves a configured `scout`, invoke `scout.tool` exactly once with this argument
object. The call is fresh: omit prior turns and `threadId`. Substitute only the absolute scout
contract path, bounded question, repository root, and validated registry values:

```json
{
  "prompt": "Your FIRST action is a bounded read-only `exec_command` inspection of the single exact absolute contract path named here. Use only bounded `cat`, `sed`, `nl`, or `rg` reads before doing anything else. Read <abs>/contracts/scout.md first and follow it exactly.\n\nQuestion: <bounded investigation question>",
  "model": "<scout.model>",
  "cwd": "<absolute repository root>",
  "sandbox": "read-only",
  "approval-policy": "<scout.approval_policy>",
  "developer-instructions": "You are a subordinate read-only scout. The only permitted local commands are bounded cat, sed, nl, or rg reads of the exact contract path and files rooted inside the assigned repository. All other commands and operations are forbidden, including network calls, tests, mutation, arbitrary absolute paths, orchestration, skills, and nested agents. Return only the contracted evidence report.",
  "config": {
    "model_reasoning_effort": "<scout.reasoning_effort>",
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

Require a supported response with non-empty string `threadId` and `content`; use `content` as the
scout report and discard `threadId`. Missing fields, non-string fields, empty output, tool errors,
or malformed responses are configured call failures. Never invoke `codex-reply`.

## Configured verifier wire

When review resolves a configured `verifier`, invoke `verifier.tool` exactly once per initial or
closure pass with this argument object. Each call is fresh: omit prior turns and `threadId`.

```json
{
  "prompt": "Your FIRST action is a bounded read-only `exec_command` inspection of the single exact absolute verifier-contract path named here. Use only bounded `cat`, `sed`, `nl`, or `rg` reads before doing anything else. Read <abs>/reviewers/verifier.md first and follow it exactly.\n\nmode: <initial or closure>\n<the exact frozen revisions, boundary, and candidate or open-ledger fields required by the review workflow>",
  "model": "<verifier.model>",
  "cwd": "<absolute review worktree>",
  "sandbox": "read-only",
  "approval-policy": "<verifier.approval_policy>",
  "developer-instructions": "You are a subordinate read-only verifier. Inspect only the supplied candidates, frozen boundary, exact verifier contract, and repository files needed to execute each verify_by step. Use only bounded cat, sed, nl, or rg reads. Do not mutate, run tests, browse the network, orchestrate, load skills, delegate, discover new review work, or add observations outside the supplied IDs. Return only the contract classifications.",
  "config": {
    "model_reasoning_effort": "<verifier.reasoning_effort>",
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

Require a supported response with non-empty string `threadId` and `content`; use `content` as the
verifier result and discard `threadId`. The result must satisfy the verifier contract for every
supplied ID. Missing or extra classifications, missing fields, non-string fields, empty output,
tool errors, or malformed responses are configured call failures. Never invoke `codex-reply`.

## Configured test-runner wire

When a skill resolves a configured `test-runner`, invoke `test-runner.tool` exactly once for the
requested command with this argument object. The call is fresh: omit prior turns and `threadId`.

```json
{
  "prompt": "Run exactly this verification command once from the configured working directory: <complete command>. Make no source edits. Report the command, exit code, pass/fail counts when available, and the relevant failure output exactly.",
  "model": "<test-runner.model>",
  "cwd": "<absolute repository or worktree root>",
  "sandbox": "<test-runner.sandbox>",
  "approval-policy": "<test-runner.approval_policy>",
  "developer-instructions": "You are a subordinate test runner. Run only the exact requested verification command once. Do not edit source files, repair failures, run additional commands, orchestrate, load skills, delegate, discover tasks, or expand scope. Generated build and test artifacts are permitted only when the command itself creates them. Return the exact verification result and relevant failure evidence.",
  "config": {
    "model_reasoning_effort": "<test-runner.reasoning_effort>",
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

Require a supported response with non-empty string `threadId` and `content`; use `content` as the
test report and discard `threadId`. The report must state the exact command and exit code; missing
or ambiguous command evidence, missing fields, non-string fields, empty output, tool errors, or
malformed responses are configured call failures. Never invoke `codex-reply`.
<!-- /gambit-backend -->
<!-- gambit-backend:codex -->
# Executor registry on native Codex

The external executor registry is a Claude-only executor registry and does not apply to native
Codex. Native Codex dispatch selects the contracted class and its documented built-in or custom
agent fallback directly; it neither reads nor emulates the Claude registry. Executor selection
never changes the class contract or its authority.
<!-- /gambit-backend -->
