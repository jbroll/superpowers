# Keep Sequencing Out of Specs

**Date:** 2026-07-21
**Status:** approved, not yet implemented

## Problem

`brainstorming` produces specs that reach past target design into **task sequencing** — a
"one branch, N commits" build order (e.g. the KinoQ workspace-restructure spec's §12). That
sequencing is authored with no parsimony gate: `writing-plans` invokes `code-parsimony` before
decomposing (`skills/writing-plans/SKILL.md:16`), but `brainstorming` does not. So a
non-parsimonious sequence — transitional scaffolding that a later commit rewrites — gets written,
marked `approved`, and committed, then thrown out one step downstream when `writing-plans`
re-derives the order from scratch. The work is redundant and the redundant copy is the ungated one.

`brainstorming`'s own instructions never ask for a build sequence; the model adds it unprompted.
The fix is to name the boundary and enforce it, not to add a second parsimony gate.

## The boundary

A spec describes the **target state** and **how we know it's reached**. It does **not** prescribe
how to get there. Test: *"how to order the work"* leaves the spec; *"what the end state is and how
we know it's done"* stays.

| Leaves the spec | Stays in the spec |
|---|---|
| Commit sequences, build order, "do X before Y", phase-by-phase task breakdown | Target design — layout, naming, interfaces, module boundaries |
| | Move maps (from→to; order-independent) |
| | Rationale, out-of-scope |
| | Acceptance / verification criteria — the checks that define done |

Task ordering belongs to `writing-plans`, where `code-parsimony` already gates it.

## Design

Two edits, both in `skills/brainstorming/SKILL.md`. Nothing in `writing-plans` changes — it already
owns and gates decomposition, and already re-derives order regardless of what the spec says.

1. **Boundary statement** in the "Presenting the design" guidance (near the `Cover:` line, ~86):
   the spec covers target design and acceptance criteria, not build sequence, commit order, or task
   breakdown — that is `writing-plans`' job, where `code-parsimony` gates it.

2. **Self-review scan item** in Spec Self-Review (adjacent to the Scope check, ~116): flag and
   remove any sequencing / build-order / commit-plan section before the user-review gate, since
   `writing-plans` derives ordering fresh.

## Out of scope

- `writing-plans` edits. It already invokes `code-parsimony` before decomposing and re-derives
  ordering independently; a spec with no sequence section changes nothing for it.
- Project-level decomposition into sub-project specs (`brainstorming` lines 68–69). That is
  scope-splitting across specs, not commit ordering within one — it stays.
- Retroactively editing already-written specs (e.g. KinoQ §12). Historical records stand.

## Validation

`brainstorming` is eval-tuned (CLAUDE.md high-bar zone). Run the relevant evals in `evals/` before
and after. Accept only if skill compliance holds and specs stop emitting sequencing sections.

## Acceptance

- `skills/brainstorming/SKILL.md` carries the boundary statement and the self-review scan item.
- A brainstorming eval whose subject has an obvious build order produces a spec with target design
  and acceptance criteria but **no** commit-sequence / build-order section.
- Existing brainstorming compliance evals still pass.
