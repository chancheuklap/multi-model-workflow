---
name: trace-forensics
description: Diagnose a captured profiling artifact (cpuprofile, trace, spindump, heap snapshot) handed to you after the fact. The deliverable is a diagnosis, not a fix.
---

# Trace forensics

**You own the diagnosis from the artifact.**

Distinct from **runtime-forensics**, which instruments the live process. Here the capture already exists. The artifact is a fixed dataset, read it, don't re-run it. Keep tooling generic: a DevTools or trace parser for cpuprofile and `.json.gz`, a text editor for a spindump, your heap tooling for a heapsnapshot.

Redact every secret before showing the artifact: write `<REDACTED>` in its place.

## 1. Load the artifact

Identify the format and load it with the right tool. Use **principle-guard-the-context-window** and parse a large artifact in bounded pieces. Keep the reduced finding in the main thread.

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

State the repair the evidence supports or what evidence is still missing. For a diagnosis request, deliver that finding and stop here.

When the owner has requested a ticket or authorized a repair, use the **to-tickets** issue template and its worker-grade guidance to prepare one ticket. For a confirmed defect, name the mechanism, require the captured symptom to be gone and the commit message to state the mechanism. For a measured slowness, include the baseline; for sustained improvement, name the metric, direction and stop condition. Record a missing signal or unconfirmed cause as an evidence gap. Show the ticket and publish it within the authorized scope.

Dispatch the ticket through **dispatch** as Coordinator only when the owner authorized implementation and the evidence supports the repair.
