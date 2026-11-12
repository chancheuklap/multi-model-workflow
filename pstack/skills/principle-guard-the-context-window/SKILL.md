---
name: principle-guard-the-context-window
description: "Apply when large outputs, screenshots, long files, or fan-out planning threaten the context window. Read a focused excerpt or delegate the bulk reading. Keep findings in the main thread."
disable-model-invocation: true
---

# Guard the Context Window

**Why:** Context overflow degrades reasoning quality, creates compression artifacts, and halts progress.

**Pattern:**
- **Isolate large payloads.** Read a short excerpt when it answers the question. Give bulk reading to a subagent under the active playbook or skill. Return the finding and its source to the main thread.
- **Size phases and cap scope.** Limit files per phase, set turn budgets, account for mechanism costs.
