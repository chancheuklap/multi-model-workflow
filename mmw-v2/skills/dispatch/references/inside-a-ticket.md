# A ticket you picked up yourself

You picked ticket `<n>` up yourself; no `start` is behind you. Resolve `<dispatch>` in the `## Resolve `<dispatch>` once` section of [../SKILL.md](../SKILL.md).

Run `<dispatch> adopt <n>` first: it records you as the ticket's worker and makes sure a relay watches the ticket. Without it no event names your session, so your reviewer's report would wake nobody, and `start <n> reviewer` would refuse.

## Exit codes

**`adopt <n> [--into <branch>]`**, for a session that picked ticket `<n>` up itself rather than being started on it: run from the ticket's worktree on branch `issue-<n>`, before claiming. `into` comes from the latest `worker.started`, else the open night's `spec.opened`, else the required `--into` outside a night; it must exist on origin. `0` this session is the ticket's worker and `worker.started` records its runner, session, grade row, worktree, ticket branch, base branch and base commit; a relay watches the ticket, stdout is the session id, and no product slot is taken. Adopting again from the same session writes nothing more. `2` nothing was adopted; stderr names a session it cannot identify, the ticket state, wrong ticket branch, missing `origin/<base branch>`, `worker.started` without `into`, an existing worker, relay failure or tracker failure.

## After the closeout

A ticket you adopted outside a night, where `adopt` started a relay with you as the session it wakes, has no main agent to land it: you are woken with `#<n> ticket.passed` or `#<n> ticket.returned`; `<dispatch> ack <n> <that event>`, then tell the user the ticket is closed and that `<dispatch> land <n>` merges it and stops that relay. Do not run `land` from this worker session: it stops every session the ticket's events name, including this one.
