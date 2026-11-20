---
name: principle-prove-it-works
description: "Apply before acting on a finding or declaring work done. Check the real artifact at its current version, including the path or state the claim depends on. A proxy or a self-report can't settle it."
---

# Prove It Works

Verify every output by checking the real thing directly: run the feature, read the actual value, inspect the diff. Before acting on a finding, check its exact claim against the current version of the real artifact, including the reachable path or state it depends on. Keep an unsettled claim unverified. Proxies (file mtimes, self-reports, cached output, "it compiles") do not count. When a check fails, suspect the observation method before the system.

Script the check when you can. A deterministic script that reruns the comparison beats a one-time look. Keep its output where the operator can see it, and commit it only when the trail must be auditable later.
