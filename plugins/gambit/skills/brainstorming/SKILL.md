---
name: brainstorming
description: Use when user has a new feature idea, rough concept, or unexplored approach. Include when planning before code, breaking a design into tasks, creating an implementation plan, laying out tasks and dependencies, exploring architectural options, or requirements are vague. User phrases like "I want to build X", "should we do this", "let's think through Y", "explore approaches", "break this into tasks", "make an implementation plan". Do NOT use for executing existing plans, fixing bugs, refactoring, or when requirements and an epic already exist.
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

# Brainstorming Ideas Into Designs

## Overview

Turn rough ideas into validated designs captured as immutable epic contracts in the root transcript. Complete worker briefs are authored iteratively as you learn, not upfront.

**Core principle:** Ask questions to understand, research before proposing, document decisions for future reference.

**Announce at start:** "I'm using gambit:brainstorming to refine your idea into a design."

## Rigidity Level

HIGH FREEDOM - Adapt questioning to context. But always:
- Present the immutable epic contract before code
- Author only the first wave — complete independently pluckable worker briefs, never a full tree
- Ask every question in prose with context and a recommendation — never the GambitAskUser tool
- Apply task refinement before handoff

## Quick Reference

| Step | Action | Deliverable |
|------|--------|-------------|
| 1 | Scope-check, then ask clarifying questions | Right granularity + understanding |
| 2 | Research codebase and patterns | Existing approaches |
| 3 | Propose 2-3 approaches | Recommended option |
| 4 | Present design, then Steelman agreement | Validated architecture + frozen Design Ledger |
| 5 | Present draft epic contract | Immutable requirements + anti-patterns |
| 6 | Author complete first-wave worker briefs | Ready for self-review |
| 7 | Apply task refinement | Corner cases covered |
| 8 | Confirm immutable requirements with user | Contract locked |
| 9 | Ask next step, invoke skill | Chain continues automatically |

**Key:** Epic = root-transcript contract (immutable), wave plan = adaptive (replaced as you learn)

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

Resolve the absolute path to `codex-contracts/scout.md`, then dispatch the contracted `scout` class:

```
SpawnAgent
  task_name: "scout"
  fork_turns: "none"
  agent_type: "scout"  # Profile-aware: requires hide_spawn_agent_metadata = false and a non-reserved tool_namespace.
  message: "Read <abs>/codex-contracts/scout.md first (your binding scout contract), then: Find existing [relevant] implementation patterns in this codebase. Report with file:line evidence; say NOT FOUND if absent."
```

**Check scope before refining.** If the request spans multiple independent subsystems (e.g., "a platform with chat, billing, and analytics"), STOP and decompose before asking detail questions — don't refine something that should be several epics. Identify the independent pieces, how they relate, and what order to build them. Then brainstorm the FIRST piece through the normal flow; each piece gets its own epic → tasks cycle. Refining an over-large project wastes questions and produces a brittle epic.

**Then ask clarifying questions in prose. Never use the GambitAskUser tool — in this step or anywhere else in this skill.**

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

### 2. explorer Approaches

**Research before proposing:**
- Existing pattern in codebase → explorer agent
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

**Design the validation ladder, not just the tests.** Identify the fastest focused worker command, the integrated wave/component gate, and any expensive release acceptance or blackbox suite. Record the freshness setup and an explicit acceptance budget. A slow system suite is a release claim, not a reflexive per-task check.

**Decompose for isolation.** Break the system into units that each have one clear purpose, communicate through well-defined interfaces, and can be understood and tested independently. For each unit, you should be able to say what it does, how to use it, and what it depends on — without reading its internals. If you can't change a unit's internals without breaking its consumers, the boundaries are wrong; rework them before locking the epic.

**Apply YAGNI ruthlessly.** Cut every feature, abstraction, and "we might want this later" the stated requirements don't demand. Unbuilt scope is the cheapest scope to remove — if the user wants it, they'll say so when you present.

---

### 3a. Steelman the Agreed Design

After the user and root agree on one coherent candidate design, run one mandatory discovery pass
before drafting an epic contract or authoring first-wave work.
Do not initialize or mutate native plan state during Steelman discovery, dialogue, or closure.
No epic or first-wave work begins before Steelman resolution. The Steelman is read-only and
advisory; the root owns all decisions and every ledger disposition.

#### Build the Design Packet

Supply a self-contained **Design Packet** containing exactly these contracted fields:

1. **User goal**
2. **Agreed constraints and scope**
3. **Chosen approach**
4. **Architecture and data flow**
5. **Rejected alternatives and reasons**
6. **Validation strategy**
7. **Delivery constraints**
8. **Unresolved decisions**

Do not omit an empty field; write `None` when there is genuinely nothing unresolved. The packet
must stand alone without inherited conversation.

#### Resolve and dispatch the Steelman

Resolve the absolute path to `codex-contracts/steelman.md`. Native Codex does not read the external
executor registry. Dispatch the contracted `steelman` class, preferring an installed `steelman`
profile and otherwise `default`, always with `fork_turns: "none"`. The dispatch is fresh and its
message contains only the contract path plus the mode inputs.

```
SpawnAgent
  agent_type: "steelman"  # Profile-aware: requires hide_spawn_agent_metadata = false and a non-reserved tool_namespace.
  task_name: "steelman_the_agreed_design"
  fork_turns: "none"
  message: |
    Read <abs>/codex-contracts/steelman.md first and follow it exactly.

    Mode: Discovery

    Design Packet:
    [complete self-contained packet]
```

Discovery receives the Design Packet and no previous Steelman output. Require one of the contract
statuses — `READY`, `REVISE`, `NEEDS_DECISION`, or `BLOCKED` — and all contracted sections:
**Status**, **Strongest case for the chosen design**, **Strongest credible alternative and when it
wins**, **Numbered findings**, **Actual user decisions**, and **Evidence and coverage**. A missing
status or section is a failed call, not permission for the root to invent the result.

If the selected discovery dispatch or tool call fails, or its output is malformed or missing any
contracted section, stop and report the failure. Do not create a Design Ledger, draft an epic
contract, fall back to another dispatch path, or automatically redispatch.

Route each valid discovery result exactly once:

- `BLOCKED`: stop and show the exact missing material named by the result. Do not draft an epic or
  dispatch another call.
- `NEEDS_DECISION`: follow the ledger/yield path and yield on every named user decision. The root
  cannot advance while any named decision remains unresolved.
- `REVISE`: follow the ledger/yield path but do not advance directly. It requires finding
  dispositions and a material Design Packet revision. If no material revision is adopted, stop.
- `READY`: follow the ledger/yield path. It may skip closure only when no material design change
  follows.

No non-`READY` discovery result can fall through to epic drafting. No discovery branch
automatically spends a second discovery call. Any adopted or open material revision requires the
single closure pass.

#### Freeze the ledger and yield

For every result routed to the ledger/yield path, reflect every discovery finding visibly to the
user in a transcript-local frozen **Design Ledger**. Keep every returned ID and assign it exactly
one root-owned disposition: `ADOPTED`, `REJECTED` with a reason, `OPEN`, or `DEFERRED` with a scope
boundary. Record user decisions and packet revisions against the affected IDs. Never put the
ledger in task or plan state.

Then yield to the user for discussion. The root cannot silently revise the packet and dispatch
closure in the same turn. The user must be able to see every discovery finding, every disposition,
and the resulting design change before deciding what comes next.

#### Run bounded closure when required

After user/root discussion, run exactly one closure pass if an `ADOPTED` or `OPEN` finding
materially changes the design. Skip closure only when discovery returned `READY` and no material
design change occurred. Use the revised self-contained Design Packet, the frozen
Design Ledger verbatim, and a concise design delta as the only closure inputs. Repeat the same
backend dispatch rules above.
Under those rules, native Codex uses another fresh contracted dispatch with
`fork_turns: "none"`.

Require one closure status — `READY`, `STILL_OPEN`, `CHANGE_INDUCED_CONCERN`, or `BLOCKED` — plus
**Status**, **Ledger dispositions**, **Change-induced concerns**, **Required caller action**, and
**Evidence and coverage**. Closure cannot restart discovery, cannot reopen `REJECTED` or
`DEFERRED` items, and cannot add unrelated improvements. A `READY` result, or the permitted
discovery skip, allows epic drafting to begin.

No automatic third call is allowed. For any non-`READY` closure, stop and offer exactly these user
choices in prose:

1. revise without another Steelman pass;
2. lock the contract with the residual risk recorded; or
3. explicitly authorize another discovery cycle.

The third choice is the only choice that resets the budget, and it is valid only for a fundamental
architecture reset with explicit user authorization. Never infer that authorization from a
finding, a revision, or user silence.

#### Finalize the packet for contract drafting

Before epic drafting, the root must produce a finalized Design Packet from the agreed design,
user decisions, and ledger dispositions. Incorporate every `ADOPTED` conclusion into the
applicable packet field and carry it into the epic's **Requirements (IMMUTABLE)**,
**Anti-Patterns (FORBIDDEN)**, **Approach**, **Validation Strategy**, or **Delivery Constraints**.
A `READY` status permits drafting but is not the contract source.

Draft the epic contract from that finalized Design Packet. Do not copy the Design Ledger itself
into the epic, and do not convert ledger IDs into task or plan state; the ledger remains
transcript-local.

---

### 4. Present the Epic Contract

After design is validated, author the immutable contract and present it in full in the root transcript. See [TEMPLATES.md](TEMPLATES.md) for the complete template. The epic is not a native plan step.

**Required epic sections:**

| Section | Purpose |
|---------|---------|
| Requirements (IMMUTABLE) | Specific, testable conditions that must be true |
| Success Criteria | Objective, checkable items including "all tests passing" |
| Anti-Patterns (FORBIDDEN) | Explicitly forbidden patterns with reasoning |
| Quality Bar | gambit's fixed maximal standard for "good code" — the highest professional quality, written verbatim into every epic and judged against each diff by reviewers and the orchestrator at every checkpoint, beyond the objective Success Criteria |
| Approach | 2-3 paragraph summary of chosen approach |
| Approaches Considered | Rejected alternatives with DO NOT REVISIT conditions |
| Delivery Constraints | Circuit breakers for non-convergence, repeated repairs, and scope growth |
| Validation Strategy | Focused worker command, wave/component gate, release acceptance, freshness, and acceptance budget |

**The Quality Bar is fixed — write it verbatim, don't elicit it.** Every epic carries the same bar: the highest professional standard, the code a master engineer would ship — elegant, complete, built on a superb foundation. It is not a per-project preference and is never negotiated down. Copy it verbatim from [TEMPLATES.md](TEMPLATES.md) into the epic so the checkpoint gate and reviewers have it locally. It governs *craftsmanship, not scope* — how well the required work is built, never how much of it; project-specific prohibitions go in Anti-Patterns. It sits on top of the mechanical floor the worker contract enforces (no suppression, no weakened tests, no dead code).

```
Present in the root transcript as "Epic: [Feature Name]":
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

    ## Delivery Constraints
    - Stop after two consecutive non-converging checkpoints; require explicit user approval
      before expanding scope, architecture, or budget. Repairs ladder up to terminal
      escalation attempts repeated with updated evidence until the defect clears.

    ## Validation Strategy
    - Focused worker command: [fast exact command]
    - Wave/component gate: [integrated exact command]
    - Release acceptance: [fresh expensive exact command]
    - Acceptance budget: [normally one final run]
```

**Anti-patterns prevent requirement erosion.** When implementation gets hard, there's pressure to water down requirements. Explicit forbidden patterns with reasoning prevent this.

---

### 5. Create the First Wave

Author a complete worker brief for every worker that is **independently pluckable from the current codebase**: each brief must be writable entirely from code that exists right now — exact file set, cited anchors, testable criteria — with no placeholder for another worker's output, and its file set must be disjoint from the others'. Present every full first-wave worker brief in the root transcript. Often there is one worker; when the design genuinely starts in parallel pieces, there are several. Never author a full tree.

Do not encode dependency edges. The epic is a contract in the root transcript, not a plan step or prerequisite. Put all independent first-wave workers in one concise wave step; order work that cannot start yet as a later wave only after its brief can be written from execution learnings.

```
Present in the root transcript as "Worker Brief: Add [specific deliverable]":
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

Keep each revised complete worker brief in the root transcript while refining. Do not initialize native plan state during drafting or self-review.

#### Epic + first-task self-review

Before announcing the plan to the user, run an inline self-review across the epic AND the first task. This takes 30 seconds and catches the same class of defects a subagent review pass would — immutable requirements that are actually vague, scope that silently expanded, contradictions between the epic's approach and the first task's implementation steps.

Scan for:
- **Placeholders:** Any `TBD`, `TODO`, `FIXME`, `XXX`, `[details above]`, "see requirements", `<angle-bracket-placeholder>`, or sentence that trails off without committing to a specific behavior
- **Vague requirements:** "properly handle errors", "good performance", "secure authentication", "similar to X" — requirements that can't be tested objectively must be rewritten with concrete, checkable conditions (or moved to a subtask's implementation notes)
- **Scope drift:** Does the first task introduce files, behaviors, or dependencies the epic's requirements don't justify? Either tighten the task or add the requirement to the epic explicitly.
- **Ambiguity:** Any sentence where two readers could reach different implementations. Pick one and say it.
- **Internal consistency:** The first task's files, function names, and success criteria should match the epic's stated approach. Mismatches mean one of them is wrong.
- **Quality Bar present:** Does the epic carry the fixed Quality Bar verbatim from [TEMPLATES.md](TEMPLATES.md), unweakened? It's the same standard on every epic — restore it if it's missing, paraphrased, or watered down.
- **Convergence bounded:** Does Delivery Constraints stop autonomous continuation after two consecutive checkpoints that retire no success criterion or named blocker, bound repair attempts, and require explicit user approval for scope or budget growth?
- **Validation tiered:** Does Validation Strategy distinguish the focused worker command, wave/component gate, and release acceptance, including freshness and an acceptance budget?

Fix what you find in the draft contract and complete worker briefs. Do not initialize native plan state during self-review. Do NOT present a plan that has items on this list.

#### Confirm the contract with the user

Epic requirements are IMMUTABLE once execution starts — so the user reviews them BEFORE handoff, not after. Present the complete draft contract and every complete first-wave worker brief for confirmation. The contract includes Requirements, Success Criteria, Anti-Patterns, Quality Bar, Approach, Approaches Considered, Delivery Constraints, and Validation Strategy. The Quality Bar is gambit's fixed standard, so note it rather than asking the user to set it:

> "Here's the epic contract and the complete first wave — these requirements lock once we start: [summary]. Good to lock both, or change anything first?"

If they request changes, present the revised full contract and re-run the self-review. Only proceed to handoff once they confirm.

After explicit user confirmation of the full epic contract and complete first-wave worker briefs:

1. Present the full approved epic contract in the root transcript.
2. Present every complete first-wave worker brief in the root transcript.
3. Initialize the complete native wave plan. The epic and worker briefs are not plan steps; each step is only a concise wave summary.

```
SessionPlanWrite
  plan:
    - step: "Wave 1: Add [deliverable]"
      status: pending
```

This is the first native plan write. There is no draft plan state before confirmation.

---

### 7. Handoff

**Offer next steps in prose (not GambitAskUser), then invoke the chosen skill directly.**

> "The approved epic contract and full first-wave worker briefs are in this root transcript. I'd start executing now — gambit:executing-plans opens a fresh worktree for the epic automatically. Or I can tighten the briefs further first with gambit:task-refinement. Which do you want?"

**After user responds, invoke the chosen skill directly using Codex skill invocation.** Do not just tell the user to run it — load and follow the skill immediately.

- "Start executing" → `Invoke skill="$gambit:executing-plans"`
- "Refine tasks first" → `Invoke skill="$gambit:task-refinement"` (then executing-plans after)

## Examples

### Bad: Epic and Workers as Plan Records

Do not put an epic step followed by one step per worker into the native plan. That turns concise wave state into a brittle task tree, and later steps become wrong as execution teaches you more.

### Good: Contract and Briefs in Transcript, Waves in Plan

```
# Root transcript contains the complete approved "Epic: Add OAuth" contract.
# Root transcript contains complete briefs for both independent first-wave workers.

SessionPlanWrite
  plan:
    - step: "Wave 1: Configure OAuth provider and validate middleware anchors"
      status: pending

# Execute the wave, checkpoint learnings, then author later worker briefs.
# Replace the complete plan list only when the next concise wave is known.
```

### Bad: Contract Without Anti-Patterns

```
Present "Epic: OAuth" in the root transcript:
    ## Requirements
    - Users authenticate via Google OAuth2
    - Tokens stored securely
# "Tokens stored securely" is vague
# No forbidden patterns → agent rationalizes localStorage when blocked
```

### Good: Contract With Anti-Patterns

```
Present "Epic: OAuth" in the root transcript:
    ## Requirements (IMMUTABLE)
    - Tokens stored in httpOnly cookies with Secure flag
    ## Anti-Patterns (FORBIDDEN)
    - NO localStorage tokens (reason: XSS vulnerability)
    - NO mocking OAuth in integration tests (reason: defeats purpose)
# Explicit reasoning prevents watering down under pressure
```

## Critical Rules

1. **Decompose multi-subsystem requests** — several subsystems = several epics, before refining
2. **Questions in prose, with context** — never GambitAskUser; every question states why you're asking and your recommendation
3. **Research BEFORE proposing** — use explorer agent for codebase context
4. **Propose 2-3 approaches** — don't jump to a single solution
5. **Decompose for isolation, apply YAGNI** — well-bounded units, no unrequested scope
6. **Steelman before epic drafting** — one mandatory discovery pass after design agreement
7. **Freeze and show every finding** — disposition the complete ledger, then yield to the user
8. **Bound closure** — at most one discovery and one closure call without an explicitly authorized reset
9. **Epic requirements IMMUTABLE** — tasks adapt, requirements don't
10. **Include anti-patterns** — prevents watering down under pressure
11. **Author only the first wave** — independently pluckable tasks; the rest created iteratively
12. **Apply task refinement** — before handoff
13. **Confirm the contract before handoff** — user locks immutable requirements first
14. **Invoke next skill directly** — don't tell user to run it manually

**Common rationalizations (all mean STOP, follow the process):**
- "Requirements obvious" → Questions reveal hidden complexity
- "I know this pattern" → Research might show a better way
- "The design already looks solid" → The contracted discovery pass is still mandatory
- "Closure can happen immediately" → Show the frozen ledger and yield to the user first
- "One more pass will settle it" → No automatic third call; only an explicit architecture reset renews the budget
- "Can plan every worker upfront" → Worker briefs become brittle as you learn
- "It's one project" → Independent subsystems are separate epics; decompose first
- "They'll want this feature too" → YAGNI; propose minimal, let them ask for more

## Verification Checklist

- [ ] Scope-checked: decomposed if multiple independent subsystems
- [ ] All questions asked in prose with context and a recommendation (no GambitAskUser)
- [ ] Researched codebase patterns (explorer agent)
- [ ] Proposed 2-3 approaches with trade-offs
- [ ] Design decomposed into well-bounded, independently testable units
- [ ] YAGNI applied — no scope the requirements don't demand
- [ ] Sent the complete eight-field Design Packet through mandatory Steelman discovery
- [ ] Reflected every finding in the visible frozen Design Ledger and yielded to the user
- [ ] Ran closure when required, with no automatic third call or inferred reset
- [ ] Created epic with all required sections
- [ ] Anti-patterns include reasoning
- [ ] Quality Bar present in the epic — gambit's fixed maximal standard, copied verbatim (not elicited, not weakened)
- [ ] Rejected approaches have DO NOT REVISIT UNLESS
- [ ] Created only the first wave (pluckable tasks, not full tree)
- [ ] Task refined: scoped, self-contained, explicit, testable
- [ ] User confirmed immutable requirements and the complete first wave before handoff
- [ ] Offered next step in prose (execute/refine)
- [ ] Invoked chosen skill directly via Codex skill invocation

## Integration

**Calls:** explorer agent → contracted Steelman discovery/closure → prose next-step question → invokes one of:
- `gambit:executing-plans` (default — enters the epic worktree automatically)
- `gambit:task-refinement` (optional, before execution)
