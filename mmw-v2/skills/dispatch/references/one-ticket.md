# One ticket, outside a night

You are starting one worker on one ticket, with no batch behind it. A ticket outside a night belongs to no spec, so no `advance` will ever collect it: `land <n>` is its whole ending. Resolve `<dispatch>` in the `## Resolve `<dispatch>` once` section of [../SKILL.md](../SKILL.md).

Three steps:

1. `<dispatch> start <n> worker`.
2. `<dispatch> wait <n> worker` until it answers `ALL MET` or `HANDOFF REQUIRED` (exit codes in [inside-a-ticket.md](inside-a-ticket.md)); a ticket message with the same first line may arrive first when both sessions are on Paseo.
3. `<dispatch> land <n>`: it runs the product's `stop` in the ticket's worktree, merges its branch, stops every session the ticket's `RUNNER` lines name, removes its worktree, and gives its slot and its claim back.

## Exit codes

**`start <n> worker`:**

| Code | What happened |
| --- | --- |
| `0` | The session is running; its id is on stdout and a `RUNNER` line is on the ticket |
| `2` | Nothing was started. The reason is on stderr — read it verbatim. Typical causes: the ticket is not `OPEN` / not `ready-for-agent` / still blocked; two worker-grade labels; no live-table row for that agent; the runner refused the start (its reason is on stderr, and it was not retried); an argument this form does not take |

**`land <n>`:**

| Code | What happened |
| --- | --- |
| `0` | Done. Stderr carries the merge line and the tally `land: merged <m>, archived <a>, released <r>, still working <w>, left unmerged <u>`. A ticket still being worked is named on stderr and nothing is done to it. A ticket whose product would not go down keeps its workspace and is named there too — archiving deletes the worktree the `stop` command lives in, so that one is left recoverable |
| `1` | The ticket closed but its branch is not in `HEAD`, so it was left standing; stderr names it. Archiving deletes the worktree, so this one waits for you: merge that branch, or decide the work is abandoned and archive it yourself |
| `2` | Nothing was touched: not a git repository, uncommitted tracked changes, or a ticket number that is not digits |
| `3` | A merge is in conflict and is still in the tree. Resolve it with the `resolving-merge-conflicts` skill, run this repository's checks, commit the merge, then run `land` again |
