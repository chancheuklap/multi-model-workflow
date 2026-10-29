### Session pickup

**You own the resume point. Read the prior trail, don't redo it.**

1. Locate the prior trail. An open ticket of ours, one whose `## Problem` has a `Playbook:` line, is a trail of its own:
   - Its newest outcome a `ticket.returned` event: run the playbook its `Playbook:` line names from the step its **A ticket that came back** names, in the ticket's `fix-<n>`.
   - Its newest outcome a `ticket.bounced` event: run One ticket (`playbooks/one-ticket.md`) on it from step 1.
   - With `ready-for-agent` and a worker on it: One ticket is waiting for its wake.
   - Otherwise, that playbook is part way through: carry on in the ticket's `fix-<n>`, from the first step its record does not show done, or from that playbook's first step when the ticket has no `fix-<n>`.

   Taking up a ticket from `needs-triage` takes it out of the queue: `gh issue edit <n> --remove-label needs-triage`. This is the owner's selection to write a plan, not Go. Keep its kind and follow its `Playbook:` line.

   For any other trail, find this host's transcripts of the prior session (where each host keeps them is listed at the head of `scripts/worktree-audit.sh`), for this repository only (do not search the transcripts of other projects, that reads private chats from unrelated work), or a pushed branch. Read the metadata overview and last messages first, then scan back for the decision points. Parse a long transcript in a subagent on the `reader` row and keep the reduced timeline in the main thread (the **principle-guard-the-context-window** skill). Its piece names the transcript and what it hands back: a timeline, one line per decision, with its time, the decision, and the line of the transcript that shows it.
2. Reconstruct operational state. The branch and worktree, what already landed (`git log`, `git diff` against the base), the decisions made. Where the work stands follows **principle-progress-is-what-the-record-says**.
3. Diff done vs pending. Compare what shipped against what was planned, name the resume point, do not re-run the prior repro or redo completed work. A "let me verify from scratch" pass means you're treating the trail as untrustworthy when it's authoritative.
4. Route the remaining work to the matching playbook and pick the verdict: continue the execution, ship a finished recommendation, ratify or override a prior conclusion, or postmortem a failed run.
5. Verify against the original goal on the real artifact each inherited claim the record carries no proof for (**principle-prove-it-works**).

The pickup playbook ends here. The routed playbook owns the rest.

**Reply:** where the prior agent stopped, what you inherited vs redid (ideally nothing redone), the resume point, and the outcome.
