---
name: principle-no-secrets-or-personal-data-in-artifacts
description: "Apply when writing a ticket, a Memory record, a handoff, a log or a spec. Keep credentials and personal data out of every artifact, and redact them from anything you quote."
---

# No secrets or personal data in artifacts

Credentials and personal data go into no artifact: no ticket, Memory record, handoff, log or spec.

**Pattern:**
- **Redact before you write.** Redact any sensitive information, such as API keys, passwords, or personally identifiable information.
- **Quote only what carries the signal.** Captured artifacts carry auth headers: quote only the lines that carry the signal.
