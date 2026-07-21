# Parsimony Cut Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bias plan/code writing toward minimal solutions and cut padding from brainstorming and plan output, without adding commands or changing skill triggering.

**Architecture:** One new fork-local skill (`code-parsimony`) carries ponytail's YAGNI ladder. A shared prose "cut rules" block (harvested from ai-roller's `specification` skill) is inserted into the self-review passes of `brainstorming` and `writing-plans`. Validation is a manual before/after comparison, with the eval harness optional.

**Tech Stack:** Markdown skill files. Bash for verification. Optional: `evals/` submodule (superpowers-evals).

## Global Constraints

- Skills are behavior-shaping content; CLAUDE.md flags `brainstorming`/`writing-plans` as high-bar. Do not reword beyond the specified insertions.
- No new commands. No change to when any skill triggers.
- `code-parsimony` is fork-local and additive (no upstream conflict). The edits to `brainstorming`/`writing-plans` modify upstream files and will conflict on `sync-upstream.sh` — expected for a fork; resolve in favor of keeping the cut-rules block.
- Credit ponytail (MIT, github.com/DietrichGebert/ponytail) inside the new skill.
- No word cap. Length is an outcome of the cut rules, judged by the completeness test.
- Commit messages end with the repo's required Co-Authored-By / Claude-Session trailers.

---

### Task 1: Create the `code-parsimony` skill

**Files:**
- Create: `skills/code-parsimony/SKILL.md`

**Model:** `sonnet` — new behavior-shaping skill; description/trigger wording needs judgment even though the body is supplied.

**Interfaces:**
- Produces: a skill named `code-parsimony`, auto-discovered from `skills/*/SKILL.md`, that triggers on plan/code writing. Later tasks reference it by name in the "After Writing" pairing with `verification-before-completion`.

- [ ] **Step 1: Write the skill file**

Create `skills/code-parsimony/SKILL.md` with exactly this content:

```markdown
---
name: code-parsimony
description: Use when writing code or an implementation plan - biases toward the fewest lines and steps that fully solve the problem. Triggers on writing plans, implementing a feature, adding code, "simplest way", "minimal", "do we need this".
---

# Code Parsimony

Write the least code that fully solves the problem. The best code is the code you never wrote — it can't break, can't confuse the next reader, and costs nothing to maintain.

Adapted from the ponytail skill (github.com/DietrichGebert/ponytail, MIT).

## The Ladder

Before writing an implementation, walk this ladder and stop at the first rung that works:

1. **Does it need to exist?** (YAGNI) Does the task actually require this piece, or is it speculative? If speculative, don't build it.
2. **Does it already exist?** Reuse code already in this codebase before writing new code.
3. **Does the standard library do it?** Reach for stdlib before custom code.
4. **Is it a native platform feature?** Use the platform before a dependency.
5. **Does an already-installed dependency do it?** Use what's on hand before adding a new dependency.
6. **Can it be one line?** If one line is clear, write one line.
7. **Otherwise:** the minimum viable code that fully solves the problem.

## Non-Negotiable

Parsimony never means skipping input validation, error handling, security, or accessibility. These are part of "fully solves the problem," not padding to cut.

## Rules

- Understand the problem fully before simplifying. Minimal code that solves the wrong problem is not parsimony.
- Deletion over addition. When a change lets you remove code, remove it.
- Boring beats clever. The next reader — often you — should understand it without effort.
- No unrequested abstraction or boilerplate. Don't add a layer for a second case that doesn't exist yet.
- Mark a deliberate shortcut with a comment naming when to upgrade: `// single-tenant for now; revisit when we add orgs`.

## After Writing

One pass before you call it done: what can I delete without losing behavior? This pairs with superpowers:verification-before-completion — run the pass there.
```

- [ ] **Step 2: Verify the file and frontmatter**

Run: `head -4 skills/code-parsimony/SKILL.md && echo "---" && grep -c '^name: code-parsimony$' skills/code-parsimony/SKILL.md`
Expected: frontmatter prints; grep count is `1`.

- [ ] **Step 3: Verify the skill is discoverable**

Run: `ls skills/code-parsimony/SKILL.md && grep -rl 'name: code-parsimony' skills/`
Expected: path prints; grep finds the file.

- [ ] **Step 4: Commit**

```bash
git add skills/code-parsimony/SKILL.md
git commit -m "skills: add code-parsimony (ponytail YAGNI ladder, MIT)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01S4ru6HouiqD8syxQLLwr2L"
```

---

### Task 2: Add cut rules to `brainstorming`

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (Present-design bullet ~line 84; Spec Self-Review block ~lines 112-124)

**Model:** `sonnet` — editing eval-tuned content; must place exact text without disturbing surrounding instructions.

**Interfaces:**
- Consumes: nothing.
- Produces: the shared cut-rules block, also used verbatim in Task 3.

- [ ] **Step 1: Subordinate the word figure to the cut rules**

Replace this line in `skills/brainstorming/SKILL.md`:

```
- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced
```

with:

```
- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced. Treat that figure as a ceiling, not a target — then cut every section with the rules in Spec Self-Review below. Use every word the content requires and no more; length is the outcome of the cut rules, not a number you aim for.
```

- [ ] **Step 2: Add the cut-rules step to Spec Self-Review**

In the `**Spec Self-Review:**` section, replace this line:

```
Fix any issues inline. No need to re-review — just fix and move on.
```

with:

```
5. **Cut padding:** Every sentence must earn its place.
   - **Boilerplate test** (before writing): if a competent implementer would get this right without being told, don't write it.
   - **Sentence test** (after writing): if removing a sentence changes nothing the reader learns, delete it. Apply hardest to the first and last sentence of each paragraph.
   - **Delete on sight:** "Note that", "It is important to", "This section describes/covers", "In order to X" → "To X", filler adverbs (generally/typically/usually/often), setup sentences ("There are three reasons"), closing restatements ("This is why X matters"), transition sentences carrying no information, any sentence restating a heading.
   - **Completeness test:** a section is done when two different phrasings would produce identical behavior — not when it is long or short.
   - Prefer active voice with a named agent, and specific over general ("retries three times with 500 ms backoff", not "retries as needed").

Fix any issues inline. No need to re-review — just fix and move on.
```

- [ ] **Step 3: Verify both edits landed**

Run: `grep -c 'ceiling, not a target' skills/brainstorming/SKILL.md && grep -c 'Boilerplate test' skills/brainstorming/SKILL.md && grep -c 'Delete on sight' skills/brainstorming/SKILL.md`
Expected: each prints `1`.

- [ ] **Step 4: Verify no self-review item was dropped**

Run: `grep -nE '^\s*[0-9]\.' skills/brainstorming/SKILL.md | grep -iE 'placeholder|consistency|scope|ambiguity|cut padding'`
Expected: five numbered items present (Placeholder, Internal consistency, Scope, Ambiguity, Cut padding).

- [ ] **Step 5: Commit**

```bash
git add skills/brainstorming/SKILL.md
git commit -m "skills: add prose cut rules to brainstorming spec self-review

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01S4ru6HouiqD8syxQLLwr2L"
```

---

### Task 3: Add cut rules to `writing-plans`

**Files:**
- Modify: `skills/writing-plans/SKILL.md` (Self-Review section ~lines 166-180)

**Model:** `sonnet` — editing eval-tuned content; exact placement matters.

**Interfaces:**
- Consumes: the cut-rules block wording from Task 2 (repeated here in full — do not reference Task 2).

- [ ] **Step 1: Add the cut-rules item to Self-Review**

In the `## Self-Review` section of `skills/writing-plans/SKILL.md`, replace this line:

```
If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task.
```

with:

```
**4. Cut padding:** Plan steps carry code and commands, which stay verbatim — but the prose around them must earn its place.
- **Boilerplate test** (before writing): if a competent engineer would get this right without being told, don't write it.
- **Sentence test** (after writing): if removing a sentence changes nothing the engineer learns, delete it. Apply hardest to the first and last sentence of each paragraph.
- **Delete on sight:** "Note that", "It is important to", "This section describes/covers", "In order to X" → "To X", filler adverbs (generally/typically/usually/often), setup sentences, closing restatements, transition sentences carrying no information, any sentence restating a heading.
- Never cut required content: file paths, complete code, exact commands, expected output. Parsimony trims prose, not the executable substance of a step.

If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task.
```

- [ ] **Step 2: Verify the edit landed**

Run: `grep -c 'Cut padding' skills/writing-plans/SKILL.md && grep -c 'not the executable substance' skills/writing-plans/SKILL.md`
Expected: each prints `1`.

- [ ] **Step 3: Verify the Self-Review checklist is intact**

Run: `grep -nE '\*\*[0-9]\.' skills/writing-plans/SKILL.md | grep -iE 'coverage|placeholder|consistency|cut padding'`
Expected: four numbered items present (Spec coverage, Placeholder scan, Type consistency, Cut padding).

- [ ] **Step 4: Commit**

```bash
git add skills/writing-plans/SKILL.md
git commit -m "skills: add prose cut rules to writing-plans self-review

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01S4ru6HouiqD8syxQLLwr2L"
```

---

### Task 4: Validate parsimony holds behavior

**Files:**
- Create: `docs/superpowers/specs/2026-07-20-parsimony-validation.md` (validation notes)

**Model:** `sonnet` — judgment call comparing before/after output quality, not mechanical.

**Interfaces:**
- Consumes: the three edited/created skills from Tasks 1-3.

- [ ] **Step 1: Check whether the eval harness is available**

Run: `test -f evals/README.md && echo "evals present" || echo "evals absent — use manual validation"`
Expected: prints one of the two. If "evals present", run the brainstorming/writing-plans evals per `evals/README.md` and record token deltas; then continue to Step 2 for the behavior check either way.

- [ ] **Step 2: Manual before/after on a representative prompt**

Pick a small representative request (e.g. "add a `--json` flag to an existing CLI command"). In two scratch sessions — one with the three changes reverted (`git stash`), one with them applied — run brainstorming through to a written spec, and note for each:
- word count of the presented design sections and the written spec
- whether the design was still presented section-by-section with approval gates
- whether the spec still passes its own completeness test (a skilled agent could implement it with no clarifying questions)

Record the two word counts and the three yes/no behavior checks in `docs/superpowers/specs/2026-07-20-parsimony-validation.md`.

- [ ] **Step 3: Confirm acceptance criteria**

Acceptance: applied output has a lower word count than reverted output for the same request, AND all three behavior checks are "yes" (gates intact, sections presented, spec still complete). If word count did not drop, the cut rules aren't firing — revisit Task 2/3 wording. If any behavior check flipped to "no", the edits over-cut — revisit.

Run: `test -f docs/superpowers/specs/2026-07-20-parsimony-validation.md && grep -qiE 'word count' docs/superpowers/specs/2026-07-20-parsimony-validation.md && echo "validation recorded"`
Expected: `validation recorded`.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-07-20-parsimony-validation.md
git commit -m "docs: record parsimony before/after validation

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01S4ru6HouiqD8syxQLLwr2L"
```

---

## Self-Review

**1. Spec coverage:**
- Code parsimony skill → Task 1. ✓
- Port cut rules into brainstorming → Task 2. ✓
- Port cut rules into writing-plans → Task 3. ✓
- No word cap / length is outcome → Task 2 Step 1. ✓
- Strip ai-roller plumbing → cut-rules block contains none of `air check`/Route Skill/index.md. ✓
- Eval validation (with local caveat) → Task 4. ✓
- Ponytail MIT credit → Task 1 skill body + Global Constraints. ✓
- Deferred (pruning, subagent-exec pass) → intentionally not in this plan. ✓

**2. Placeholder scan:** No TBD/TODO. Every edit gives exact before/after text and exact verify commands. Task 4's representative prompt is an example, not a placeholder — the engineer picks any small request.

**3. Type consistency:** Skill name `code-parsimony` used consistently. The cut-rules block wording is repeated in full in Tasks 2 and 3 (not cross-referenced), with Task 3 adapting the "never cut" clause for code/commands.
