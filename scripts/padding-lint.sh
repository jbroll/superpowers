#!/usr/bin/env bash
# padding-lint.sh — flag prose padding the cut rules are meant to remove.
# Deterministic, zero-dependency. Runs on any spec/plan markdown.
# Usage: scripts/padding-lint.sh FILE [FILE...]
# Reports per file: word count, flag count, and each flagged line.
# Exit 1 if any file has flags (so it doubles as a gate/test).
set -euo pipefail

# Delete-on-sight patterns (extended regex, case-insensitive). Each is prose
# padding per the cut rules ported from ai-roller's specification skill.
PATTERNS='(^|[^a-z])(note that|it is important to|it is worth noting|this (section|document|plan) (describes|covers|explains)|in order to|allows for|enables|facilitates|as (a|the) matter of fact)([^a-z]|$)|\b(generally|typically|usually|often)\b'

total_flags=0
for f in "$@"; do
  [[ -f "$f" ]] || { echo "skip (not a file): $f" >&2; continue; }
  words=$(wc -w < "$f" | tr -d ' ')
  hits=$(grep -nEi "$PATTERNS" "$f" || true)
  count=$(printf '%s' "$hits" | grep -c . || true)
  total_flags=$((total_flags + count))
  printf '%s: %s words, %s padding flag(s)\n' "$f" "$words" "$count"
  [[ -n "$hits" ]] && printf '%s\n' "$hits" | sed 's/^/    /'
done

echo "---"
echo "total padding flags: $total_flags"
[[ "$total_flags" -eq 0 ]]
