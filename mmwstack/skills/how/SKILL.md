---
name: how
description: "Explain subsystem architecture, runtime flow, and placement, ownership, or layering (\"how does X work\", \"where should this live\", pre-change walkthroughs). Use why for motivation."
---

# How

Explore the codebase to answer "how does X work?" questions.

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

## 1. Explain

For a tiny one- or two-file lookup, read the files directly and answer the question. Otherwise spawn one read-only subagent following [Subagents](../mmw-mode/SKILL.md#subagents) to explore and explain in one pass. Use the model and settings from the current host's `reader` entry in `~/.agents/mmwstack-models.md` (or the supplied rule file). Give it the user's question, their audience instructions, and this brief:

> Explore the codebase and write an architectural explanation that gives the reader a solid mental model of how this area works, including runtime flow, key types, and non-obvious behavior. Follow the user's audience instructions. You have read-only access to the codebase.

## 2. Present

Present the explanation. Light edits for clarity or context from the conversation are fine, and apply [unslop](../unslop/SKILL.md) to the final prose. Do not substantially rewrite it.
