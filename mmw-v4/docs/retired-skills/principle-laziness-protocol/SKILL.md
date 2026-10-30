---
name: principle-laziness-protocol
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Laziness Protocol

Aim for the most result with the least code and complexity.

- **Prefer deletion.** When asked to refactor or improve, look for removals before additions.
- **Consolidate decisions.** Do not repeat the same choice in several places. Put it behind one source of truth and pass the result as a simple flag.
- **Minimize the diff.** Make the smallest change that solves the problem. Fewer lines beat "elegant" boilerplate.

**Keep intact.** Whatever you simplify, keep security, error handling that prevents data loss, accessibility, and anything the task explicitly asks for.

**In a diff:**

- Of every hunk, ask whether the acceptance criteria still pass with less: the hunk deleted, folded into a branch that already exists, or replaced by a helper the repository already has. Raise it only when you can write the shorter form; one you cannot write is a preference.
- Look for the reframing that keeps the behavior and makes a block of branches, helpers, modes or layers disappear, rather than rearranging it. One that reaches beyond the ticket's files is a finding outside the ticket, never a demand on this diff.
- A simplification that removes a security check, error handling that prevents data loss, accessibility, or something the request asked for: put it back (**Keep intact**).
