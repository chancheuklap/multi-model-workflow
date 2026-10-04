---
name: handoff
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
argument-hint: "What will the next session be used for?"
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to the temporary directory of the user's OS - not the current workspace.

Capture the intent, what you were doing, progress and what is verified, the current state, the next steps, the key files, and the gotchas.

Include a "suggested skills" section in the document, naming which skills the next agent should reach for.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.
