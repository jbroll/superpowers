# Parsimony Protected Content Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop the prose cut rules from deleting repo-derived facts, by protecting constraints and failure contracts in `brainstorming` and `writing-plans`.

**Spec:** `docs/superpowers/specs/2026-07-22-parsimony-protected-content-design.md` — problem, evidence, and rationale live there; this plan does not restate them.

**Architecture:** Five text edits across two SKILL.md files, then one new eval scenario that reproduces the KinoQ/rowboat size-cap incident as a pass/fail fixture.

**Tech Stack:** Markdown skill files, bash, the quorum eval harness (`evals/`).

## Global Constraints

- Repo `/home/john/src/superpowers`, branch `spec-sequencing-boundary`, main checkout — no worktree. No remote push.
- `skills/brainstorming/SKILL.md` has an **uncommitted working-tree edit** (the parked sequencing change: a `Cover the target state…` bullet at line 87 and a `**Sequencing scan:**` self-review item at line 118). Do not commit it, do not revert it, do not reformat around it. `git add` only the specific files each task names.
- Anchor every edit on quoted content, never on line number — the parked edit shifts self-review numbering.
- No size cap, commit hook, lefthook, or `package.json` script exists in this repo. `scripts/padding-lint.sh FILE...` is the only prose gate; exit 1 on any flag.
- CLAUDE.md places both SKILL.md files in the high-bar zone. Do not reword Red Flags tables or "human partner" language. Change only the text these steps quote.
- Live eval runs launch real agent CLIs and are a trusted-maintainer operation. Task 2 authors and structurally validates the scenario; it does NOT run a live eval.
- Sessions load `/home/john/.claude/plugins/cache/superpowers-dev/superpowers/6.1.1/skills/`, a plain directory copy. Nothing in this plan touches it; syncing is a manual post-plan step.
- **`evals/` is gitignored in this repo** (`.gitignore:13`) and is a separate git repo with remote `ssh://git@github.com/prime-radiant-inc/superpowers-evals.git`. Task 2 commits inside `evals/`, never from the superpowers root. Do not push; local commit only.

---

### Task 1: Protect constraints and failure contracts in both skill files

**Files:**
- Modify: `skills/brainstorming/SKILL.md`
- Modify: `skills/writing-plans/SKILL.md`

**Model:** `sonnet` — behavior-shaping prose in the high-bar zone, edited around a parked uncommitted change; anchors need judgment even though the replacement text is given verbatim.

**Interfaces:**
- Consumes: nothing.
- Produces: the exact strings `new to this repo`, `Never cut: constraints the repo enforces`, `Required sections:`, `Measure before you write.`, and `Global Constraints block` — Task 2's fixture prose is independent, but the final verification greps these.

- [ ] **Step 1: Record the pre-edit state**

Run:
```bash
cd /home/john/src/superpowers
grep -n "Boilerplate test" skills/brainstorming/SKILL.md skills/writing-plans/SKILL.md
```
Expected: exactly two hits — `skills/brainstorming/SKILL.md:121` and `skills/writing-plans/SKILL.md:178`. If the count differs, stop and report; the file has drifted from the plan.

- [ ] **Step 2: Narrow the boilerplate test in `brainstorming`**

In `skills/brainstorming/SKILL.md`, replace this line:

```markdown
   - **Boilerplate test** (before writing): if a competent implementer would get this right without being told, don't write it.
```

with:

```markdown
   - **Boilerplate test** (before writing): if a competent implementer *new to this repo* would get this right from general engineering knowledge, don't write it. Project-specific facts — enforced caps, path conventions, landing mechanics, exact values, and where a value comes from and when it is available — fail this test and stay.
```

- [ ] **Step 3: Add the protected-content list to `brainstorming`**

In the same `**Cut padding:**` block, immediately after the line beginning `   - Prefer active voice with a named agent`, add:

```markdown
   - **Never cut:** constraints the repo enforces (size caps, lint gates, path conventions), ownership and landing mechanics (worktree, branch, land command), failure contracts (which errors, on which paths, with what codes), and exact values (ports, issuers, header names, limits). Parsimony trims reasoning, never measurements.
```

- [ ] **Step 4: Add the required-sections self-review item to `brainstorming`**

Insert a new numbered item **immediately before** the `**Cut padding:**` item, and renumber `Cut padding` to follow it. With the parked sequencing edit present, `Cut padding` is item 6, so the new item becomes 6 and `Cut padding` becomes 7. (If the parked edit is absent, they become 5 and 6.) The new item reads:

```markdown
6. **Required sections:** Does the spec carry a *Binding constraints* section (what the repo enforces that this work must respect, with measured current values) and a failure-contract section (which errors, on which paths, with what codes)? Both are exempt from the cut rules. If missing or empty, write them.
```

- [ ] **Step 5: Add the measurement gate to `brainstorming`**

In the `**Working in existing codebases:**` list, after the line beginning `- Don't propose unrelated refactoring`, add:

```markdown
- **Measure before you write.** For each file the work will touch, read it and record: current size against any cap the repo enforces, the exact values the design depends on (names, ports, headers, limits), and which gates run on commit. Record measured numbers, not estimates. These land in Binding constraints.
```

- [ ] **Step 6: Narrow the boilerplate test in `writing-plans`**

In `skills/writing-plans/SKILL.md`, replace this line:

```markdown
- **Boilerplate test** (before writing): if a competent engineer would get this right without being told, don't write it.
```

with:

```markdown
- **Boilerplate test** (before writing): if a competent engineer *new to this repo* would get this right from general engineering knowledge, don't write it. Project-specific facts — enforced caps, path conventions, landing mechanics, exact values, and where a value comes from and when it is available — fail this test and stay.
```

- [ ] **Step 7: Extend the `writing-plans` protected list**

In `skills/writing-plans/SKILL.md`, replace this line:

```markdown
- Never cut required content: file paths, complete code, exact commands, expected output. Parsimony trims prose, not the executable substance of a step.
```

with:

```markdown
- Never cut required content: file paths, complete code, exact commands, expected output, and the Global Constraints block — repo, branch/worktree, landing command, version floors, enforced caps. Parsimony trims reasoning, never measurements.
```

- [ ] **Step 8: Verify every edit landed**

Run:
```bash
cd /home/john/src/superpowers
grep -c "new to this repo" skills/brainstorming/SKILL.md skills/writing-plans/SKILL.md
grep -c "Never cut" skills/brainstorming/SKILL.md skills/writing-plans/SKILL.md
grep -c "Required sections:\|Measure before you write\." skills/brainstorming/SKILL.md
grep -c "Global Constraints block" skills/writing-plans/SKILL.md
```
Expected: `1` for every count on every file listed (the third command prints `2`).

- [ ] **Step 9: Verify the parked edit is untouched and self-review numbering is sane**

Run:
```bash
cd /home/john/src/superpowers
grep -n "Sequencing scan:" skills/brainstorming/SKILL.md
grep -nE "^[0-9]+\. \*\*" skills/brainstorming/SKILL.md
```
Expected: the `Sequencing scan:` item still present; the numbered self-review items run `1.` through `7.` with no gaps or repeats.

- [ ] **Step 10: Run the padding gate**

Run:
```bash
cd /home/john/src/superpowers
scripts/padding-lint.sh skills/brainstorming/SKILL.md skills/writing-plans/SKILL.md
```
Expected: `total padding flags: 4`, exit 1 — **unchanged from the pre-edit baseline**. The four
are pre-existing and none are in text this plan supplies: `brainstorming` "often" (the
well-bounded-units bullet) and its `Delete on sight` line; `writing-plans` "usually" (the
model-tier paragraph) and its `Delete on sight` line. The two `Delete on sight` hits are
structural false positives — those lines quote the filler adverbs they ban.

The gate must not regress: compare against the baseline rather than against zero.

```bash
cd /home/john/src/superpowers
git show HEAD:skills/brainstorming/SKILL.md > /tmp/base-brainstorming.md
git show HEAD:skills/writing-plans/SKILL.md > /tmp/base-writing-plans.md
scripts/padding-lint.sh /tmp/base-brainstorming.md /tmp/base-writing-plans.md | tail -1
```
Expected: `total padding flags: 4` — the same count. A higher post-edit count means this plan's
text introduced padding; report it rather than rewording, since the wording is spec-approved.

- [ ] **Step 11: Commit**

```bash
cd /home/john/src/superpowers
git add skills/brainstorming/SKILL.md skills/writing-plans/SKILL.md
git commit -m "skills: protect constraints and failure contracts from the cut rules

Narrow the boilerplate test to a reader new to the repo, give brainstorming
the protected-content list it never had, require Binding constraints and
failure-contract sections, add the measurement gate, and extend writing-plans'
protected list to cover Global Constraints.

Spec: docs/superpowers/specs/2026-07-22-parsimony-protected-content-design.md

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

Note: `git add` names both files explicitly so the parked sequencing edit in the same file is carried along — that is expected and correct, since it lives in `brainstorming/SKILL.md`. If `git status` shows the commit would also include unrelated files, stop and report.

---

### Task 2: Eval scenario — a spec must record an enforced constraint

**Files:**
- Create: `evals/scenarios/spec-records-enforced-constraint/story.md`
- Create: `evals/scenarios/spec-records-enforced-constraint/setup.sh`
- Create: `evals/scenarios/spec-records-enforced-constraint/checks.sh`

**Model:** `sonnet` — fixture design plus harness-DSL conventions; the files are given verbatim but the structural validation needs judgment.

**Interfaces:**
- Consumes: nothing from Task 1 (the scenario tests behavior, not file content).
- Produces: scenario id `spec-records-enforced-constraint`.

**Harness facts measured for this task** (do not re-derive):
- A scenario is exactly three files: `story.md` (YAML frontmatter + QA-agent story + `## Acceptance Criteria`), `setup.sh`, `checks.sh` (`pre()` and `post()`).
- `setup.sh` runs with `$QUORUM_WORKDIR` set and must `cd` into it.
- `file-exists` supports globs; **`file-contains` does not** — it resolves a literal path. For glob-matched files use `command-succeeds` with a `grep` (it runs via `bash -c`).

- [ ] **Step 1: Create the scenario directory**

```bash
mkdir -p /home/john/src/superpowers/evals/scenarios/spec-records-enforced-constraint
```

- [ ] **Step 2: Write `setup.sh`**

Create `evals/scenarios/spec-records-enforced-constraint/setup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$QUORUM_WORKDIR"
git init -qb main
git config user.email "drill@test.local"
git config user.name "Drill Test"

mkdir -p src scripts .githooks

# A production file 8 lines under an enforced 500-line cap.
{
  echo "// Session state for the editor. Owns the open document and its history."
  echo "export const MAX_HISTORY = 100;"
  echo ""
  echo "export function createSession(docId) {"
  echo "  return { docId, history: [], cursor: 0 };"
  echo "}"
  for i in $(seq 1 486); do
    echo "export function sessionHelper$i(s) { return s; }"
  done
} > src/session.js

cat > scripts/check-size.sh <<'SH'
#!/usr/bin/env bash
# Production source files are capped at 500 lines. Enforced on commit.
set -euo pipefail
status=0
for f in $(git diff --cached --name-only --diff-filter=ACM | grep -E '^src/.*\.js$' || true); do
  [ -f "$f" ] || continue
  n=$(wc -l < "$f")
  if [ "$n" -gt 500 ]; then
    echo "size cap: $f is $n lines, limit is 500" >&2
    status=1
  fi
done
exit $status
SH
chmod +x scripts/check-size.sh

cat > .githooks/pre-commit <<'SH'
#!/usr/bin/env bash
exec scripts/check-size.sh
SH
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks

cat > README.md <<'MD'
# editor fixture

Production source under `src/` is capped at **500 lines per file**, enforced on
commit by `scripts/check-size.sh` via the `pre-commit` hook.
MD

mkdir -p docs/superpowers/specs docs/superpowers/plans
git add -A
git commit -qm "initial: editor session fixture"
```

- [ ] **Step 3: Write `story.md`**

Create `evals/scenarios/spec-records-enforced-constraint/story.md`:

```markdown
---
id: spec-records-enforced-constraint
title: Spec records the enforced size cap and the target file's current size
status: ready
tags: spec-design
quorum_max_time: 20m
---

You are a developer who wants help DESIGNING a feature — not implementing
it yet, just a design.

When the agent is ready for input, tell it you want per-session draft
autosave: while someone edits a document, their unsaved changes should be
kept on the session so a reload restores them. Ask it to help you design
this.

Do NOT mention the line cap, do NOT mention `scripts/check-size.sh`, do NOT
mention the pre-commit hook, and do NOT mention how big any file is. If the
agent asks where the state should live, say "wherever fits the existing
session model." If it asks about persistence, say "in-memory on the session
is fine for now."

If the agent presents a design, accept it and let it proceed ("sounds good").
Once the agent has written a spec under `docs/superpowers/specs/`, you are
done.

## Acceptance Criteria

- The agent read `src/session.js` — the file the feature's state naturally
  belongs on — during design, rather than proposing a design without opening
  it.
- The written spec records the repo's enforced 500-line cap on `src/`
  production files. Naming the cap is the point; citing
  `scripts/check-size.sh` or the pre-commit hook as its source is a stronger
  pass.
- The written spec records `src/session.js`'s measured current size (492
  lines) or states equivalently that the file is within a few lines of the
  cap. An unquantified remark that the file is "large" is a fail — the
  criterion is a measured number, not an impression.
- The spec addresses the consequence: adding session state to a file 8 lines
  from an enforced cap requires an extraction or a new module. A design that
  silently adds state to `src/session.js` with no mention of the cap is the
  failure this scenario measures.
```

- [ ] **Step 4: Write `checks.sh`**

Create `evals/scenarios/spec-records-enforced-constraint/checks.sh`:

```bash
# Deterministic half of the scenario: the spec must carry the measured numbers.
# file-contains resolves a literal path and the spec's filename is agent-chosen,
# so the glob greps run through command-succeeds (bash -c).

pre() {
    git-repo
    git-branch main
    file-exists 'src/session.js'
    file-exists 'scripts/check-size.sh'
    not file-exists 'docs/superpowers/specs/*.md'
}

post() {
    check-transcript skill-called superpowers:brainstorming
    file-exists 'docs/superpowers/specs/*.md'
    # The enforced cap, by number.
    command-succeeds 'grep -qE "500[ -]?line|500 lines|limit is 500|cap.*500" docs/superpowers/specs/*.md'
    # The target file's measured current size.
    command-succeeds 'grep -qE "49[0-9]" docs/superpowers/specs/*.md'
}
```

- [ ] **Step 5: Verify the fixture builds and the cap is real**

Run:
```bash
cd /home/john/src/superpowers
rm -rf /tmp/qsetup && mkdir -p /tmp/qsetup
QUORUM_WORKDIR=/tmp/qsetup bash evals/scenarios/spec-records-enforced-constraint/setup.sh
wc -l < /tmp/qsetup/src/session.js
```
Expected: setup exits 0, and `wc -l` prints exactly `492`.

- [ ] **Step 6: Verify the enforced cap actually rejects an over-cap commit**

Run:
```bash
cd /tmp/qsetup
for i in $(seq 1 20); do echo "export function extra$i(s) { return s; }" >> src/session.js; done
git add src/session.js
git commit -qm "should be rejected"; echo "exit=$?"
```
Expected: the commit FAILS with `size cap: src/session.js is 512 lines, limit is 500` on stderr and `exit=1`. If it exits 0, the hook is not wired — fix `core.hooksPath` in `setup.sh` before continuing.

- [ ] **Step 7: Verify the post-check greps behave**

Run:
```bash
cd /tmp/qsetup && git checkout -- src/session.js
mkdir -p docs/superpowers/specs
printf '# Design\n\nsrc/session.js is at 492 lines against the enforced 500-line cap.\n' \
  > docs/superpowers/specs/2026-07-22-probe-design.md
grep -qE "500[ -]?line|500 lines|limit is 500|cap.*500" docs/superpowers/specs/*.md; echo "cap_grep=$?"
grep -qE "49[0-9]" docs/superpowers/specs/*.md; echo "size_grep=$?"
printf '# Design\n\nThe session file is quite large.\n' > docs/superpowers/specs/2026-07-22-probe-design.md
grep -qE "500[ -]?line|500 lines|limit is 500|cap.*500" docs/superpowers/specs/*.md; echo "neg_cap_grep=$?"
```
Expected: `cap_grep=0`, `size_grep=0`, `neg_cap_grep=1`. The negative case proves the check can fail — a post-check that passes on a spec saying only "quite large" would be vacuous.

- [ ] **Step 8: Clean up the probe**

```bash
rm -rf /tmp/qsetup
```

- [ ] **Step 9: Commit**

`evals/` is its own repo and is gitignored by superpowers, so this commit is made **inside `evals/`**:

```bash
cd /home/john/src/superpowers/evals
chmod +x scenarios/spec-records-enforced-constraint/setup.sh
git add scenarios/spec-records-enforced-constraint
git commit -m "scenario: spec must record an enforced size cap

Reproduces the KinoQ and rowboat incidents as a fixture: src/session.js at
492 lines under a pre-commit-enforced 500-line cap, and a feature whose state
naturally lands on that file. Pass = the spec records both numbers.

Spec: superpowers docs/superpowers/specs/2026-07-22-parsimony-protected-content-design.md

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

Do not push. Verify with `git -C /home/john/src/superpowers/evals log --oneline -1` and confirm `git -C /home/john/src/superpowers status --short` shows nothing new under `evals/`.

---

## Deferred acceptance — manual, after this plan

The spec's Acceptance requires eval evidence that this plan cannot produce: live runs launch
real agent CLIs under permissive flags and are a trusted-maintainer operation. Both remaining
items are manual:

1. **Run the new scenario and the five existing ones**, before and after the Task 1 commit:
   ```bash
   cd /home/john/src/superpowers/evals
   quorum run spec-records-enforced-constraint spec-writing-blind-spot \
     spec-reviewer-catches-planted-flaws sdd-spec-context-consumed \
     cost-spec-plan-duplication brainstorming-resists-jump-to-implementation
   ```
   Accept only if the new scenario passes, the five hold, and spec word count has not returned
   to pre-07-20 levels.
2. **Sync the plugin cache.** The edits are inert in live sessions until
   `/home/john/.claude/plugins/cache/superpowers-dev/superpowers/6.1.1/skills/` is refreshed —
   it is a plain directory copy, not a symlink or git checkout. This mutates the live plugin
   install, so it is a deliberate decision, not a plan step.

## Out of scope for this plan

- The parked sequencing change in `skills/brainstorming/SKILL.md`.
