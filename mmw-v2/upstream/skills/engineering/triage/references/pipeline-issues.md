# Issues from this repository's own pipeline

## A ticket handed back

A `needs-triage` ticket whose newest result is `ticket.returned` or `ticket.bounced` did not arrive from outside. `ticket.returned` means the worker could not finish it. `ticket.bounced` means a passed ticket could not merge onto the fetched `origin/<base branch>` commit because the merge conflicted or the repository checks failed.

Read the ticket's event trail instead of reproducing from a reporter's steps, and skip `.out-of-scope/`: nobody rejected this request. For `ticket.returned`, read its `ticket.checked` runs and `reviewer.reported`. For `ticket.bounced`, read the `origin/<base branch>` commit the merge tried to build on (`commit`), the base branch in `into`, the sibling tickets that landed after this ticket started, and the `files` or `commands` attached to the event. Then recommend one of the four outcomes, `needs-info`, `ready-for-agent`, `ready-for-human`, or `wontfix`, from what the pipeline already established.

## Gather context

The issue being triaged is written `<m>`. First read the parent issue (the `parent:` line of `gh issue view <m>`, or `gh api repos/{owner}/{repo}/issues/<m> --jq .parent_issue_url`; the REST object has no `parent` field). When the parent is a ticket, read that ticket's event trail (its `ticket.checked` runs and its `reviewer.reported`) instead of reproducing.

## ready-for-agent

Judging an issue agent-ready also answers where the work is done. When the parent is a ticket, pick one destination:

| Judgement | Command |
| --- | --- |
| Work that belongs to another ticket in this batch | `gh issue edit <m> --parent <ticket>` |
| New work in this batch, belonging to no existing ticket | the `dispatch` skill's `route <ticket> <m> became-ticket <m>` (`<ticket>` is the ticket whose `child.opened` names `<m>`), which moves `<m>` under the spec, swaps its layer label `mmw:child` for `mmw:ticket`, and records the route on the ticket it came from; fill every section of `<issue-template>` (in `to-tickets`); the `verify-ticket` skill's `--lint <m>` passes; from then it is a ticket |
| A toolbox problem found in a consuming repository | `gh issue transfer <m> chancheuklap/multi-model-workflow`; the parent–child link breaks on transfer; origin remains the body's first line |

When the issue is itself a ticket the pipeline handed back (`## A ticket handed back` above), swap its `needs-triage` for `ready-for-agent`. The next `advance` on its spec (the `dispatch` skill) gives back the pipeline's claim on it and starts a worker on it once its blockers have landed.
