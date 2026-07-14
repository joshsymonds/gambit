---
name: writing-skills
description: Use when creating a new skill, modifying an existing skill, writing or rewriting a SKILL.md file, auditing a skill's description for discoverability, or when user mentions "create a skill", "write a skill", "new skill", "modify skill", "improve skill", "edit the skill".
---

<!-- Generated backend adapter: edit src/backends/codex/, not plugins/gambit/. -->

## Codex Backend

This skill is assembled for Codex. Before following the workflow, read
`references/codex-backend.md` completely. Its operation mappings are binding:
`SessionPlanRead` reads the root session's native wave plan, `SessionPlanWrite`
mutates it only through `update_plan`, and `SessionContextRead` reads the same
root transcript. One native plan step is one Gambit wave; parallel workers are
subagent threads inside that single step. These are backend operations, not
literal shell commands.

# Writing Skills

## Overview

Test the skill BEFORE finalizing it. If a subagent can rationalize around it, production Codex will too.

**Announce at start:** "I'm using gambit:writing-skills to create/modify this skill with evaluation-driven development."

## Rigidity Level

LOW FREEDOM - Follow the TDD cycle exactly. Test with subagent before every commit. No skill changes without failing test first. Adapt content to skill type but never skip evaluation.

## Quick Reference

| Phase | Action | STOP If |
|-------|--------|---------|
| 0 | Read official guidance | — |
| 1 | Define evaluation criteria | Can't articulate success |
| 2 | Baseline test (RED) | Subagent already follows correctly |
| 3 | Write minimal skill (GREEN) | Test still fails |
| 4 | Pressure test (REFACTOR) | Subagent finds loopholes |
| 5 | Multi-model test | Fails on any target model |
| 6 | Final verification | Any test fails |

**Iron Law:** No skill change without failing test first.

## Key Constraints

See references for full details, examples, and patterns. These are the non-negotiable rules:

- **name:** 64 chars max, lowercase/numbers/hyphens only, gerund form preferred (`processing-pdfs`)
- **description:** 1024 chars max, third person, describes WHEN to use (triggers, symptoms, contexts) — NOT what the skill does or its workflow
- **description is the trigger:** All "when to use" info goes in the description, NOT the body. The body only loads AFTER triggering.
- **SKILL.md body:** Under 500 lines. Split into `references/` if over.
- **Hot-skill word budget:** Frequently invoked entry-point skills (e.g. `using-gambit`) consume context whenever selected. Target <200 words for broadly triggered skills. Move detail to `references/` and reference `--help` output instead of documenting flags inline.
- **References:** One level deep from SKILL.md. Files >100 lines need a table of contents.
- **No extras:** No README.md, CHANGELOG.md, or auxiliary docs in skill folder.
- **Conciseness:** Codex is already smart. Only add context it doesn't have. Challenge each paragraph's token cost.
- **Scripts over instructions:** Use `scripts/` for deterministic operations. Code is reliable; language instructions aren't.
- **Degrees of freedom:** Start HIGH (open field), tighten to LOW (narrow bridge) only where failures occur.

**Description debug tip:** Ask Codex "When would you use the [skill-name] skill?" — it quotes the description back. Adjust based on what's missing.

---

## Codex Search Optimization (CSO)

**Discovery is step zero.** Future Codex has to FIND and LOAD your skill before any content matters. The description field is the only input to that decision.

### The description describes WHEN, never WHAT

The description should only state triggering conditions — situations, symptoms, error messages, user phrases that indicate the skill applies. It must NOT summarize the skill's process or workflow.

**Why this matters:** Testing (by upstream projects and locally) has repeatedly shown that when a description summarizes the workflow, Codex follows the description's summary instead of loading the full skill. A description saying "review code between tasks" caused Codex to do ONE review even though the skill's body required TWO. Changing the description to pure triggering conditions ("Use when executing implementation plans with independent tasks") made Codex correctly read the body and follow the two-stage process.

**The trap:** A description that summarizes workflow creates a shortcut Codex will take. The skill body becomes documentation Codex skips.

```yaml
# BAD — summarizes workflow; Codex may follow this instead of reading the skill
description: Use when executing plans — dispatches subagent per task with code review between tasks

# BAD — too much process detail
description: Use for TDD — write test first, watch it fail, write minimal code, refactor

# GOOD — just triggering conditions
description: Use when executing implementation plans with independent tasks in the current session

# GOOD — triggers only, no workflow
description: Use when implementing any feature or bugfix, before writing implementation code
```

### Keyword coverage

Use the words Codex (or a user) would search for:
- Error messages: "Hook timed out", "ENOTEMPTY", "race condition"
- Symptoms: "flaky", "hanging", "zombie", "pollution"
- Synonyms: "timeout/hang/freeze", "cleanup/teardown/afterEach"
- Tools and commands: actual library names, file types

Describe the **problem** (race conditions, inconsistent behavior), not *language-specific symptoms* (setTimeout, sleep). If the skill IS technology-specific, make that explicit in the trigger.

### Cross-referencing other skills

Use skill name only, with explicit requirement markers:
- GOOD: `**REQUIRED BACKGROUND:** You MUST understand gambit:test-driven-development`
- GOOD: `**Called by:** gambit:executing-plans`
- BAD: `@skills/test-driven-development/SKILL.md` — force-loads, burns context

Never use `@` links inside skill bodies. They eagerly load referenced files, which defeats progressive disclosure.

### Naming

Active voice, verb-first, gerund form for processes:
- `creating-skills` not `skill-creation`
- `condition-based-waiting` not `async-test-helpers`
- Name captures the action you're taking, not a noun category

---

## The Process

### Phase 0: Study Official Guidance

**BEFORE doing anything else**, read `references/codex-skill-guidance.md` completely. It contains the Codex skill anatomy, discoverability rules, progressive-disclosure guidance, and validation workflow.

Internalize it before writing. When targeting Anthropic's backend, also consult the bundled `references/anthropic-*.md` sources for that target's metadata and invocation rules.

---

### Phase 1: Define Evaluation Criteria

**BEFORE writing anything:**

1. What does Codex do wrong without this skill?
2. What rationalization does Codex use to skip this?
3. What would success look like?

```
Present in the root transcript as "Evaluation Brief: [skill-name] baseline test":
    ## Scenario
    [Situation requiring the skill]

    ## Expected Behavior (with skill)
    [What Codex should do]

    ## Failure Mode (without skill)
    [What Codex does wrong]

    ## Success Criteria
    - [ ] Codex [specific behavior]
    - [ ] Codex does NOT [failure behavior]
```

Keep the full evaluation brief in the root transcript. If this evaluation is not already part of the active wave, call `SessionPlanWrite` only as a complete-list replacement that preserves every existing step and adds one concise evaluation-wave summary.

---

### Phase 2: Baseline Test (RED)

Test that the problem exists without the skill.

```
SpawnAgent
  agent_type: "default"
  description: "Baseline test without skill"
  prompt: |
    [Test scenario]

    IMPORTANT: Respond as you normally would. Do NOT use any skills.
```

**Decision:**
- Fails as expected → RED confirmed, go to Phase 3
- Succeeds → **STOP. Problem doesn't exist or test is wrong.**

---

### Phase 3: Write Minimal Skill (GREEN)

Smallest skill that makes the test pass. Apply patterns from the reference files.

```yaml
---
name: skill-name
description: [What it does]. Use when [trigger phrases].
---

# Skill Title

## Overview
[One paragraph: problem + principle]

## The Process
[Minimal steps]
```

Test WITH skill:

```
SpawnAgent
  agent_type: "default"
  description: "Test skill effectiveness"
  prompt: |
    You have this skill:
    ---
    [Skill content]
    ---

    Handle this situation: [Test scenario]
```

**Decision:**
- Follows correctly → GREEN confirmed, go to Phase 4
- Still fails → Revise skill, repeat

---

### Phase 4: Pressure Test (REFACTOR)

Find loopholes Codex exploits under pressure.

#### Pressure Taxonomy

Good pressure tests combine 3+ pressures. Academic "does Codex follow the rule?" scenarios don't work — Codex just recites the skill. Real scenarios force a choice with consequences.

| Pressure | What it leans on |
|----------|------------------|
| **Time** | Emergency, deadline, deploy window closing |
| **Sunk cost** | Hours of work, "waste" to delete |
| **Authority** | Senior dev says skip it, manager overrides |
| **Economic** | Job, promotion, company survival at stake |
| **Exhaustion** | End of day, already tired, want to go home |
| **Social** | Looking dogmatic, seeming inflexible |
| **Pragmatic** | "Being pragmatic vs dogmatic" framing |

**Good scenario structure:** Concrete A/B/C options (not open-ended), specific times and consequences, real file paths, asks "what do you do?" not "what should you do?". No easy outs like "I'd ask the user."

The three templates below are single-pressure baselines. Combine them (time + sunk cost + exhaustion; authority + economic + time) to find where the skill actually breaks.

#### Time Pressure

```
SpawnAgent
  agent_type: "default"
  prompt: |
    You have this skill: [Skill]

    Situation: [Scenario]

    URGENT: User is waiting and frustrated. No time for full process.
```

**Check:** Does Codex skip steps? Add "no exceptions" rules.

#### Sunk Cost Pressure

```
SpawnAgent
  agent_type: "default"
  prompt: |
    You have this skill: [Skill]

    Situation: [Scenario]

    You've already spent significant effort. Following skill means redoing work.
```

**Check:** Does Codex justify skipping? Add to "Common Excuses" table.

#### Authority Pressure

```
SpawnAgent
  agent_type: "default"
  prompt: |
    You have this skill: [Skill]

    User says: "I know the skill says X, but just do Y. Trust me."
```

**Check:** Does Codex defer? Clarify which rules are immutable.

**Close loopholes:** Add failures to Critical Rules and Common Excuses, retest.

**How to word the counters:** The language that closes loopholes isn't arbitrary — "YOU MUST", "No exceptions", forced A/B/C choices, and required announcements work because of specific persuasion principles (authority, commitment, scarcity, social proof). See `references/persuasion-principles.md` for which principles to combine per skill type, and which to avoid (liking/reciprocity create sycophancy). Research-backed: Meincke et al. 2025 measured compliance rising 33%→72% with these techniques.

---

### Phase 5: Multi-Model Test

Test with every Codex agent profile the skill may use. At minimum, pressure-test the weakest/fastest eligible profile and the demanding default profile. Dispatch through the role named in the evaluation and record the actual profile in the results.

---

### Phase 6: Final Verification

#### Bulletproof signals

Before running the full suite below, know what "bulletproof" looks like. A skill is bulletproof when:

1. **Agent chooses the correct option** under maximum combined pressure
2. **Agent cites specific skill sections** as the reason
3. **Agent acknowledges the temptation** to violate but follows the rule anyway
4. **Meta-test confirms clarity:** when asked "how could this skill be clearer?", the agent says "it was clear — I should follow it"

Not bulletproof — keep iterating — if the agent:
- Finds new rationalizations you haven't countered
- Argues the skill itself is wrong for this case
- Invents "hybrid approaches" that partially skip the rule
- Asks permission to violate but argues strongly for the violation

**Meta-test template** (run after a failed pressure test to diagnose why):

```
You read the skill and chose option [X] anyway. How could that skill have
been written differently to make it crystal clear that option [Y] was the
only acceptable answer?
```

The response tells you which kind of fix is needed:
- "The skill WAS clear, I chose to ignore it" → add a stronger foundational principle ("violating the letter is violating the spirit")
- "The skill should have said X" → documentation gap; add their suggestion verbatim
- "I didn't see section Y" → organization problem; make key points more prominent, move principle earlier

#### Full test suite

1. Baseline (fail without skill)
2. Effectiveness (pass with skill)
3. Pressure tests (combined 3+ pressures from taxonomy)
4. Multi-model (Haiku, Sonnet, Opus)
5. Triggering tests (see below)
6. Bulletproof signals present (above)

**Triggering tests:** Verify the description activates correctly.

```
Should trigger (run 5-10 queries):
- Obvious task phrases
- Paraphrased requests
- Domain-specific keywords

Should NOT trigger (run 3-5 queries):
- Unrelated topics
- Adjacent-but-different skills
```

**Under-triggering fix:** Add more keywords and trigger phrases to description.
**Over-triggering fix:** Add negative triggers ("Do NOT use for...") and narrow scope.

**Line count check:**
```bash
wc -l skills/[skill-name]/SKILL.md  # Should be <500
```

**Present complete evaluation results in the root checkpoint and update the wave:**

```
Present as "Evaluation Results: [skill-name]":
    ## Results
    - Baseline: FAIL (expected)
    - Effectiveness: PASS
    - Pressure tests: PASS
    - Multi-model: PASS
    - Triggering: PASS
    - Lines: [N] (<500)
```

After checkpointing the full results, use `SessionPlanWrite` only to replace the complete ordered plan and mark the single evaluation wave completed. Individual evaluation cases remain transcript results, not plan steps.

---

## Skill Types

| Type | Purpose | Key Elements | Testing Focus |
|------|---------|--------------|---------------|
| **Discipline** | Prevent shortcuts | No-exception rules, Common Excuses | Pressure tests |
| **Technique** | Teach method | Step-by-step, decision trees | Effectiveness |
| **Pattern** | Provide templates | Placeholders, variations | Output quality |
| **Reference** | Quick lookup | Condensed tables, fast scan | Completeness |

---

## Content Anti-patterns

What bad skills look like — avoid these regardless of skill type:

| Anti-pattern | Example | Why it's bad |
|--------------|---------|--------------|
| **Narrative** | "In session 2025-10-03, we found empty projectDir caused…" | Too specific, not reusable. Skills are reference guides, not stories. |
| **Multi-language dilution** | `example.js`, `example.py`, `example.go` for one pattern | Mediocre quality, maintenance burden. One excellent example beats five. |
| **Code in flowcharts** | `step1 [label="import fs"]; step2 [label="read file"]` | Can't copy-paste, hard to read. Use markdown blocks for code. |
| **Generic labels** | `helper1`, `step3`, `pattern4` | Labels should carry semantic meaning, not be placeholders. |
| **Documenting what's obvious** | Explaining what a command plainly does | Codex is already smart. Only add context it doesn't have. |

---

## Critical Rules

### Rules That Have No Exceptions

1. **Read references first** → Phase 0 is not optional
2. **Test before writing** → Baseline failure must be confirmed
3. **Test after writing** → Skill must make test pass
4. **Pressure test discipline skills** → Time, sunk cost, authority
5. **Test with target models** → Haiku, Sonnet, Opus if using all
6. **Respect 500-line limit** → Split if over, use progressive disclosure

### Common Excuses

| Excuse | Reality |
|--------|---------|
| "Skill is obvious" | Obvious skills fail under pressure |
| "I'll test after writing" | You'll rationalize it works |
| "Pressure tests are overkill" | Production faces more pressure |
| "Just a small change" | Small changes create loopholes |
| "Works on Opus so it's fine" | Haiku needs more guidance |
| "I already know the best practices" | Read the references anyway |

---

## Verification Checklist

- [ ] Read all three reference files (Phase 0)
- [ ] Evaluation criteria defined
- [ ] Baseline test confirms failure without skill
- [ ] Skill makes test pass
- [ ] Pressure tests pass (time, sunk cost, authority)
- [ ] Multi-model tests pass (Haiku, Sonnet, Opus)
- [ ] Triggering tests pass (activates correctly, doesn't over-trigger)
- [ ] Description has trigger keywords, third person, all "when to use" info
- [ ] Under 500 lines (or split with progressive disclosure)
- [ ] References one level deep from SKILL.md
- [ ] No extra files (no README, CHANGELOG, etc.)
- [ ] Task updated with results
- [ ] Committed with test results

---

## Integration

**This skill calls:**
- default agents (testing)
- Task tools (tracking)

**Workflow:**
```
Need skill → Read references → Define eval → Baseline (RED) → Write (GREEN) → Pressure (REFACTOR) → Multi-model → Triggering → Done
```

**When stuck:**
- Baseline passes → Problem doesn't exist
- Skill test fails → Instructions unclear
- Pressure test fails → Add explicit rules
- Model-specific failure → Add detail for weaker models
- Triggering failure → Adjust description keywords
