# Compact-Spec Parsimony Rules — Implementation Plan

> **For agentic workers:** two surgical edits to one skill file, then a 2-arm A/B eval. Small enough to execute inline (not subagent-driven). Steps use `- [ ]`.

**Goal:** Make `brainstorming/SKILL.md` produce specs that state each fact once and are cheap to produce, then A/B it against stock upstream v6.1.1.

**Architecture:** Two text replacements in `skills/brainstorming/SKILL.md` (Region A: canonical section set; Region B: 5-step review + conditional prose battery). Validation reuses `scratchpad/probe.sh` with baseline = v6.1.1.

**Tech Stack:** Markdown skill content; bash/python probe harness; quorum eval on claude/opus subscription.

## Global Constraints

- Repo: fork `jbroll/superpowers`, `/home/john/src/superpowers`. Branch `spec-sequencing-boundary`. Do NOT touch the evals repo for the skill edit.
- Spec: `docs/superpowers/specs/2026-07-23-compact-spec-parsimony-rules-design.md`.
- Behavior-shaping content: edits are surgical to the two named regions only. Do not touch Red-Flags tables, rationalization lists, or "human partner" language.
- `bun` at `~/.bun/bin/bun`; subscription token at `~/.claude-token`; scenario needs `SUPERPOWERS_ROOT` set per-arm.
- Baseline ref: stock upstream **v6.1.1** = `d884ae0`. Treatment: fork HEAD + this change.

---

### Task 1: Edit brainstorming/SKILL.md

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (Region A lines 84 & 86; Region B the Spec Self-Review block)

**Model:** `sonnet` — surgical edits to tuned behavior-shaping content; precision matters.

- [ ] **Step 1: Region A — replace the "Cover:" bullet with the canonical section set**

Replace this exact line:

```
- Cover: architecture, components, data flow, error handling, testing
```

with:

```
- Use a canonical section set, each fact in exactly one section: **Goal**, **Scope / Non-goals**, **Data model**, **Behavior contract** (what each operation does), **Failure contract** (errors, codes, paths), **Binding constraints** (repo-enforced, measured), **Testing** (a named list — one entry per behavior/failure/edge, *by reference*: "unknown input → error", not a re-description). State each requirement, failure mode, and constraint ONCE, in its owner section; later sections reference it, never restate it. Do not add a "Success criteria" / "Acceptance criteria" section — the contracts and Binding constraints are the acceptance criteria.
```

- [ ] **Step 2: Region A — replace the scale/cut bullet**

Replace this exact line:

```
- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced. Treat that figure as a ceiling, not a target — then cut every section with the rules in Spec Self-Review below. Use every word the content requires and no more; length is the outcome of the cut rules, not a number you aim for.
```

with:

```
- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced. Write it compact the first time; length is the outcome of stating each fact once, not a target.
```

- [ ] **Step 3: Region B — replace the entire Spec Self-Review block**

Replace this exact block (the 7-step review):

```
**Spec Self-Review:**
After writing the spec document, look at it with fresh eyes:

1. **Placeholder scan:** Any "TBD", "TODO", incomplete sections, or vague requirements? Fix them.
2. **Internal consistency:** Do any sections contradict each other? Does the architecture match the feature descriptions?
3. **Scope check:** Is this focused enough for a single implementation plan, or does it need decomposition?
4. **Sequencing scan:** Did a build order, commit sequence, or phase-by-phase task breakdown creep in? Cut it — writing-plans derives ordering fresh under code-parsimony. Keep target design, move maps, and acceptance criteria.
5. **Ambiguity check:** Could any requirement be interpreted two different ways? If so, pick one and make it explicit.
6. **Required sections:** Does the spec carry a *Binding constraints* section (what the repo enforces that this work must respect, with measured current values) and a failure-contract section (which errors, on which paths, with what codes)? Both are exempt from the cut rules. If missing or empty, write them.
7. **Cut padding:** Every sentence must earn its place.
   - **Boilerplate test** (before writing): if a competent implementer *new to this repo* would get this right from general engineering knowledge, don't write it. Project-specific facts — enforced caps, path conventions, landing mechanics, exact values, and where a value comes from and when it is available — fail this test and stay.
   - **Sentence test** (after writing): if removing a sentence changes nothing the reader learns, delete it. Apply hardest to the first and last sentence of each paragraph.
   - **Delete on sight:** "Note that", "It is important to", "This section describes/covers", "In order to X" → "To X", filler adverbs (generally/typically/usually/often), setup sentences ("There are three reasons"), closing restatements ("This is why X matters"), transition sentences carrying no information, any sentence restating a heading.
   - **Completeness test:** a section is done when two different phrasings would produce identical behavior — not when it is long or short.
   - Prefer active voice with a named agent, and specific over general ("retries three times with 500 ms backoff", not "retries as needed").
   - **Never cut:** constraints the repo enforces (size caps, lint gates, path conventions), ownership and landing mechanics (worktree, branch, land command), failure contracts (which errors, on which paths, with what codes), and exact values (ports, issuers, header names, limits). Parsimony trims reasoning, never measurements.

Fix any issues inline. No need to re-review — just fix and move on.
```

with:

```
**Spec Self-Review:**
After writing, a quick structural pass — expensive prose-cutting only where a section reads padded:

1. **Placeholder scan:** Any "TBD", "TODO", or vague requirement? Fix them.
2. **Consistency & scope:** Sections agree; focused enough for a single implementation plan (else decompose).
3. **Sequencing scan:** Did a build order, commit sequence, or phase-by-phase task breakdown creep in? Cut it — writing-plans derives ordering fresh under code-parsimony. Keep target design, move maps, and acceptance criteria.
4. **Ambiguity check:** Could any requirement be read two ways? Pick one and make it explicit.
5. **Single source of truth & required sections:** The spec carries a *Binding constraints* section (repo-enforced values, measured) and a *failure-contract* section, both non-empty and exempt from cutting. Each requirement, failure mode, and constraint appears in exactly one owner section (Behavior contract / Failure contract / Binding constraints / Data model); any fact stated in a second section → replace with a reference or delete it. No "Success/Acceptance" section — the contracts are the acceptance criteria; Testing lists tests by reference, not re-described behavior. This is where cross-section duplication gets cut.
6. **Cut padding — only if a section reads padded:** apply the tests below; skip an already-tight section.
   - **Boilerplate test:** if a competent implementer *new to this repo* would get it right from general engineering knowledge, don't write it. Project-specific facts — enforced caps, path conventions, landing mechanics, exact values — stay.
   - **Sentence test:** if removing a sentence changes nothing the reader learns, delete it. Apply hardest to the first and last sentence of each paragraph.
   - **Delete on sight:** "Note that", "It is important to", "This section describes/covers", "In order to X" → "To X", filler adverbs, setup sentences, closing restatements, any sentence restating a heading.
   - **Never cut:** constraints the repo enforces, ownership and landing mechanics, failure contracts, and exact values. Parsimony trims restatement and reasoning, never the fact's single canonical statement.

Fix any issues inline. No need to re-review — just fix and move on.
```

- [ ] **Step 4: Verify the edits landed and no other region changed**

Run: `cd /home/john/src/superpowers && git diff --stat skills/brainstorming/SKILL.md`
Expected: only `skills/brainstorming/SKILL.md` changed. Confirm by eye that the "Success/Acceptance" prohibition and "Single source of truth" step are present and the old "Completeness test"/"Cover: architecture" lines are gone:
Run: `grep -c "Completeness test\|Cover: architecture" skills/brainstorming/SKILL.md` → expect `0`; `grep -c "Single source of truth\|canonical section set" skills/brainstorming/SKILL.md` → expect `2`.

- [ ] **Step 5: Commit**

```bash
cd /home/john/src/superpowers
git add skills/brainstorming/SKILL.md
git commit -m "skills: compact-spec rules — single-source, lighter self-review"
```

---

### Task 2: A/B eval vs stock v6.1.1

**Files:**
- Create: `scratchpad/probe2.sh` (adapted from `scratchpad/probe.sh`)

**Model:** `sonnet` — running a harness and interpreting results against reject conditions.

**Interfaces:**
- Consumes: Task 1's commit (the treatment ref = new fork HEAD).
- Produces: per-arm medians for spec bytes/lines, total_output, est_cost_usd, duration, gauntlet pass-rate; the treatment−baseline delta judged against the spec's three reject conditions.

- [ ] **Step 1: Create the two worktrees (baseline v6.1.1, treatment new HEAD)**

```bash
cd /home/john/src/superpowers
WT=/home/john/src/superpowers/.probe-worktrees; rm -rf "$WT"
git worktree add --detach "$WT/baseline"  d884ae0     # stock upstream v6.1.1
git worktree add --detach "$WT/treatment" HEAD        # fork + Task 1 change
# sanity: treatment has code-parsimony skill + the new rule; baseline does not
grep -c "Single source of truth" "$WT/treatment/skills/brainstorming/SKILL.md"   # expect 1
grep -c "Single source of truth" "$WT/baseline/skills/brainstorming/SKILL.md"    # expect 0
```

- [ ] **Step 2: Write `scratchpad/probe2.sh`**

Same structure as `scratchpad/probe.sh` (interleaved n=5, TSV output), with two changes: baseline worktree points at v6.1.1, and each run also records spec-doc lines/bytes. Full script:

```bash
#!/usr/bin/env bash
set -uo pipefail
export PATH="$HOME/.bun/bin:$PATH"
EVALS=/home/john/src/superpowers/evals
WT=/home/john/src/superpowers/.probe-worktrees
OUT=/home/john/src/superpowers/evals/.superpowers/probe2
mkdir -p "$OUT"
TSV="$OUT/results.tsv"
SCEN=scenarios/cost-spec-plan-duplication
set -a; . ~/.claude-token; set +a
unset ANTHROPIC_API_KEY AWS_BEARER_TOKEN_BEDROCK 2>/dev/null || true
cd "$EVALS"
printf 'arm\trep\tfinal\tspec_lines\tspec_bytes\ttotal_output\test_cost_usd\ttotal_tokens\tduration_ms\trun_dir\n' > "$TSV"
run_one() {
  local arm="$1" rep="$2" root="$3"
  local log="$OUT/run-${arm}-${rep}.log"
  SUPERPOWERS_ROOT="$root" bun run quorum run "$SCEN" --coding-agent claude --credential opus > "$log" 2>&1
  local rd; rd=$(grep 'run-dir' "$log" | grep -oE '/home/[^ ]+' | head -1)
  local final="unknown" sl="" sb="" out="" cost="" tot="" dur=""
  if [[ -n "$rd" && -f "$rd/verdict.json" ]]; then
    final=$(python3 -c "import json;print(json.load(open('$rd/verdict.json')).get('final','?'))" 2>/dev/null || echo "?")
    read out cost tot dur < <(python3 -c "
import json,glob,os
u='$rd/coding-agent-token-usage.json'
d=json.load(open(u)) if os.path.isfile(u) else {}
print(d.get('total_output',''), d.get('est_cost_usd',''), d.get('total_tokens',''), d.get('duration_ms',''))" 2>/dev/null)
    read sl sb < <(python3 -c "
import glob,os
fs=glob.glob('$rd/coding-agent-workdir/docs/superpowers/specs/*.md') or glob.glob('$rd/coding-agent-workdir/docs/specs/*.md')
if fs:
    f=max(fs,key=os.path.getsize); t=open(f,encoding='utf-8',errors='replace').read()
    print(t.count(chr(10))+1, len(t.encode()))
else: print('','')" 2>/dev/null)
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$arm" "$rep" "$final" "$sl" "$sb" "$out" "$cost" "$tot" "$dur" "$rd" >> "$TSV"
  echo "[$(date +%H:%M:%S)] $arm rep$rep -> $final spec=${sl}L/${sb}B out=$out cost=$cost"
}
for rep in 1 2 3 4 5; do
  run_one baseline  "$rep" "$WT/baseline"
  run_one treatment "$rep" "$WT/treatment"
done
echo "PROBE2_DONE"
```

- [ ] **Step 3: Launch in background (10 runs, ~45–60 min)**

```bash
chmod +x /home/john/src/superpowers/evals/scratchpad/probe2.sh 2>/dev/null; \
bash /home/john/src/superpowers/evals/scratchpad/probe2.sh
```
Run in background; verify the first baseline run produced a results dir and a growing transcript before leaving it unattended.

- [ ] **Step 4: Aggregate and judge against reject conditions**

After `PROBE2_DONE`, compute per-arm medians (spec_lines, spec_bytes, total_output, est_cost_usd, duration_ms) and pass counts, and the treatment−baseline deltas. Judge against the spec's three reject conditions:
1. Outcome regression — treatment pass-rate < baseline → reject.
2. No compactness gain — treatment spec bytes/lines not lower → structural change failed.
3. Cost regression — treatment output/cost/duration materially above baseline → "cheap" goal failed.

- [ ] **Step 5: Remove the worktrees**

```bash
cd /home/john/src/superpowers
git worktree remove --force .probe-worktrees/baseline
git worktree remove --force .probe-worktrees/treatment
rmdir .probe-worktrees 2>/dev/null || true
```

- [ ] **Step 6: Report the result and recommendation (ship / revise / reject) to the user.**
