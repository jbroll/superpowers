#!/usr/bin/env bash
#
# sync-upstream.sh — rebase this jbroll/superpowers fork onto the latest
# obra/superpowers upstream, keeping our customization commits on top.
#
# Our customization is always exactly `git log upstream/main..main`. This script
# fetches upstream, replays our commits onto it, and force-pushes (with lease).
# See the "Fork maintenance" section of README.md for the why.
#
set -euo pipefail

cd "$(dirname "$0")/.."   # repo root

UPSTREAM_URL="https://github.com/obra/superpowers.git"

# 1. Preconditions: on main, clean working tree.
branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" != "main" ]; then
  echo "error: on branch '$branch', not 'main' — run 'git checkout main' first" >&2
  exit 1
fi
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "error: working tree is dirty — commit or stash before syncing" >&2
  exit 1
fi

# 2. Ensure the upstream remote exists.
if ! git remote get-url upstream >/dev/null 2>&1; then
  echo "adding 'upstream' remote -> $UPSTREAM_URL"
  git remote add upstream "$UPSTREAM_URL"
fi

# 3. Show our customization before touching anything.
git fetch --quiet upstream
echo "=== our customization (upstream/main..main), before sync ==="
git log --oneline upstream/main..main || true
echo

# 4. Replay our commits onto the latest upstream.
echo "=== rebasing onto upstream/main ==="
if ! git rebase upstream/main; then
  {
    echo
    echo "CONFLICT: an upstream change collides with our edit (a skill likely moved)."
    echo "Resolve the conflict, then:"
    echo "    git rebase --continue      # or: git rebase --abort  to bail out"
    echo "Then re-run this script (or push manually with --force-with-lease)."
  } >&2
  exit 2
fi

# 5. Publish.
echo "=== pushing origin/main (force-with-lease) ==="
git push --force-with-lease origin main

echo
upstream_ver=$(git describe --tags upstream/main 2>/dev/null || git rev-parse --short upstream/main)
echo "done — now rebased onto upstream $upstream_ver."
echo "our customization still applied:"
git log --oneline upstream/main..main
echo
echo "Next: run '/plugin' in Claude Code and update superpowers@superpowers-dev."
