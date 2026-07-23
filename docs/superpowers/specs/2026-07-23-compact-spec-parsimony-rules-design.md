# Compact-Spec Parsimony Rules — Design

**Date:** 2026-07-23
**Status:** Approved for implementation

## Goal

Change `brainstorming/SKILL.md` so specs carry each fact **once** (no cross-section restatement) and are **cheap to produce** (no verbose-then-scrub loop), while still fully specifying the work so downstream code is unchanged.

Motivated by a live A/B probe (2026-07-22, `cost-spec-plan-duplication`, opus-4.8, n=5): the current parsimony span raised output +22%, cost +25%, and time +41% over its pre-parsimony baseline while spec/plan length stayed flat and the gauntlet failed 8/10 runs for the same reason in both arms — the same behavioral facts restated across Behavior / Failure contract / Success criteria / Testing sections. The cut rules operate at sentence level; the duplication is at section level.

## Scope / Non-goals

- **In:** `skills/brainstorming/SKILL.md` — two regions (Presenting the design; Spec Self-Review).
- **Out:** `writing-plans/SKILL.md` (the plan→spec duplication is a separate later change); all other skills; the harness.

## The change

### Move 1 — canonical section set, single ownership (Region A: *Presenting the design*)

Replace the *"Cover: architecture, components, data flow, error handling, testing"* bullet and the scale/cut bullet with a fixed section set where each fact has one home, and forbid a Success/Acceptance section. New bullets:

> - Use a canonical section set, each fact in exactly one section: **Goal**, **Scope / Non-goals**, **Data model**, **Behavior contract** (what each operation does), **Failure contract** (errors, codes, paths), **Binding constraints** (repo-enforced, measured), **Testing** (a named list — one entry per behavior/failure/edge, *by reference*: "unknown input → error", not a re-description). State each requirement, failure mode, and constraint ONCE, in its owner section; later sections reference it, never restate it. Do not add a "Success criteria" / "Acceptance criteria" section — the contracts and Binding constraints are the acceptance criteria.
> - Scale each section to its complexity: a few sentences if straightforward, up to 200–300 words if nuanced. Write it compact the first time; length is the outcome of stating each fact once, not a target.

### Move 2 + 3 — single-source scan, lighter review (Region B: *Spec Self-Review*)

Replace the 7-step review (whose *Completeness test* rewards per-section self-completeness, causing the restatement) with a 5-step structural pass plus a **conditional** prose battery:

> **Spec Self-Review:**
> After writing, a quick structural pass — expensive prose-cutting only where a section reads padded:
>
> 1. **Placeholder scan:** Any "TBD", "TODO", or vague requirement? Fix them.
> 2. **Consistency & scope:** Sections agree; focused enough for a single implementation plan (else decompose).
> 3. **Sequencing scan:** Did a build order, commit sequence, or phase-by-phase task breakdown creep in? Cut it — writing-plans derives ordering fresh under code-parsimony. Keep target design, move maps, and acceptance criteria.
> 4. **Ambiguity check:** Could any requirement be read two ways? Pick one and make it explicit.
> 5. **Single source of truth & required sections:** The spec carries a *Binding constraints* section (repo-enforced values, measured) and a *failure-contract* section, both non-empty and exempt from cutting. Each requirement, failure mode, and constraint appears in exactly one owner section (Behavior contract / Failure contract / Binding constraints / Data model); any fact stated in a second section → replace with a reference or delete it. No "Success/Acceptance" section — the contracts are the acceptance criteria; Testing lists tests by reference, not re-described behavior. This is where cross-section duplication gets cut.
> 6. **Cut padding — only if a section reads padded:** apply the tests below; skip an already-tight section.
>    - **Boilerplate test:** if a competent implementer new to this repo would get it right from general engineering knowledge, don't write it. Project-specific facts — enforced caps, path conventions, landing mechanics, exact values — stay.
>    - **Sentence test:** if removing a sentence changes nothing the reader learns, delete it. Hardest on the first and last sentence of each paragraph.
>    - **Delete on sight:** "Note that", "It is important to", "This section describes/covers", "In order to X" → "To X", filler adverbs, setup sentences, closing restatements, any sentence restating a heading.
>    - **Never cut:** constraints the repo enforces, ownership and landing mechanics, failure contracts, and exact values. Parsimony trims restatement and reasoning, never the fact's single canonical statement.
>
> Fix any issues inline. No need to re-review — just fix and move on.

Default path is steps 1–5 (all cheap structural checks); the expensive sentence battery (step 6) fires only when a section reads padded — versus stock v6.1.1's 4-step review, this adds one structural step and keeps prose-cutting off the default path.

## Why the code is unchanged

Nothing is removed but restatement. Every requirement, failure mode, and constraint keeps exactly one canonical statement; Testing still enumerates every check (by reference); Failure contract and Binding constraints stay required. The spec carries the same information, stated once.

## Failure contract (guardrails — reject conditions)

- **Outcome regression:** if the treatment arm's `cost-spec-plan-duplication` pass-rate drops below stock v6.1.1's, the change is rejected — a compact spec that produces worse/different code fails the "same code" bar.
- **No compactness gain:** if treatment spec-doc bytes/lines do not fall vs stock, the structural change did not work; revisit before shipping.
- **Cost regression vs stock:** if treatment output-tokens/cost/duration rise materially above stock's (whose review is only 4 light steps), the "cheap to produce" goal failed; the review is still too heavy.

## Binding constraints

- Repo is the fork `jbroll/superpowers`; work lands on branch `spec-sequencing-boundary`. Skill changes require eval evidence before merge (`CLAUDE.md`: "Skill Changes Require Evaluation").
- The file is behavior-shaping content; edits are surgical to the two named regions. Do not touch Red-Flags tables, rationalization lists, or "human partner" language.
- `brainstorming/SKILL.md` is 170 lines at HEAD `21eec8c`; stock v6.1.1 (`d884ae0`) is 159 lines with a 4-step self-review and no cut rules.

## Validation

2-arm A/B via the reusable probe harness (`scratchpad/probe.sh`), scenario `cost-spec-plan-duplication`, claude/opus subscription, n=5/arm interleaved:

- **Baseline:** stock upstream **v6.1.1** (`d884ae0`) — the release the fork builds on.
- **Treatment:** fork HEAD **+ this change**.

Per run capture spec-doc bytes/lines (compactness), `total_output` + `est_cost_usd` + `duration_ms` (production cost), and the gauntlet `final` verdict (outcome guardrail). Report per-arm medians and the treatment−baseline delta against the three reject conditions above.
