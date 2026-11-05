---
name: runtime-forensics
description: Diagnose a runtime symptom (leak, idle-CPU spin, glitch) from live instrumentation. The deliverable is a diagnosis, not a fix.
---

# Runtime forensics

**You own the diagnosis. Instrument the live process, don't theorize from source.** The deliverable is a cited diagnosis, not a fix.

Redact every secret before showing a captured artifact: write `<REDACTED>` in its place.

## 1. Capture the live signal

Capture the live signal on the surface where the symptom shows: a CPU profile for a spinning process, a heap snapshot for a leak, a CDP trace for a visual glitch. A real artifact, not a guess. When the live signal cannot be captured, skip to the handoff and publish a ticket that records the missing signal and names no fix.

## 2. Reduce to the smoking gun

Reduce the artifact to the smoking gun: the function on the hot path, the retainer chain from the leaked object to a GC root, the loop firing without input. Use **principle-guard-the-context-window** and parse a large artifact in bounded pieces. Keep the reduced finding in the main thread.

## 3. Prove the mechanism

Prove the mechanism before believing it. Inject instrumentation via CDP eval on the running process, or hotfix the live code without reloading, to confirm the hypothesis cheaply.

## 4. Map it to source

Map the finding back to source: file, symbol, the line that allocates or schedules.

## 5. Hand off the diagnosis

The reply names the signal captured, the reduced finding, how you proved the mechanism, the source location, and the artifact paths.

Use **to-tickets** for the issue template. Use only that template as the ticket format, not that skill's interactive Process. One ticket. Blocked by: None (can start immediately). Use the worker-grade selection in the `Draft vertical slices` section from that same call.

When the live signal is missing, What to build records that gap and names no fix.

A defect becomes a fix ticket. What to build is the behaviour once that mechanism is gone. The proved mechanism is the fix, written there. Acceptance is the captured symptom gone, and the confirmed mechanism stated in the commit message.

A measured slowness becomes a perf-issue ticket. What to build is the improvement against the baseline this diagnosis captured. When that improvement is sustained improvement of one metric against a target, name the metric, the direction that counts as better, and the stop predicate.

Show the ticket to the user before publishing. Don't block on it; publish and proceed if the user is AFK.

When the ticket names a fix, use **dispatch** and send this ticket as its Coordinator.

Done when the ticket is published. The Worker implements a ticket that names a fix.
