---
name: runtime-forensics
description: Diagnose a runtime symptom (leak, idle-CPU spin, glitch) from live instrumentation. The deliverable is a diagnosis, not a fix.
---

# Runtime forensics

**You own the diagnosis. Instrument the live process, don't theorize from source.** The deliverable is a cited diagnosis, not a fix.

Redact every secret before showing a captured artifact: write `<REDACTED>` in its place.

## 1. Capture the live signal

Capture the live signal on the surface where the symptom shows: a CPU profile for a spinning process, a heap snapshot for a leak, a CDP trace for a visual glitch. A real artifact, not a guess. When the live signal cannot be captured, report the missing signal at handoff.

## 2. Reduce to the smoking gun

Reduce the artifact to the smoking gun: the function on the hot path, the retainer chain from the leaked object to a GC root, the loop firing without input. Use **principle-guard-the-context-window** and parse a large artifact in bounded pieces. Keep the reduced finding in the main thread.

## 3. Prove the mechanism

Prove the mechanism before believing it. Inject instrumentation via CDP eval on the running process, or hotfix the live code without reloading, to confirm the hypothesis cheaply.

## 4. Map it to source

Map the finding back to source: file, symbol, the line that allocates or schedules.

## 5. Hand off the diagnosis

The reply names the signal captured, the reduced finding, how you proved the mechanism, the source location, and the artifact paths.

State the repair the evidence supports or what evidence is still missing. For a diagnosis request, deliver that finding and stop here.

When the owner has requested a ticket or authorized a repair, use the **to-tickets** issue template and its worker-grade guidance to prepare one ticket. For a confirmed defect, name the mechanism, require the captured symptom to be gone and the commit message to state the mechanism. For a measured slowness, include the baseline; for sustained improvement, name the metric, direction and stop condition. Record a missing signal or unconfirmed cause as an evidence gap. Show the ticket and publish it within the authorized scope.

Dispatch the ticket through **dispatch** as Coordinator only when the owner authorized implementation and the evidence supports the repair.
