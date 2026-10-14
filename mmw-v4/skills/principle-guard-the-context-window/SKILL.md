---
name: principle-guard-the-context-window
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Guard the Context Window

The context window is finite and non-renewable within a session. Every token should be worth its cost.

**Why:** Context overflow degrades reasoning quality, creates compression artifacts, and halts progress.

**Pattern:**
- **Isolate large payloads.** Read verbose outputs, screenshots, and large documents in chunks, or give them to the subagent the current step sends for them. The main context gets summaries, not raw data.
- **Keep frequently used content inline.** Templates and references used on every invocation belong in the skill file, not in separate files that cost a read each time.
- **Size phases and cap scope.** Limit files per phase, set turn budgets, account for mechanism costs.
