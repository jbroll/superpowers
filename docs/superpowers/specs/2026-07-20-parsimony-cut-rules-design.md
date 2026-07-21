# Parsimony: Code and Token Cut Rules

## Problem

The auto-triggered flow (brainstorm → spec → plan → subagent execution) produces
output that is too verbose, and nothing biases generated code toward the minimal
solution. Two gaps, one shape.

## Goals

- **Code parsimony**: bias plan and code writing toward the fewest steps/lines that work.
- **Token parsimony**: cut padding from brainstorming spec output and written plans.
- Keep the existing flow auto-triggered and natural. No new commands.

## Non-Goals

- Caveman-style compression (dropped articles, fragments). It fights the deliberate
  "human partner" prose and risks breaking structured output.
- Pruning unused skills. Tracked as a separate follow-up.
- Changing when skills trigger.

## Design

Both goals are the same shape — a **cut ladder**: a pre-write gate that stops content
from being written, and a post-write test that removes what was written anyway.

|            | Prose (token)                    | Code                                             |
|------------|----------------------------------|--------------------------------------------------|
| Pre-write  | boilerplate test                 | "does it need to exist?" → reuse → stdlib → native → dep → one line |
| Post-write | sentence test                    | "what can I delete?"                             |
| Source     | ai-roller `specification` skill  | ponytail YAGNI ladder (MIT)                      |

### 1. `code-parsimony` skill (new)

`skills/code-parsimony/SKILL.md`. Ponytail's YAGNI ladder, adapted to house voice.

- Description triggers on plan and code writing so it fires alongside `writing-plans`
  and `test-driven-development` — not always-on.
- Pre-generation ladder, stop at the first rung that works: does it need to exist
  (YAGNI) → reuse existing code → standard library → native platform feature →
  already-installed dependency → one line → minimal viable code.
- Guardrails kept from ponytail: never skip input validation, error handling,
  security, or accessibility; mark deliberate shortcuts with a comment naming when to
  upgrade; understand the problem before simplifying.
- Post-generation: one "what can I delete?" pass, folded into
  `verification-before-completion` rather than duplicated here.
- Drop from ponytail: intensity levels, "challenge the requirements" (brainstorming
  already owns requirements), the MCP server, hooks, and per-platform adapters.
- Credit ponytail (MIT) in the skill.

### 2. Port cut rules into `brainstorming` and `writing-plans`

Harvest the transferable rules from ai-roller's `specification` skill. Take the rules,
not the plumbing.

**No word cap.** Use every word the content requires and no more. Length is the
outcome of the cut rules, not a target we set. The existing 200-300 word figure stays
as a ceiling; every section then passes through the cut rules, so a 300-word draft is
cut to whatever earns its place — sometimes a third of that, occasionally the full 300
when the content is genuinely that dense. Completeness is judged by the completeness
test below, never by length in either direction.

Rules to port:
- **Boilerplate test** (before writing): if a competent implementer would get it right
  without being told, delete it.
- **Sentence test** (after writing): if removing a sentence changes nothing a reader
  learns, delete it. Apply hardest to the first and last sentence of each paragraph.
- **Delete on sight** kill-list: "Note that", "It is important to", "This section
  describes/covers", "In order to X"→"To X", filler adverbs (generally/typically/
  usually/often), setup sentences, closing restatements, transition sentences, any
  sentence restating a heading.
- **Completeness test**: a section is done when two different phrasings would produce
  identical behavior — not when it is long or polished.
- **Voice**: active voice with a named agent; specific over general.

Placement:
- `brainstorming`: keep the "up to 200-300 words" ceiling (line ~84) but subordinate
  it to the cut rules, and add the cut rules to the spec self-review (lines ~112-117),
  so padding is removed from each section before the user review gate.
- `writing-plans`: add the cut rules to the plan self-review pass.

Do **not** import: `air check`, Route Skill references, parent-`index.md`-vs-leaf
structure, `##`-triggers-decomposition — all specific to ai-roller's spec tree.

### 3. Validation

`brainstorming` and `writing-plans` are eval-tuned; CLAUDE.md flags this as the
high-bar zone. Run the relevant evals in `evals/` before and after. Accept only if
token count drops and skill compliance holds.

## Deferred

- Prune unused skills from the fork.
- Applying code-parsimony's post-write pass to subagent-driven execution.
