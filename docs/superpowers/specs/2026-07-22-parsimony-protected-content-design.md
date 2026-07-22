# Protect Constraints and Failure Contracts From the Cut Rules

**Date:** 2026-07-22
**Status:** approved, not yet implemented

## Problem

The prose cut rules added on 2026-07-20 (`0f4729e`) work as designed on reasoning, and
overreach on measurement. Across three codebases on 07-21/07-22 the specs stayed generous
with rationale and architecture, and lost a specific content class: **facts obtainable only
by reading the repo.**

Observed decay, same project and author, consecutive specs:

| Corpus | Content | Trajectory | Execution cost |
|---|---|---|---|
| KinoQ | `## Binding constraints` (per-file size headroom) | present stages 2/3/4 → **absent** 5a/5b | `useProjectSession.ts` reached 498/500 by deleting doc comments; unplanned extraction task mid-build, then a second for `App.tsx` |
| KinoQ | `## Error handling` | present stage 4 → **absent** 5a/5b | property writes silently no-op'd; `useCameraProperties.refresh()` had no error path — a dead camera rendered as "This camera exposes no settings" |
| checklist | `## Ownership / boundaries` | 54 → 35 → **0** words | three rowboat commits landed on `main`, bypassing `land.sh`'s lock, during concurrent lands |
| checklist | plan `## Global Constraints` | −33% while the plans themselves grew | the block pinning repo, branch, worktree, landing policy |
| rowboat | `sync.ts` at 491 lines against a 500-line cap, stated in-session an hour before the spec was written | never recorded | forced a 4-way file split mid-commit |

The mechanism is the **boilerplate test** — "if a competent implementer would get this right
without being told, don't write it." Landing mechanics, size caps, and path conventions read
like generic process boilerplate. They are project-specific facts no implementer can infer.

Two structural gaps let it through. `brainstorming`'s cut rules carry no protected-content
list; `writing-plans` has one but it covers only file paths, code, commands, and expected
output. And the test is applied by the author, who holds full repo context, against a reader
who has none: `writing-plans` targets "an engineer with zero context for our codebase", and
`subagent-driven-development` makes that literal — the implementer sees only the extracted
task brief plus whatever spec text the controller pastes in.

Roughly half the friction in the same window was unrelated to prose length (subagent deaths
on API errors, a Camera2 domain error, a latent selector bug, environment noise). This spec
targets only the attributable half.

## The boundary

**Parsimony trims reasoning, never measurements.** A sentence that records something the
author had to read the repo to learn stays, regardless of length. A sentence that re-derives,
restates, or justifies goes.

## Design

Five edits across two skill files. Anchor by quoted content, not line number — the parked
sequencing edit shifts `brainstorming`'s self-review numbering.

### 1. Narrow the boilerplate test

Both files. Replace the existing boilerplate-test bullet with:

> **Boilerplate test** (before writing): if a competent implementer *new to this repo* would
> get this right from general engineering knowledge, don't write it. Project-specific facts —
> enforced caps, path conventions, landing mechanics, exact values, and where a value comes
> from and when it is available — fail this test and stay.

### 2. Protected-content list in `brainstorming`

Add to the `Cut padding` block, mirroring the clause `writing-plans` already carries:

> - Never cut: constraints the repo enforces (size caps, lint gates, path conventions),
>   ownership and landing mechanics (worktree, branch, land command), failure contracts
>   (which errors, on which paths, with what codes), and exact values (ports, issuers, header
>   names, limits).

### 3. Required sections in `brainstorming` self-review

The `Cover:` line already names error handling and it was cut anyway, so presence must be
checked. Add as a numbered self-review item, before `Cut padding`:

> **Required sections:** Does the spec carry a *Binding constraints* section (what the repo
> enforces that this work must respect, with measured current values) and a failure-contract
> section (which errors, on which paths, with what codes)? Both are exempt from the cut rules.
> If missing or empty, write them.

`Binding constraints` reuses the section name from the pre-cut KinoQ specs.

### 4. Extend the `writing-plans` protected list

Append to the existing "Never cut required content" bullet:

> …and the Global Constraints block — repo, branch/worktree, landing command, version floors,
> enforced caps.

### 5. Measurement gate in `brainstorming`

Add under **Working in existing codebases:**

> **Measure before you write.** For each file the work will touch, read it and record: current
> size against any cap the repo enforces, the exact values the design depends on (names, ports,
> headers, limits), and which gates run on commit. Record measured numbers, not estimates.
> These land in Binding constraints.

Scoped to files the design's move map or component list names — bounded by the size of the
change, not the repo.

`writing-plans` needs no sixth edit: it already instructs that Global Constraints carry "exact
values copied verbatim from the spec."

## Binding constraints

- Sessions load `/home/john/.claude/plugins/cache/superpowers-dev/superpowers/6.1.1/skills/`
  (synced 2026-07-21 07:44), **not** this working tree. An edit here has no effect on any
  session until that cache is re-synced. This is why the 07-21 sequencing change has never
  run despite `2ffa91b` being committed — that commit added only the spec document.
- `skills/brainstorming/SKILL.md` is 167 lines, `skills/writing-plans/SKILL.md` 197. No size
  cap, commit hook, or lefthook config exists in this repo; `package.json` defines no scripts.
- `skills/brainstorming/SKILL.md` has an **uncommitted** working-tree edit (the parked
  sequencing change, self-review item 4). Edits here must apply cleanly with or without it.
- CLAUDE.md places both files in the high-bar zone: behavior-shaping content, changes require
  eval evidence, and Red Flags tables and "human partner" language are not to be reworded.
- `scripts/padding-lint.sh FILE...` is the deterministic regression gate; exit 1 on any flag.
  It measures delete-on-sight phrases only, and was already found a weak signal.

## Failure contracts

- A spec with no *Binding constraints* section fails self-review item 3 and is written, not
  waived. An empty section is the same failure as a missing one.
- A file the design touches that cannot be read (missing, generated, out of tree) is recorded
  by name as unmeasured, rather than estimated or omitted.
- The measurement gate does not gate on the repo having caps. A repo with no enforced gates
  records that fact once and moves on.

## Out of scope

- The parked sequencing edit. Left uncommitted by decision; ship separately.
- `code-parsimony`. The ladder governs code and task count, not spec prose, and no incident
  traced to it. Note it never fired in either rowboat session despite `d86cc9a` hard-wiring it.
- Verification depth as a whole. The KinoQ controller's own diagnosis — "I wrote this plan with
  less codebase verification" — names a broader problem than the cut rules. Edit 5 addresses
  the measurable slice; the rest is a separate spec.
- Retroactive edits to specs already written.

## Validation

Both files are eval-tuned. Run the existing brainstorming and spec scenarios before and after:
`spec-writing-blind-spot`, `spec-reviewer-catches-planted-flaws`, `sdd-spec-context-consumed`,
`cost-spec-plan-duplication`, `brainstorming-resists-jump-to-implementation`.

None of them test for a recorded constraint, so add one scenario. Fixture: a repo with a
~490-line source file under an enforced 500-line commit hook, and a feature request that must
add state to that file. Pass = the spec records the current line count and the cap; fail = it
does not. This reproduces the KinoQ and rowboat incidents directly.

Accept only if the new scenario passes, the existing scenarios hold, and spec word count does
not return to pre-07-20 levels — the cut rules are meant to keep working on reasoning.

## Acceptance

- Both SKILL.md files carry the narrowed boilerplate test.
- `brainstorming` carries the protected-content list, the required-sections self-review item,
  and the measurement gate.
- `writing-plans`' protected list names Global Constraints.
- `scripts/padding-lint.sh` reports zero flags on both edited files.
- The new eval scenario passes; the five existing scenarios hold.
- Edits apply cleanly whether or not the parked sequencing change is present.
