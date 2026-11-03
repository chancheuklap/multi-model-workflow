---
name: trace-forensics
description: Diagnose a captured profiling artifact (cpuprofile, trace, spindump, heap snapshot) handed to you after the fact. The deliverable is a diagnosis, not a fix.
---

# Trace forensics

**You own the diagnosis from the artifact.**

Distinct from **runtime-forensics**, which instruments the live process. Here the capture already exists. The artifact is a fixed dataset, read it, don't re-run it. Keep tooling generic: a DevTools or trace parser for cpuprofile and `.json.gz`, a text editor for a spindump, your heap tooling for a heapsnapshot.

Redact every secret before showing the artifact: write `<REDACTED>` in its place.

## 1. Load the artifact

Identify the format and load it with the right tool. Call the Skill tool with "principle-guard-the-context-window" and parse a large artifact in bounded pieces. Keep the reduced finding in the main thread.

## 2. Make it queryable

Transform the raw artifact into a form you can query. Dump the trace or heap snapshot into sqlite, one row per sample, frame, or node. Reach the queryable shape before you read.

## 3. Narrow to the cause

Query for the frames that hold the most time and walk the call tree to the hot path. For a leak, follow the retainer chain from the leaked object to a GC root. For a spindump, find the thread stuck on-CPU or blocked and its wait reason.

## 4. Attribute to source

Map the hot frame to file, symbol, and line via the artifact's own symbols. A frame with no source mapping is not yet a diagnosis. Resolve the symbols, or say plainly the artifact does not carry them.

## 5. Diff a paired capture

If you have a paired capture, diff the before and after artifacts to confirm. Otherwise, mark the finding as the strongest hypothesis the artifact supports, not a confirmed cause.

## 6. Hand off the diagnosis

The reply names the artifact and format, the reduced finding, the source location, the artifact paths, and whether a paired capture confirmed it.

Call the Skill tool with "to-tickets" for the issue template. Use only that template as the ticket format, not that skill's interactive Process. One ticket. Blocked by: None (can start immediately). Use the worker-grade selection in the `Draft vertical slices` section from that same call.

A defect becomes a fix ticket. What to build is the behaviour once that mechanism is gone. The finding is the fix, written there. Acceptance is that symptom gone, and the finding stated in the commit message. When the artifact does not carry the symbols, the ticket records that gap and names no fix.

A measured slowness becomes a perf-issue ticket. What to build is the improvement against the captured baseline. When that improvement is sustained improvement of one metric against a target, name the metric, the direction that counts as better, and the stop predicate.

Show the ticket to the user before publishing. Don't block on it; publish and proceed if the user is AFK.

When the ticket names a fix, call the Skill tool with "dispatch" and send this ticket as its Coordinator.

Done when the ticket is published. The Worker implements a ticket that names a fix.
