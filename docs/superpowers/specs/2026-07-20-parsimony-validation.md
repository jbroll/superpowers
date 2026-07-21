# Parsimony Cut Rules — Validation

Word-count A/B on the token-parsimony edit to `brainstorming` (the same cut-rules
block later added to `writing-plans`).

## Method

Six fresh subagents (clean context), identical model (sonnet) and fixed prompt
("add a `--json` output flag to an existing `report` CLI command"). Each followed
a brainstorming skill file and wrote a design spec. The only variable: three read
the current skill, three read a copy with the cut rules added to Spec Self-Review.

## Result

| Side | Spec word counts | Mean |
|------|------------------|------|
| Baseline (current skill) | 1248, 1131, 1137 | 1172 |
| Edited (cut rules)       | 511, 615, 436    | 520  |

**−55.6%.** The ranges do not overlap — every edited spec is shorter than every
baseline spec — so the effect is real, not run-to-run variance.

## Completeness held

The most aggressive edited spec (436 words) still covered every load-bearing
element the 1131-word baseline did: the core design decision (separate data
collection from rendering), the rejected `--format` alternative with reasoning,
byte-for-byte-unchanged text mode, JSON-key mirroring, exit codes, filter-flag
interaction, error-as-JSON handling, four test cases, out-of-scope. It dropped
padding only: a standalone Assumptions section, a verbose three-option Approaches
Considered, and a Data Flow section that restated the architecture. Passes the
completeness test — implementable with no clarifying questions.

## Caveats

One model, one prompt, n=3 per side, non-interactive proxy for the interactive
flow. Effect size is large and cleanly separated, sufficient to de-risk the change.
The padding-phrase linter (`scripts/padding-lint.sh`) was found to be a weak signal
— baseline specs already flag near-zero filler phrases; the verbosity is word
volume, which the word-count A/B measures directly. The linter remains as a cheap
regression gate.
