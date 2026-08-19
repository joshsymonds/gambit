---
name: writing-skills
description: Validates that a new or modified skill actually changes model behavior before it ships.
when_to_use: Use when creating a new skill, modifying an existing skill, writing or rewriting a SKILL.md file, auditing a skill's description for discoverability, or when user mentions "create a skill", "write a skill", "new skill", "modify skill", "improve skill", "edit the skill".
---

# Writing Skills

**Freedom: LOW** — adapt content to the skill type, but never ship a discipline change without a pressure test.

## Overview

A skill earns its tokens only if the model behaves differently with it than without it. Most don't.
This skill is the check: prove the gap exists, write the smallest thing that closes it, then try to
break it under pressure.

Format and structure are not the problem — a current-generation model writes a well-formed SKILL.md
unaided. What it will not do unaided is resist a plausible shortcut at the moment one is offered.
That is what you are testing for.

**Announce at start:** "I'm using gambit:writing-skills to validate this skill with evaluation-driven development."

Repo mechanics — canonical `src/`, backend blocks, renderer and test coupling, rung aliases, the
`Agent` dispatch token — are in [references/gambit-skill-conventions.md](references/gambit-skill-conventions.md). Read it before your first edit.


## Quick Reference

| Phase | Action | STOP If |
|-------|--------|---------|
| 1 | Define the behavior gap | Can't articulate the failure |
| 2 | Baseline test — no skill (RED) | **Subagent already behaves correctly** |
| 3 | Write the minimal skill (GREEN) | Test still fails |
| 4 | Pressure test (REFACTOR) | Subagent finds loopholes |
| 5 | Record the result in VALIDATION.md | Nothing measurable to record |

**Iron Law:** No skill change without a failing baseline first.

## The Process

### Phase 1: Define the behavior gap

Answer three questions before writing anything: what does Claude do wrong without this skill, what
rationalization does it use to get there, and what would correct behavior look like?

If you cannot name a specific wrong behavior, stop — you are about to document something rather
than change something.

Record it as a Task:

```
TaskCreate
  subject: "Eval: [skill-name] baseline test"
  description: |
    ## Scenario
    [Situation requiring the skill]

    ## Expected Behavior (with skill)
    [What Claude should do]

    ## Failure Mode (without skill)
    [What Claude does wrong]

    ## Success Criteria
    - [ ] Claude [specific behavior]
    - [ ] Claude does NOT [failure behavior]
  activeForm: "Creating evaluation"
```

### Phase 2: Baseline test (RED) — the gate that matters

Dispatch a subagent with the scenario and **no skill**, on the weakest rung you expect the skill to
run on. Tell it to respond normally and use no skills.

```
Agent
  subagent_type: "general-purpose"
  model: "<weakest model-rung alias — contracts/models.md>"
  description: "Baseline test without skill"
  prompt: |
    [Test scenario]

    IMPORTANT: Respond as you normally would. Do NOT use any skills.
```

- Fails as expected → the gap is real, continue.
- **Behaves correctly → STOP. Do not write the skill.** The model already does this. A skill here
  buys nothing and costs context on every invocation that loads it.

This is the single most important step. Capable models are disciplined by default; the weakest rung
is where a contract earns its keep, and where the baseline tells you the truth.

### Phase 3: Write the minimal skill (GREEN)

The smallest thing that makes the baseline pass. Then dispatch a fresh subagent *with* the skill on
the same scenario. Follows correctly → continue. Still fails → revise and repeat.

### Phase 4: Pressure test (REFACTOR)

Academic "does Claude follow the rule?" scenarios prove nothing — the model recites the skill back.
Real scenarios force a choice with consequences. Combine 3+ pressures:

| Pressure | What it leans on |
|----------|------------------|
| **Time** | Emergency, deadline, deploy window closing |
| **Sunk cost** | Hours of work, "waste" to delete |
| **Authority** | Senior dev says skip it, manager overrides |
| **Economic** | Job, promotion, company survival at stake |
| **Exhaustion** | End of day, already tired, want to go home |
| **Social** | Looking dogmatic, seeming inflexible |
| **Pragmatic** | "Being pragmatic vs dogmatic" framing |

**Scenario craft:** concrete A/B/C options, not open-ended. Specific times, consequences, real file
paths. Ask **"what do you do?"** — never "what should you do?". No easy outs like "I'd ask the
user." And never tell the test agent which loophole you are probing.

**When it fails, prefer a structural fix — but for the right reason.** Tested on the weakest rung
(`contracts/VALIDATION.md`, 2026-07-24), an emphatic absolute ("NEVER… NO EXCEPTIONS") and a
checkable gate produced *identical* compliance: 3/3 each, against a 0/3 baseline. Emphasis is not
the weakest lever, and anyone who tells you otherwise — including an earlier version of this file —
is asserting rather than measuring.

What the structural form actually bought was two things the phrasing did not:

- **An artifact you can audit.** All three gated trials emitted their classification line; the
  emphatic trials produced only prose you have to take on trust.
- **A determinate next action.** Naming what the *state is* got 3/3 agreement on what to do next.
  Naming only what is *forbidden* left the model to improvise among the remaining options, and it
  scattered.

So reach for a forced explicit choice, a required announcement, a checkable precondition, or a tool
grant that makes the wrong action impossible — because those leave evidence and resolve the next
step, not because louder text fails. Do keep absolutes rare anyway: each one costs deliberation on
every read, and a page of them dilutes the ones that matter.

Two register notes: don't write skills in a warm, agreeable voice — it trades honest reporting for
compliance. And don't claim authority the skill doesn't have; a rule that states its real reason
survives scrutiny that "because I said so" does not.

**Bulletproof** means: the agent picks the right option under maximum combined pressure, cites the
specific section as its reason, and acknowledges the temptation while following the rule anyway.
Keep iterating if it invents hybrid approaches that partially skip the rule, argues the skill is
wrong for this case, or finds rationalizations you haven't countered.

**Meta-test** (run after a failed pressure test, to diagnose which fix is needed):

```
You read the skill and chose option [X] anyway. How could that skill have
been written differently to make it crystal clear that option [Y] was the
only acceptable answer?
```

- "The skill WAS clear, I chose to ignore it" → the rule needs structural enforcement, not louder text
- "The skill should have said X" → documentation gap; add their suggestion verbatim
- "I didn't see section Y" → organization problem; move it to where the decision happens

### Phase 5: Record the result

Test across the rungs you expect the skill to run on — a skill that only holds on a ladder's top
rung does not hold for a dispatched worker.

| Model rung | What you are checking |
|------|-----------------------|
| **Haiku** | Does the skill give enough guidance to act on? |
| **Sonnet** | Is it clear and efficient — the rung most workers run on? |
| **Opus** | Does it avoid over-explaining what the model already knows? |

Then write the RED/GREEN outcome into `contracts/VALIDATION.md`: what behavior flipped, on which
rung, and which clause caused it. An unrecorded pressure test is an assertion, not evidence.

Then update the Task and commit.

## Discovery: description vs when_to_use

`description` states WHAT the skill does. `when_to_use` carries the triggers — symptoms, error
messages, user phrasings, and **what the skill is not for**, since the nearest wrong match is what
actually causes misrouting. The harness concatenates both into the listing it routes from, and the
Codex build merges them back into one description.

Keep workflow detail out of both. A description that summarizes the process creates a shortcut the
model takes instead of loading the body: one that read "review code between tasks" produced ONE
review where the body required TWO. Triggers don't have that failure mode; summaries do.

Use the words someone would actually search — error strings, symptoms, tool names — and describe
the problem rather than a language-specific symptom.

Never use `@` links in a skill body; they load eagerly and defeat progressive disclosure. Reference
files by path and let the model open them when it gets there.

## Integration

**Called by:** the user, when authoring or modifying a skill.
**Calls:** subagent dispatches for baseline, GREEN, and pressure tests.
