# External executor registry

Claude-backed Gambit may override the native executor for exactly three contracted classes by
reading `~/.claude/gambit/executors.json`. The registry is optional. It selects an executor only;
the class contract, authority, model tier, and workflow semantics remain unchanged.

Only `steelman`, `worker`, and `finder` may be configured. `scout`, `test-runner`, `escalation`, and
`verifier` always use native execution.

## Canonical schema

The file is one JSON object whose keys are roles. Each role is optional, so any subset of the three
allowed roles is valid. Validate the complete object against this schema, not merely the requested
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
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$"
        },
        "sandbox": { "const": "read-only" },
        "approval_policy": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$"
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
    "worker": {
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
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$"
        },
        "sandbox": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$"
        },
        "approval_policy": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$"
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
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$"
        },
        "sandbox": { "const": "read-only" },
        "approval_policy": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?!.*[<>])\\S+$"
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
    }
  },
  "additionalProperties": false
}
```

`executor` is always the literal `codex`. `tool` is the fully qualified MCP tool name. `model` is
a concrete external-config model value, never a placeholder, inherited value, or Gambit tier
alias. `reasoning_effort`, `sandbox`, and `approval_policy` are concrete external-executor values.
Steelman and finder require `web_search: "live"` and
`sandbox: "read-only"`; worker forbids `web_search` through `additionalProperties: false`.

## Validation and resolution

For `scout`, `test-runner`, `escalation`, or `verifier`, select native execution without reading the
registry. For `steelman`, `worker`, or `finder`, use this deterministic sequence:

1. Missing registry file: use native execution.
2. JSON parse or duplicate-key failure: stop immediately. Reject duplicate JSON object keys before
   schema validation by parsing the existing file while preserving duplicate-key errors. A repeated
   role is therefore invalid rather than last-value-wins. Report the parsing error and do not
   dispatch the requested class.
3. Schema validation failure: stop immediately. Validate the entire parsed registry against the
   canonical schema. Unknown roles, unknown fields, missing fields, and invalid values invalidate
   the entire registry. Do not ignore an invalid unrequested entry. Report the validation error and
   do not dispatch the requested class.
4. Valid registry, requested role absent: use native execution.
5. Valid registry, requested role present: select the configured Codex executor and invoke exactly
   its configured fully qualified MCP tool with its configured model, reasoning effort, sandbox,
   approval policy, and, when present, web-search value.
6. Configured Codex call fails: stop immediately. Preserve and report the call failure; do not retry
   natively.

Never infer executor selection from MCP tool availability. Availability cannot opt a role into
Codex and cannot repair an invalid registry. Never silently fall back from configured Codex to
native Claude. Missing configuration selects native execution; broken configured execution fails
closed.

Executor selection is independent of model-tier selection. Native execution resolves the class's
tier through [models.md](models.md). Configured Codex execution uses the concrete model stored in
this external registry. No provider-specific concrete model ID belongs in Gambit skills or
contracts.
