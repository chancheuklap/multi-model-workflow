# Claiming a ticket

## Resolve `<engine>` once

`<engine>` is `scripts/verify-ticket.py`, resolved from this skill's own `SKILL.md` the way its **Resolve `<engine>` once** section says.

## Before you touch the ticket

```bash
<engine> <n> --preflight
```

It checks the branch, uncommitted tracked changes, the ticket's state, its `ready-for-agent` label, its open blockers, and its assignee, and claims the ticket for you when all six pass. If it prints `NOT_READY`, stop — the reason is already a comment on the ticket, so there is nothing to report twice.

This is the only run that claims a ticket, and the claim is what the closeout reads at the end: a draft on a ticket you do not hold is refused with `#<n> is not assigned to you (<login>); run --preflight first`. So it comes before anything else on the ticket, including work you are being prompted back into after the claim was taken off.

## Exit codes

`0` the ticket is now yours. `2` a refusal: the `NOT_READY: <reason>` comment is on the ticket, and nothing else changed.
