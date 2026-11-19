---
name: how
description: "Use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). Explains subsystem architecture, runtime flow, onboarding mental models. Use why for motivation."
---

# How

Explore the codebase to answer "how does X work?" questions.

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

## 1. Explain

Start one fresh subagent that explores and explains in one pass, on the `reader` role from the [mmwstack model rule](../setup-mmwstack/SKILL.md#model-rule). It is read-only. Give it the user's question and the relevant audience instructions. Ask it to answer that reader directly from the code.

## 2. Present

Present the subagent's output. Use [unslop](../unslop/SKILL.md) for light edits to clarity or context. Do not substantially rewrite it.
