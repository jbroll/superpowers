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
