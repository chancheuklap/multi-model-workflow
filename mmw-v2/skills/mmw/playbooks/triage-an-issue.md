### Triage an issue

**The maintainer owns each outcome.**

1. **Triage.** Run the `triage` skill's `## Triage a specific issue or PR` on the issue until the maintainer has agreed to one of its four outcomes. A `ready-for-human` outcome is written here rather than routed. Write what `to-tickets` writes for this label, not an agent brief: **the five things** in the `to-tickets` skill's `references/person-ticket.md`, nothing more.
   Done when the maintainer has agreed to one of the four outcomes, and the `triage` skill has applied every outcome other than `ready-for-agent` to the issue.
2. **Route ready-for-agent work.** When the issue is work from outside, post an agent brief comment on it (the `triage` skill's `AGENT-BRIEF.md`), then route it into the ticket pipeline at **Split into several specs when it is several** in **Write a spec and tickets**. An issue judged `ready-for-agent` goes into the ticket pipeline, where the `to-spec` skill reads the agent brief as one of the spec's sources and the `to-tickets` skill cuts the tickets an agent works from. The label goes on those tickets, not on this issue. A ticket the pipeline handed back is not judged here: it goes to the `dispatch` skill's `references/night.md`.
   Done when the issue carries its agent brief comment and **Write a spec and tickets** has started from it at **Split into several specs when it is several**.

Work this repo plans for itself carries no category role: a spec's tickets carry a state role; a map, a spec and a decision ticket carry none and are not triaged.

**Reply:** each issue's outcome and the reason for it.
