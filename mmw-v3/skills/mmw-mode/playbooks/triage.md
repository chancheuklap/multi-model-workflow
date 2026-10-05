### Triage

**You own one pass over the triage queue with the owner: each issue they pick judged with the `triage` skill and moved to one of its four outcomes, and each issue judged `ready-for-agent` carried into a spec and its batch.** The owner decides each outcome; you bring the evidence and a recommendation, and do the moving once they decide. Most of this repository's queue was put there by the pipeline, not by a reporter, and it is read in the morning by someone who has forgotten the night, so each line you show stands on its own. Distinct from Bug fix, which starts from a defect the owner reports in this conversation, and from Run a night, whose orchestrator routes a night's children itself while the night runs.

1. **Show the queue.** Follow the `triage` skill's `## Show what needs attention`. When the owner named the issues, take those instead.
   Done when the owner has picked or named the issues to judge.
2. **Judge each picked issue.** Follow the `triage` skill's `## Triage a specific issue` for each, one at a time, through its outcome; an issue the pipeline opened is read as that skill's `references/pipeline-issues.md` says.
   Done when each picked issue carries one of the four outcomes, or the owner has put it down.
3. **Carry agent-ready work into a spec.** Take each issue from outside judged `ready-for-agent`, and each retro proposal the owner approved. Issues that share a seam go into one spec. When the work extends a published spec, run **Revise a spec** on it, citing the issue as a source, then **Cut tickets** for the new work; otherwise run **Write a spec** with the issue as its reference, which cuts the tickets at its end. Then close the issue with a comment linking that spec.
   Done when each such issue is closed with a comment linking the spec its tickets were cut from.

**Reply:** one line per issue judged: its outcome and the reason; the specs written or revised and their batches; and what is left in the queue.
