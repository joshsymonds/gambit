# CLAUDE.md

Gambit provides structured development workflows as one directly maintained tree of skills and contracts.

**Installation:** `/plugin marketplace add joshsymonds/gambit && /plugin install gambit@gambit`

## Layout

```
skills/<name>/       # Skill prose, references, and scripts
contracts/           # Shared agent and model contracts
tests/               # Structural and behavioral checks
```

Edit files in `skills/<name>/` and `contracts/` directly. Run `just check` before committing.

**The tests pin structure and forbidden content, never phrasings.** `tests/` pins substrings from skill prose such as role and model profile resolution, agent versus model dispatch shape, and scout dispatch shape. Read the assertion before rewording guarded prose.

`just scan` runs the normative-prose scan.

## Releasing

`just release X.Y.Z` updates `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, runs `just check`, stages both manifests, and commits the version bump.

## Where things are owned

- `executing-plans` owns the orchestrator/implementer architecture.
- `contracts/README.md` owns the agent-class and role enum.
- `contracts/models.md` owns model profiles and roles. No concrete model ID belongs in any skill.

Test a skill by invoking it as a subagent before finalizing.
