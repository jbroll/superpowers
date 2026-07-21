# Usage Analysis

Fork-local tooling to track the tokens, cost, and phase breakdown of real Claude Code
sessions — to observe the superpowers mods' effect on actual development without running
explicit evals. **Not for upstream** (fork-specific).

## Usage

```sh
FILES=(~/.claude/projects/*/*.jsonl)

# per-(session × phase) CSV
python3 analysis/mine.py "${FILES[@]}"

# roll sessions up into features (grouped by spec/plan artifact slug)
python3 analysis/mine.py --by-feature --only-superpowers "${FILES[@]}"

# per-session time-series JSON
python3 analysis/mine.py --timeline --only-superpowers "${FILES[@]}"

# ASCII weekly stacked-phase chart (X=week, Y=tokens, effectiveness overlay)
python3 analysis/mine.py --plot --only-superpowers "${FILES[@]}"
python3 analysis/mine.py --plot --output --only-superpowers "${FILES[@]}"   # or --input / --total
```

Flags: `--only-superpowers` (keep only sessions that really used a superpowers skill or
touched a spec/plan artifact — not the injected bootstrap mention), `--by-feature`,
`--timeline`, `--plot`, and the plot metric `--total` (default) / `--output` / `--input`.

## Data source (no logging to enable)

`~/.claude/projects/<encoded-cwd>/*.jsonl` — the main session transcripts. Per assistant
message: `message.usage` (input / output / cache_creation / cache_read tokens),
`message.model`, `timestamp`, `gitBranch`. Subagent totals come from each `Agent`
tool_result's `subagent_tokens`. Usage lines are **deduped** by `(message.id, requestId)`
— Claude Code replays entries, and counting them inflates tokens ~1.6× (matches ccusage).

## Phases — activity-based attribution

Phases are `other`, `spec`, `plan`, `execute`, `replan`. Each turn is classified by **what
its tools do** (`classify_turn`), not by which skill was announced — skill-boundary
attribution was unreliable because execution rarely announces itself (inline
implementation after the plan, no execute skill). Tool-less/read-only turns inherit the
adjacent phase.

| Turn activity | Phase |
|---|---|
| Write/Edit a source file, test-run Bash, `Agent` dispatch, execute skill | execute |
| Write/Edit `docs/superpowers/specs/…`, brainstorming skill | spec |
| Write/Edit `docs/superpowers/plans/…`, writing-plans skill | plan |
| Read-only / tool-less | inherit adjacent |

**replan** = ad-hoc planning *in the middle of the build* — a spec/plan-flavored turn
after execution began, **without** a brainstorming/writing-plans call. A formal
brainstorming/writing-plans call mid-build is the opposite: a fresh, proper planning round
(spec/plan), which resets the state. A state machine (`pre → planned → building`) drives
this. High precision, low recall by design — routine plan-doc bookkeeping can't be told
from a redesign via tool metadata, so replan requires the ad-hoc pattern; genuine
redesigns done through the skills are counted as clean planning.

## Features

Sessions group into features by the **artifact slug** shared between a spec doc
(`…-<slug>-design.md`) and its plan (`…-<slug>.md`), date-prefix and `-design` stripped.
Robust to late/shared git branches and phases spanning sessions. Artifact-less sessions
fall into `_unlinked`.

## Cost — date-effective, cache-aware

`tokens × price[model]`, cache-aware (cache_read = 0.1× input, cache_write = 1.25× input).
`prices.json` is **date-effective**: each model has entries sorted by `effective` date;
a session prices with the entry effective at its date, historic sessions use the earliest
(today's) entry, and future price changes are added going forward — never edit past
entries. Cross-checked against `npx ccusage`. Opus 4.8 = $5/$25 per 1M (authoritative,
2026-07-21).

## Effectiveness — read as a proxy, not a verdict

The `--plot` `◆` overlay is a trailing-N median of `(spec+plan)/execute` tokens per feature
("planning per unit build"); zero-execution features are excluded as attribution-suspect.
Honest limits, learned the hard way:

- Planning-vs-execution ratios are dominated by **feature type** (a migration is
  execution-heavy regardless of spec quality) — no calendar-time aggregate isolates
  parsimony.
- Token totals are **cache_read-dominated**, so the `--output` view is the parsimony-relevant
  one (output is what the cut rules shrink); `--total` mostly shows cost.
- The parsimony mods synced 2026-07-20, so the corpus is essentially all pre-mod — **no
  measurable effect yet.**

The clean signal for parsimony stays the controlled A/B and **per-feature-type** output
comparison, not the timeline. Don't treat any single number as a verdict.

## Layout

- `mine.py` — attribution, feature grouping, pricing, CSV/JSON/ASCII output
- `prices.json` — date-effective, cache-aware model prices
- `tests/test_mine.py` — plain-assert unit tests (`python3 analysis/tests/test_mine.py`)
- generated data (`*.csv`, `out/`) is gitignored
