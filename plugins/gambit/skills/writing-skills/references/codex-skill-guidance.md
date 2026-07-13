# Codex Skill Guidance

## Required shape

A skill is a directory containing `SKILL.md`. Its YAML frontmatter must include
only supported metadata; always provide a lowercase hyphen-case `name` and a
clear `description`. Put all trigger conditions in the description because
Codex decides whether to load the body from that metadata.

Keep the body imperative, focused, and under 500 lines. Move detailed schemas,
examples, and variant-specific instructions into one-level-deep `references/`.
Use `scripts/` for deterministic operations that would otherwise be rewritten
repeatedly. Use `assets/` only for resources copied into outputs.

## Discovery and invocation

Codex can invoke a skill explicitly through `$skill-name` or implicitly when
the prompt matches its description. Plugin skills are namespaced by their
plugin. Optional `agents/openai.yaml` controls display metadata, invocation
policy, and tool dependencies; do not put those fields into `SKILL.md`
frontmatter.

## Evaluation workflow

1. Define observable success and failure criteria.
2. Run a baseline task without the proposed skill change.
3. Make the smallest instruction change that closes the observed gap.
4. Pressure-test realistic rationalizations and conflicting constraints.
5. Test explicit and implicit triggering separately.
6. Validate generated frontmatter and bundled resource paths.
7. Re-run the task in a fresh Codex thread so prior context cannot mask gaps.

Keep evaluation artifacts raw: prompt, output, diff, commands, and logs. Do not
tell a test agent the expected answer or suspected loophole.
