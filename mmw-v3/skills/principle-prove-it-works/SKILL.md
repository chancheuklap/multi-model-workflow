---
name: principle-prove-it-works
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Prove It Works

Verify every task output by checking the real thing directly. Do not infer from proxies, self-reports, or "it compiles."

**Why:** Unverified work has unknown correctness. Indirect verification (file mtimes, output freshness, agent self-reports, cached screenshots) feels cheaper than direct observation. Acting on a wrong inference costs far more than checking the source.

Check the real thing, not a proxy:
- Check process liveness directly, not indirectly through derived state
- Read the actual value, not a cached or derived representation
- When verification fails, suspect the observation method before suspecting the system
- "It compiles" and "it deploys" are not "it works". The proof is the opened page, the flow that ran end to end, or the first failing line.
- A caveat about your own work ("not yet run against the real API") is an unmet criterion, not a footnote. Half done is not done, and "the rest is minor" is not done.

## Script the check when you can

The strongest proof is a deterministic script that re-runs the same comparison, not a one-time eyeball. Write the script, run it, and keep its output as an artifact a reviewer can re-run instead of trusting your word.

Keep the artifact visible for the human. Commit it only for large or complex work where the trail has to be auditable later, like a big port or migration.
