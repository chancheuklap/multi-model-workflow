# Issues from this repository's own pipeline

Almost everything in this repository's `needs-triage` queue was put there by the pipeline, not by a reporter: a worker, a review, a merge or a re-run stopped because the next step needs a judgement no script can make. The user reads this queue first thing in the morning. For each item, find what the pipeline already established, turn it into one question the user can answer in a sentence, give your recommendation with its evidence, and once the user decides, put the work back where the pipeline picks it up. The evidence is already on the tracker; read a ticket's events with `events.py fold <n>` rather than reproducing. An item left in `needs-triage` is read again tomorrow by someone with less context than you have now.

**A child a worker opened** (its body opens ``A `<kind>` child of #<n>.``): `decision`, the worker already took the default it names, so confirm or overturn it; `contract`, which authority wins, and the not-yet-started tickets the night moved to `needs-triage` wait on the same answer; `deferred`, whether a convenient change outside `## Owns` is worth a ticket; `fault`, what in the pipeline broke, here or in the toolbox; `finding`, one the night's closing pass did not reach. **A ticket handed back, bounced twice, or reopened by `reverify`**: `## A ticket handed back` below. **A ticket a night parked with no result**: it waits on an open `contract` child of its batch that names it; settle that child, then move every ticket it parked back to `ready-for-agent` together. **A retro proposal**: the retro already gathered the evidence; the user approves it or not, and approved work goes through the `to-spec` and `to-tickets` skills.

## A ticket handed back

A `needs-triage` ticket whose newest result is `ticket.returned` or `ticket.bounced` did not arrive from outside. `ticket.returned` means the worker could not finish it. `ticket.bounced` means a passed ticket could not merge onto the fetched `origin/<base branch>` commit because the merge conflicted or the repository checks failed.

Read the ticket's event trail instead of reproducing from a reporter's steps, and skip `.out-of-scope/`: nobody rejected this request. For `ticket.returned`, read its `ticket.checked` runs and `reviewer.reported`. For `ticket.bounced`, read the `origin/<base branch>` commit the merge tried to build on (`commit`), the base branch in `into`, the sibling tickets that landed after this ticket started, and the `files` or `commands` attached to the event. Then recommend one of the four outcomes, `needs-info`, `ready-for-agent`, `ready-for-human`, or `wontfix`, from what the pipeline already established.

`ticket.regressed` means a landed ticket's criteria went red on the base branch. Read the commit it names, which criteria failed, and the sibling tickets that landed since: often a later ticket broke it, and the fix belongs there. While it still wears `needs-triage`, every `reverify` re-runs it and closes it again once it is green, so a regression something else already fixed needs no outcome from you.

For `ticket.returned`, the closing comment's `ABANDON:` lines say why, and the kind points at the outcome. `stuck` on a credential, a device or a real environment is usually `ready-for-human` of kind `reach`. `failed` after rounds that each tried something raises one question: would a changed criterion, a split ticket or a `senior-worker` grade pass? Sending it back unchanged repeats the night. The worker's partial work stands in `.worktrees/issue-<n>`.

## ready-for-agent

Only `ready-for-agent` moves a child; `needs-info`, `ready-for-human` and `wontfix` leave it under its ticket. Judging an issue agent-ready also answers where the work is done. Pick one destination:

| Judgement | Command |
| --- | --- |
| Work that belongs to another ticket in this batch | `gh issue edit <m> --parent <ticket>` |
| New work in this batch, belonging to no existing ticket | `dispatch.sh resolve-child <ticket> <m> became-ticket <m>` (`<ticket>` is the ticket whose `child.opened` names `<m>`). It leaves the queue labels alone: rewrite the body to `<issue-template>` (in `to-tickets`), swap `needs-triage` for `ready-for-agent`, add `junior-worker` or `senior-worker`, and lint it. `--lint` passes a ticket outside the agent queue, so it will not catch a missing label. |
| A toolbox problem found in a consuming repository | `gh issue transfer <m> chancheuklap/multi-model-workflow`; the parent-child link breaks on transfer; origin remains the body's first line |

Only a ticket not yet started reads it: a worker reads its ticket's open children once, when it starts.

When the issue is itself a ticket the pipeline handed back (`## A ticket handed back` above), swap its `needs-triage` for `ready-for-agent`. The next `advance` on its spec (**Run a night**) gives back the pipeline's claim on it and starts a worker on it once its blockers have landed. With no night open on its spec, **Land one ticket** starts it instead.
