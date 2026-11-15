---
name: how
description: "Use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). Explains subsystem architecture, runtime flow, onboarding mental models. Use why for motivation."
---

# How

Explore the codebase to answer "how does X work?" questions. `how` starts a subagent, so the main chat or an owner session runs it, and a delegate that needs it replies `needs: how <the question>`.

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

## 1. Explain

Start one fresh subagent that explores and explains in one pass, on the `reader` role from the [mmwstack model rule](../setup-mmwstack/SKILL.md#model-rule). It is read-only. A host that runs roles through [agent definitions](../setup-mmwstack/references/agent-definitions.md#write-the-droids) gives the `reader` droid read-only tools. Give it the user's question and this brief:

> You are writing an architectural explanation for a senior engineer. Explore the codebase and write an explanation that a senior engineer unfamiliar with this area could read and walk away with a solid mental model. They should understand the architecture well enough to start working in it confidently. You have read-only access to the codebase.

## 2. Present

Present the subagent's output. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.
