# A ticket you picked up yourself

You picked ticket `<n>` up yourself; no `start` is behind you. Resolve `<dispatch>` in the `## Resolve `<dispatch>` once` section of [../SKILL.md](../SKILL.md).

Run `<dispatch> adopt <n>` first: it records you as the ticket's worker and makes sure a relay watches the ticket. Without it no event names your session, so your reviewer's report would wake nobody, and `start <n> reviewer` would refuse.

## Exit codes

**`adopt <n> [--into <branch>]`**: run it from the ticket's worktree on branch `issue-<n>`, before claiming; outside a night add `--into <base branch>`. Exit 2 adopted nothing; its stderr names what to fix.

## After the closeout

A ticket you adopted outside a night, where `adopt` started a relay with you as the session it wakes, has no main agent to land it: you are woken with `#<n> ticket.passed` or `#<n> ticket.returned`; `<dispatch> ack <n> <that event>`, then tell the user the ticket is closed and that `<dispatch> land <n>` merges it and stops that relay. Do not run `land` from this worker session: it stops every session the ticket's events name, including this one.
