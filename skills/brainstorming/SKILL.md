---
name: brainstorming
description: Use when user has a new feature idea, rough concept, or unexplored approach. Include when planning before code, breaking a design into tasks, creating an implementation plan, laying out tasks and dependencies, exploring architectural options, or requirements are vague. User phrases like "I want to build X", "should we do this", "let's think through Y", "explore approaches", "break this into tasks", "make an implementation plan". Do NOT use for executing existing plans, fixing bugs, refactoring, or when requirements and an epic already exist.
user_invokable: true
---

# Brainstorming Ideas Into Designs

## Overview

Turn rough ideas into validated designs stored as epic Tasks with immutable requirements. Tasks are created iteratively as you learn, not upfront.

**Core principle:** Ask questions to understand, research before proposing, document decisions for future reference.

**Announce at start:** "I'm using gambit:brainstorming to refine your idea into a design."

## Rigidity Level

HIGH FREEDOM - Adapt questioning to context. But always:
- Create immutable epic before code
- Create only the first wave — independently pluckable tasks, never the full tree
- Ask every question in prose with context and a recommendation — never the AskUserQuestion tool
- Apply task refinement before handoff

## Quick Reference

| Step | Action | Deliverable |
|------|--------|-------------|
| 1 | Scope-check, then ask clarifying questions | Right granularity + understanding |
| 2 | Research codebase and patterns | Existing approaches |
| 3 | Propose 2-3 approaches | Recommended option |
| 4 | Present design (isolated units, YAGNI) | Validated architecture |
| 5 | Create epic Task | Immutable requirements + anti-patterns |
| 6 | Create first wave (pluckable tasks only) | Ready for execution |
| 7 | Apply task refinement | Corner cases covered |
| 8 | Confirm immutable requirements with user | Contract locked |
| 9 | Ask next step, invoke skill | Chain continues automatically |

**Key:** Epic = contract (immutable), Tasks = adaptive (created as you learn)

<HARD-GATE>
Do NOT write any code, invoke any implementation skill, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY idea regardless of perceived simplicity. No exceptions.
</HARD-GATE>

## When to Use

- User describes a new feature to implement
- User has a rough idea that needs refinement
- About to write code without clear requirements
- Need to explore approaches before committing

**Don't use for:**
- Executing existing plans (use `gambit:executing-plans`)
- Starting a bug with no root cause yet (investigate with `gambit:debugging` first — it hands the root cause back here to design the fix)
- Refactoring (use `gambit:refactoring`)
- Requirements already crystal clear and epic exists

## The Process

### 1. Understand the Idea

**Research existing context first:**

```
Task
  subagent_type: "Explore"          # the read-only scout class
  model: "<scout tier — default cheap-or-standard; contracts/models.md>"   # resolve <abs> via Glob **/contracts/scout.md
  prompt: "Read <abs>/contracts/scout.md first (your binding scout contract), then: Find existing [relevant] implementation patterns in this codebase. Report with file:line evidence; say NOT FOUND if absent."
```

**Check scope before refining.** If the request spans multiple independent subsystems (e.g., "a platform with chat, billing, and analytics"), STOP and decompose before asking detail questions — don't refine something that should be several epics. Identify the independent pieces, how they relate, and what order to build them. Then brainstorm the FIRST piece through the normal flow; each piece gets its own epic → tasks cycle. Refining an over-large project wastes questions and produces a brittle epic.

**Then ask clarifying questions in prose. Never use the AskUserQuestion tool — in this step or anywhere else in this skill.**

Aim for 2-4 questions per round, 2-4 rounds total. Every question carries its own context: why you're asking, what the realistic options are, and which one you recommend and why. A bare question with no setup arrives confusing — the reader shouldn't have to reconstruct what prompted it. Stop when you understand scope, constraints, existing patterns, and scale.

```
Two things before I propose an approach:

**Token storage.** The OAuth tokens have to live somewhere the browser sends
them from. httpOnly cookies block XSS token theft and are the industry default;
sessionStorage clears on tab close but any injected script can read it. I'd go
httpOnly cookies unless you need the token client-side. Which fits?

**Scale.** [context → options → recommendation → question]
```

**Why prose, not the question widget.** The widget strips the context that makes a question answerable: compressed option labels can't carry the trade-off, and the question lands without the reasoning that prompted it. Prose keeps the question, its context, and your recommendation together — and it works in every environment. This applies to every question in this skill, closed or open, including the handoff menu.

---

### 2. Explore Approaches

**Research before proposing:**
- Existing pattern in codebase → Explore agent
- New integration → WebSearch or WebFetch
- No results → Ask user for direction

**Propose 2-3 approaches:**
- Lead with your recommendation and why
- Include pros/cons for each
- Reference codebase consistency as a factor

```
Based on [research findings], I recommend:

1. **[Approach A]** (recommended)
   - Pros: [benefits, especially "matches existing pattern"]
   - Cons: [drawbacks]

2. **[Approach B]**
   - Pros: [benefits]
   - Cons: [drawbacks]

I recommend option 1 because [specific reason].
```

---

### 3. Present the Design

Once approach is chosen, present in digestible sections. Ask "Does this look right?" after each. Cover: architecture, components, data flow, error handling, testing.

**Decompose for isolation.** Break the system into units that each have one clear purpose, communicate through well-defined interfaces, and can be understood and tested independently. For each unit, you should be able to say what it does, how to use it, and what it depends on — without reading its internals. If you can't change a unit's internals without breaking its consumers, the boundaries are wrong; rework them before locking the epic.

**Apply YAGNI ruthlessly.** Cut every feature, abstraction, and "we might want this later" the stated requirements don't demand. Unbuilt scope is the cheapest scope to remove — if the user wants it, they'll say so when you present.

---

### 4. Create the Epic Task

After design is validated, create epic as immutable contract. See [TEMPLATES.md](TEMPLATES.md) for the full template with all sections.

**Required epic sections:**

| Section | Purpose |
|---------|---------|
| Requirements (IMMUTABLE) | Specific, testable conditions that must be true |
| Success Criteria | Objective, checkable items including "all tests passing" |
| Anti-Patterns (FORBIDDEN) | Explicitly forbidden patterns with reasoning |
| Quality Bar | gambit's fixed maximal standard for "good code" — the highest professional quality, written verbatim into every epic and judged against each diff by reviewers and the orchestrator at every checkpoint, beyond the objective Success Criteria |
| Approach | 2-3 paragraph summary of chosen approach |
| Approaches Considered | Rejected alternatives with DO NOT REVISIT conditions |

**The Quality Bar is fixed — write it verbatim, don't elicit it.** Every epic carries the same bar: the highest professional standard, the code a master engineer would ship — elegant, complete, built on a superb foundation. It is not a per-project preference and is never negotiated down. Copy it verbatim from [TEMPLATES.md](TEMPLATES.md) into the epic so the checkpoint gate and reviewers have it locally. It governs *craftsmanship, not scope* — how well the required work is built, never how much of it; project-specific prohibitions go in Anti-Patterns. It sits on top of the mechanical floor the worker contract enforces (no suppression, no weakened tests, no dead code).

```
TaskCreate
  subject: "Epic: [Feature Name]"
  description: |
    ## Requirements (IMMUTABLE)
    - Requirement 1: [concrete, testable]

    ## Success Criteria (MUST ALL BE TRUE)
    - [ ] [objective criterion]
    - [ ] All tests passing

    ## Anti-Patterns (FORBIDDEN)
    - NO [pattern] (reason: [why])

    ## Quality Bar
    The highest professional standard — code a master engineer would ship: elegant, complete,
    built on a superb foundation. Fixed for every epic; copy it verbatim from TEMPLATES.md.

    ## Approach
    [2-3 paragraph summary]

    ## Approaches Considered
    ### [Rejected Approach] - REJECTED
    REJECTED BECAUSE: [reason]
    DO NOT REVISIT UNLESS: [condition]
  activeForm: "Planning [feature name]"
```

**Anti-patterns prevent requirement erosion.** When implementation gets hard, there's pressure to water down requirements. Explicit forbidden patterns with reasoning prevent this.

---

### 5. Create the First Wave

Author every task that is **independently pluckable from the current codebase**: its brief can be written entirely from code that exists right now — exact file set, cited anchors, testable criteria — with no placeholder for another task's output, and its file set is disjoint from the others'. Often that's one task; when the design genuinely starts in parallel pieces, it's several. Never a full tree — everything whose spec depends on what execution will teach stays unauthored, created by executing-plans as you learn. Don't manufacture disjointness by splitting one behavior across a file boundary.

**Do NOT set first-wave tasks as blocked by the epic.** The epic is a documentation container for immutable requirements, not a workflow prerequisite. The Task API's `blockedBy` means "cannot start until the blocker completes" — since the epic only completes after all subtasks do, marking a subtask as blocked by the epic creates a deadlock. Subtasks are only blocked by other subtasks.

```
TaskCreate
  subject: "Add [specific deliverable]"
  description: |
    ## Goal
    [One clear outcome]

    ## Implementation
    1. Study existing code: [file.ts:line]
    2. Write tests first (TDD)
    3. Implementation:
       - [ ] file.ts - function() - [what it does]

    ## Success Criteria
    - [ ] [specific measurable outcome]
    - [ ] Tests passing
    - [ ] Pre-commit hooks passing
  activeForm: "Adding [deliverable]"
```

**Why so few?** Later tasks reflect learnings from execution. Upfront task trees become brittle when assumptions change.

---

### 6. Apply Task Refinement

Before handoff, verify each first-wave task passes these checks:

1. **Scoped:** One focused sitting (~15-45 min). If it sprawls past that, break it down.
2. **Self-contained:** Can execute without asking questions
3. **Explicit:** All file paths specified
4. **Testable:** At least 3 success criteria

**Corner cases to check:**
- What if the happy path fails?
- Edge case inputs? Empty/null/missing data?
- Network/IO failures? Concurrent access?
- Security implications? Boundary conditions?

Update the task with any missing details before proceeding.

#### Epic + first-task self-review

Before announcing the plan to the user, run an inline self-review across the epic AND the first task. This takes 30 seconds and catches the same class of defects a subagent review pass would — immutable requirements that are actually vague, scope that silently expanded, contradictions between the epic's approach and the first task's implementation steps.

Scan for:
- **Placeholders:** Any `TBD`, `TODO`, `FIXME`, `XXX`, `[details above]`, "see requirements", `<angle-bracket-placeholder>`, or sentence that trails off without committing to a specific behavior
- **Vague requirements:** "properly handle errors", "good performance", "secure authentication", "similar to X" — requirements that can't be tested objectively must be rewritten with concrete, checkable conditions (or moved to a subtask's implementation notes)
- **Scope drift:** Does the first task introduce files, behaviors, or dependencies the epic's requirements don't justify? Either tighten the task or add the requirement to the epic explicitly.
- **Ambiguity:** Any sentence where two readers could reach different implementations. Pick one and say it.
- **Internal consistency:** The first task's files, function names, and success criteria should match the epic's stated approach. Mismatches mean one of them is wrong.
- **Quality Bar present:** Does the epic carry the fixed Quality Bar verbatim from [TEMPLATES.md](TEMPLATES.md), unweakened? It's the same standard on every epic — restore it if it's missing, paraphrased, or watered down.

Fix what you find by updating the epic or first task with `TaskUpdate`, then proceed. Do NOT present a plan that has items on this list.

#### Confirm the contract with the user

Epic requirements are IMMUTABLE once execution starts — so the user reviews them BEFORE handoff, not after. Present the epic's Requirements, Success Criteria, and Anti-Patterns for confirmation; the Quality Bar is gambit's fixed standard and applies to every epic, so note it rather than asking the user to set it:

> "Here's the epic contract — these requirements lock once we start: [summary]. Good to lock, or change anything first?"

If they request changes, update the epic and re-run the self-review. Only proceed to handoff once they confirm.

---

### 7. Handoff

**Offer next steps in prose (not AskUserQuestion), then invoke the chosen skill directly.**

> "Epic and first task are ready. I'd start executing now — gambit:executing-plans opens a fresh worktree for the epic automatically. Or I can tighten the task further first with gambit:task-refinement. Which do you want?"

**After user responds, invoke the chosen skill directly using the Skill tool.** Do not just tell the user to run it — load and follow the skill immediately.

- "Start executing" → `Skill skill="gambit:executing-plans"`
- "Refine tasks first" → `Skill skill="gambit:task-refinement"` (then executing-plans after)

## Examples

### Bad: Full Task Tree Upfront

```
TaskCreate "Epic: Add OAuth"
TaskCreate "Task 1: Configure OAuth"
TaskCreate "Task 2: Implement token exchange"
TaskCreate "Task 3: Add refresh logic"
# Execute Task 1 → discover library handles refresh
# Task 3 is now wrong. Task tree is brittle.
```

### Good: Iterative Task Creation

```
TaskCreate "Epic: Add OAuth" [immutable requirements + anti-patterns]
TaskCreate "Task 1: Configure OAuth provider"
# Execute → learn library handles refresh automatically
TaskCreate "Task 2: Integrate with existing middleware"
# Created AFTER learning from Task 1 — reflects reality
```

### Bad: Epic Without Anti-Patterns

```
TaskCreate subject: "Epic: OAuth"
  ## Requirements
  - Users authenticate via Google OAuth2
  - Tokens stored securely
# "Tokens stored securely" is vague
# No forbidden patterns → agent rationalizes localStorage when blocked
```

### Good: Epic With Anti-Patterns

```
TaskCreate subject: "Epic: OAuth"
  ## Requirements (IMMUTABLE)
  - Tokens stored in httpOnly cookies with Secure flag
  ## Anti-Patterns (FORBIDDEN)
  - NO localStorage tokens (reason: XSS vulnerability)
  - NO mocking OAuth in integration tests (reason: defeats purpose)
# Explicit reasoning prevents watering down under pressure
```

## Critical Rules

1. **Decompose multi-subsystem requests** — several subsystems = several epics, before refining
2. **Questions in prose, with context** — never AskUserQuestion; every question states why you're asking and your recommendation
3. **Research BEFORE proposing** — use Explore agent for codebase context
4. **Propose 2-3 approaches** — don't jump to a single solution
5. **Decompose for isolation, apply YAGNI** — well-bounded units, no unrequested scope
6. **Epic requirements IMMUTABLE** — tasks adapt, requirements don't
7. **Include anti-patterns** — prevents watering down under pressure
8. **Author only the first wave** — independently pluckable tasks; the rest created iteratively
9. **Apply task refinement** — before handoff
10. **Confirm the contract before handoff** — user locks immutable requirements first
11. **Invoke next skill directly** — don't tell user to run it manually

**Common rationalizations (all mean STOP, follow the process):**
- "Requirements obvious" → Questions reveal hidden complexity
- "I know this pattern" → Research might show a better way
- "Can plan all tasks upfront" → Plans become brittle as you learn
- "It's one project" → Independent subsystems are separate epics; decompose first
- "They'll want this feature too" → YAGNI; propose minimal, let them ask for more

## Verification Checklist

- [ ] Scope-checked: decomposed if multiple independent subsystems
- [ ] All questions asked in prose with context and a recommendation (no AskUserQuestion)
- [ ] Researched codebase patterns (Explore agent)
- [ ] Proposed 2-3 approaches with trade-offs
- [ ] Design decomposed into well-bounded, independently testable units
- [ ] YAGNI applied — no scope the requirements don't demand
- [ ] Created epic with all required sections
- [ ] Anti-patterns include reasoning
- [ ] Quality Bar present in the epic — gambit's fixed maximal standard, copied verbatim (not elicited, not weakened)
- [ ] Rejected approaches have DO NOT REVISIT UNLESS
- [ ] Created only the first wave (pluckable tasks, not full tree)
- [ ] Task refined: scoped, self-contained, explicit, testable
- [ ] User confirmed immutable requirements before handoff
- [ ] Offered next step in prose (execute/refine)
- [ ] Invoked chosen skill directly via Skill tool

## Integration

**Calls:** Explore agent → prose next-step question → invokes one of:
- `gambit:executing-plans` (default — enters the epic worktree automatically)
- `gambit:task-refinement` (optional, before execution)
