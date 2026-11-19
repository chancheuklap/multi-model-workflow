---
name: principle-guard-the-context-window
description: Use when large files, tool output, screenshots, or extended work threaten context capacity. Read large payloads in bounded pieces and keep only relevant material in the active context.
---

# Guard the Context Window

**Why:** Context overflow degrades reasoning quality, creates compression artifacts, and halts progress.

**Pattern:**
- **Isolate large payloads.** Read verbose outputs, screenshots, and large documents in chunks, or give them to the subagent the current step sends for them. The main context gets summaries, not raw data.
- **Keep frequently used content inline.** Templates and references used on every invocation belong in the skill file, not in separate files that cost a read each time.
- **Size phases and cap scope.** Limit files per phase, set turn budgets, account for mechanism costs.
