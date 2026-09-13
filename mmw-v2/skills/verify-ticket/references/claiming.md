# Claiming a ticket

## Resolve `<engine>` once

`<engine>` is `scripts/verify-ticket.py`, resolved from this skill's own `SKILL.md` the way its **Resolve `<engine>` once** section says.

## Before you touch the ticket

```bash
<engine> <n> --preflight
```

It checks the branch, uncommitted tracked changes, the ticket's state, its `ready-for-agent` label, its blockers — one that is open, or closed with a pass that has not landed, still holds it — and its assignee, and claims the ticket for you when all six pass, posting a `ticket.claimed` event. After the claim and before it prints `READY:`, if the ticket does not yet carry a `ticket.checked` of run `baseline` for the newest `worker.started.base`, it checks that commit out in a throwaway detached worktree, runs every criterion whose `CHECK` does not name `journey.py`, `screen_driver.py`, `lease.py` or `story-parity.py`, posts that run (red is expected and does not refuse), and deletes the worktree. The ticket branch is left where it was. If it prints `NOT_READY`, stop — the reason is already on the ticket as a `ticket.refused` event whose first line is that sentence, so there is nothing to report twice. The event names your runner and session (as the `dispatch` skill's `self` reads them), which ends your hold on the ticket: you do nothing more on it, and the main agent is woken to fix the reason and start it again.

This is the only run that claims a ticket, and the claim is what the closeout reads at the end: a draft on a ticket you do not hold is refused with `#<n> is not assigned to you (<login>); run --preflight first`. So it comes before anything else on the ticket, including work you are being prompted back into after the claim was taken off.

## The uncommitted changes it refuses, and the ones it does not

That run comes every time you enter the ticket, so the uncommitted tracked changes it finds are sometimes somebody else's and sometimes your own. The claim on the ticket tells the two apart:

| The ticket's assignee when you run it | What uncommitted tracked changes are |
| --- | --- |
| not you | left in the worktree before your claim: `NOT_READY`, reason `dirty-tree`, and you stop |
| you | your own work from an earlier turn on this ticket: it claims the ticket again and prints `CARRIED: <count> tracked files …` |

On a `CARRIED:` line, commit those files on `issue-<n>` before the closing steps: `--closeout` refuses a draft while a tracked file is uncommitted. Nothing else about the run changes.

## Exit codes

`0` the ticket is now yours. `2` a refusal: the `ticket.refused` event, first line `NOT_READY: <reason>`, is on the ticket, and nothing else changed.
