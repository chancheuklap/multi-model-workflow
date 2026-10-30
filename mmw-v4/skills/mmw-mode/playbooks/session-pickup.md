### Session pickup

**You own the resume point when the prior position must be reconstructed. Read the trail and return to its current component.**

1. Locate the prior trail. An open ticket of ours, one whose `## Problem` has a `Playbook:` line, is a trail of its own:
   - Its newest outcome a `ticket.returned` event: finish the original executor's watch closeout first. When the owner selects the ticket, read the returned evidence and identify the concrete missing preparation. A skill-set change returns to Authoring or modifying a skill; ordinary code preparation goes to Develop a change (`playbooks/develop-a-change.md`) with that gap, existing baselines and kept commits. A missed hillclimb target reports the final number and Attempt comments before preparation resumes.
   - Its newest outcome a `ticket.bounced` event: run One ticket (`playbooks/one-ticket.md`) on it from step 1.
   - With `ready-for-agent` and a worker on it: One ticket is waiting for its wake.
   - Otherwise, reconstruct the unfinished result from the current records and select its existing component: carry on in the ticket's `fix-<n>`, from the first step its record does not show done, or from the selected preparation's opening step when the ticket has no effort branch.

   Taking up a ticket from `needs-triage` takes it out of the queue: `gh issue edit <n> --remove-label needs-triage`. This is the owner's selection to write a plan, not Go. Keep its kind. A historical Playbook title supplies context, not permission to load a retired file; keep the original Problem unchanged.

   For any other trail, find this host's transcripts of the prior session (where each host keeps them is listed at the head of `scripts/worktree-audit.sh`), for this repository only (do not search the transcripts of other projects, that reads private chats from unrelated work), or a pushed branch. Read the metadata overview and last messages first, then scan back for the decision points. Parse a long transcript in a subagent on the `reader` row and keep the reduced timeline in the main thread (the **principle-guard-the-context-window** skill). Its piece names the transcript and what it hands back: a timeline, one line per decision, with its time, the decision, and the line of the transcript that shows it.
2. Reconstruct operational state. The branch and worktree, what already landed (`git log`, `git diff` against the base), the decisions made. Where the work stands follows **principle-progress-is-what-the-record-says**.
3. Diff done vs pending. Compare what shipped against what was planned, name the resume point, do not re-run the prior repro or redo completed work. A "let me verify from scratch" pass means you're treating the trail as untrustworthy when it's authoritative.
4. Route the remaining work to the component that owns its requested result and pick the verdict: continue the execution, ship a finished recommendation, ratify or override a prior conclusion, or postmortem a failed run.
5. Verify against the original goal on the real artifact each inherited claim the record carries no proof for (**principle-prove-it-works**).

The pickup playbook ends here. The selected component owns the rest. Known current steps and active run wakes enter their existing re-entry directly without this reconstruction.

**Reply:** where the prior agent stopped, what you inherited vs redid (ideally nothing redone), the resume point, and the outcome.
