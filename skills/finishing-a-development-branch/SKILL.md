---
name: finishing-a-development-branch
description: Use when implementation is complete - auto-land the branch onto main via rebase, ff-merge, and push, then clean up
---

# Finishing a Development Branch

## Overview

**Core principle:** Detect environment → Land (`land`, else manual rebase + ff-merge + push) → Clean up.

**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."

No menu. No test gate here: target repos enforce tests through their own commit hooks, and per-task implementer reports carry test evidence. Do not re-run the suite to decide whether to land, and do not ask what to do with completed work.

## Step 1: Detect Environment

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
# Capture now, while still inside the workspace — Step 2 changes directory
# before cleanup (Step 3) needs this value
WORKTREE_PATH=$(git rev-parse --show-toplevel)
BRANCH=$(git branch --show-current)
```

| State | Action |
|-------|--------|
| On a branch (normal repo or linked worktree) | Land (Step 2), then cleanup (Step 3) |
| Detached HEAD | Stop. Report: "Detached HEAD — cannot auto-land. Create a branch first." Leave everything in place. |

The base branch is always `main`. Do not ask which base.

## Step 2: Land

Prefer `land` — it auto-rebases the branch onto `main`, ff-merges, pushes `origin main`, and runs the repo's hooks:

```bash
BRANCH=$(git branch --show-current)
if command -v land >/dev/null 2>&1; then
  land "$BRANCH"
else
  # Manual fallback, mirroring land's guards
  MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
  WORKTREE_PATH=$(git rev-parse --show-toplevel)
  git -C "$WORKTREE_PATH" diff --quiet HEAD || { echo "Worktree has uncommitted changes; commit or stash first."; exit 1; }
  git -C "$MAIN_ROOT" diff --quiet HEAD || { echo "Main repo has uncommitted changes; commit or stash first."; exit 1; }
  git -C "$WORKTREE_PATH" rebase main
  cd "$MAIN_ROOT"
  git checkout main
  git merge --ff-only "$BRANCH"
  git push origin main
  git -C "$WORKTREE_PATH" reset --hard main
fi
```

On rebase conflict (`land` or manual): `main` is untouched; the worktree is mid-rebase. `land` prints the worktree path, the conflicted files, and the continue/abort commands. Resolve non-interactively (`status`, `diff`, edit, `add`, `rebase --continue`) and re-run `land "$BRANCH"`. To give up: `rebase --abort` (branch restored, `main` untouched).

## Step 3: Cleanup Workspace

Only after a successful land. Both paths below run from the main repo root — worktree removal must run from outside the worktree — and use the `GIT_DIR`/`GIT_COMMON`/`WORKTREE_PATH` values captured in Step 1, from before the directory change:

```bash
MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
cd "$MAIN_ROOT"
```

**If `GIT_DIR == GIT_COMMON`:** Normal repo, no worktree to clean up. Done.

**If `WORKTREE_PATH` is under `.worktrees/` or `worktrees/`:** Superpowers created this worktree — we own cleanup:

```bash
git worktree remove "$WORKTREE_PATH"
git worktree prune  # Self-healing: clean up any stale registrations
```

**If removal is refused** (`contains modified or untracked files`): the worktree holds files that exist nowhere else. Never `--force` on your own initiative. Stop and report what is at stake — do not ask, do not delete:

```bash
git -C "$WORKTREE_PATH" status --porcelain -uall
```

```
Worktree removal refused — these files were never committed:

<file list>

Land is complete; <branch> is merged. The worktree above still holds uncommitted files.
```

**Otherwise:** The host environment owns this workspace — leave it in place. If your platform provides a workspace-exit tool, use it.

Then delete the landed branch (fully merged, safe):

```bash
git branch -d <branch>
```

## Quick Reference

| Step | Action | Interaction |
|------|--------|-------------|
| 1. Detect | Branch vs detached HEAD, capture paths | none |
| 2. Land | `land` (or manual rebase + ff-merge + push) | none |
| 3. Cleanup | Remove owned worktree, prune, delete branch | none |

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Tests passed earlier this session" | Target-repo commit hooks gate every commit and implementer reports carry the evidence. No separate gate run here. (`land` runs `scripts/pre-land` under lock if the repo needs a final check.) |
| "I should ask what to do with completed work" | Always land. There is no menu. |
| "The base branch is obviously main" | It is always `main`. Do not ask. |
| "'Yeah, get rid of it' counts as cleanup authorization" | Only the land flow above removes anything, and only after a successful land. Discard happens solely on an explicit throw-it-away request. |
| "This other worktree looks stale — I'll clean it too" | Clean up only worktrees under `.worktrees/` or `worktrees/`. Everything else belongs to the host. |
| "Removal refused — `--force` is just finishing the cleanup" | The refusal means files exist only in that worktree. `--force` destroys them permanently. Stop and report. |
| "The rebase conflict will probably resolve itself on retry" | A conflicted rebase stays conflicted until resolved. Resolve and re-run, or `rebase --abort`. |
| "The push was rejected — force-push will fix it" | A rejected push means the remote moved. Investigate; force-push only on your human partner's explicit request. |
