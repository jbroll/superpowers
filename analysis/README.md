# Usage Analysis

Fork-local tooling to track the size, cost, and phase breakdown of real Claude Code
sessions — so we can observe the effect of the superpowers mods on actual development
without running explicit evals. **Not for upstream** (fork-specific).

## What it measures

Per session, split into **phases** (spec / plan / execute), each with:

- **prompt size** — `input_tokens` + `cache_read_input_tokens` per turn
- **tokens** — input / output / cache-create / cache-read
- **cost** — derived, cache-aware (there is no cost field in the logs)
- **subagent tokens** — rolled up into the phase active when the subagent was dispatched
- **tool calls**, wall time

Then correlate upstream size (spec/plan) against downstream cost (execute) across
features. See the effectiveness note below.

## Data source (no logging to enable)

`~/.claude/projects/<encoded-cwd>/*.jsonl`. Confirmed present per assistant message:
`message.usage` (`input_tokens`, `output_tokens`, `cache_creation_input_tokens`,
`cache_read_input_tokens`), `message.model`, `timestamp`, `gitBranch`, `sessionId`.
Subagent totals come from each `Agent` tool_result's `subagent_tokens`.

## Phase detection

Phase boundaries are `Skill` tool_use calls in the transcript:

| Skill invoked | Phase |
|---|---|
| `superpowers:brainstorming` | spec |
| `superpowers:writing-plans` | plan |
| `superpowers:subagent-driven-development`, `executing-plans`, `test-driven-development` | execute |
| (before any of the above) | other |

Each turn's tokens are attributed to the phase in effect at that turn. Subagent
tokens attach to the phase active at dispatch.

## Cost derivation

`tokens × price[model]`, cache-aware: cache_read ≈ 0.1× input, cache_create ≈ 1.25×
input, output at output rate. Prices live in `prices.json`, keyed by model id.
Stale prices = wrong cost, so keep that file current.

## Automatable vs judgment

The **miner is deterministic and unit-tested** (fixture transcript + fixture git log →
asserted table). The **effectiveness read is judgment** — a rise in execute cost may
mean the spec was over-cut, or the feature was just harder. The pipeline surfaces
candidates (e.g. spec shrank AND execute cost > 2× median); a human makes the call.
Do not treat any output number as a verdict.

## Layout

- `mine.py` — session JSONL → per-(session×phase) rows (CSV/JSON)
- `prices.json` — model price table (cache-aware)
- `tests/` — fixture transcripts + expected output
- generated data (`*.csv`, `out/`) is gitignored
