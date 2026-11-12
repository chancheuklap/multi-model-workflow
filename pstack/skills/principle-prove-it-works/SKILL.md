---
name: principle-prove-it-works
description: "Apply before acting on a finding or declaring work done. Check the real artifact at its current version, including the path or state the claim depends on. A proxy or a self-report can't settle it."
disable-model-invocation: true
---

# Prove It Works

Verify every task output by checking the real thing directly. Do not infer from proxies, self-reports, or "it compiles."

**Why:** Unverified work has unknown correctness. Indirect verification (file mtimes, output freshness, agent self-reports, cached screenshots) feels cheaper than direct observation. Acting on a wrong inference costs far more than checking the source.

Check the real thing, not a proxy:
- Check process liveness directly, not indirectly through derived state
- Read the actual value, not a cached or derived representation
- When verification fails, suspect the observation method before suspecting the system
- Before acting on a finding, check its exact claim against the current version of the real artifact, including the reachable path or state it depends on. A plausible fix or a true fact about nearby code neither proves nor disproves that claim. Keep an unsettled claim unverified.

## Script the check when you can

The strongest proof is a deterministic script that re-runs the same comparison, not a one-time eyeball. Write the script, run it, and keep its output as an artifact a reviewer can re-run instead of trusting your word.

Keep the artifact visible for the human. Commit it only for large or complex work where the trail has to be auditable later, like a big port or migration (the **show-me-your-work** skill).
