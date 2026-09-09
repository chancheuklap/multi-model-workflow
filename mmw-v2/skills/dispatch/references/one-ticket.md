# One ticket, outside a night

You are starting one worker on one ticket, with no batch behind it. A ticket outside a night belongs to no spec, so no `advance` will ever collect it: `land <n>` is its whole ending. Resolve `<dispatch>` in the `## Resolve `<dispatch>` once` section of [../SKILL.md](../SKILL.md).

Three steps:

1. `<dispatch> start <n> worker`, then the one `create_agent` path in [../SKILL.md](../SKILL.md).
2. End your turn. What wakes you is a message whose first line is `#<n> ALL MET` or `#<n> HANDOFF REQUIRED`, sent by `verify-ticket.py` at the moment the ticket comes to rest.
3. `<dispatch> land <n>`: it runs the product's `stop` in the ticket's worktree, merges its branch, archives its workspace (the agents inside it included), and gives its slot and its claim back.

## Exit codes

**`start <n> worker`:**

| Code | What happened |
| --- | --- |
| `0` | One JSON object is on stdout. A second live-table row for that agent is nested as `fallback` |
| `2` | Nothing was started. The reason is on stderr — read it verbatim. Typical causes: the ticket is not `OPEN` / not `ready-for-agent` / still blocked; two worker-grade labels; no live-table row for that agent; the Paseo daemon could not be asked to register this checkout as a project; an argument this form does not take |

**`land <n>`:**

| Code | What happened |
| --- | --- |
| `0` | Done. Stderr carries the merge line and the tally `land: merged <m>, archived <a>, released <r>, still working <w>, left unmerged <u>`. A ticket still being worked is named on stderr and nothing is done to it. A ticket whose product would not go down keeps its workspace and is named there too — archiving deletes the worktree the `stop` command lives in, so that one is left recoverable |
| `1` | The ticket closed but its branch is not in `HEAD`, so it was left standing; stderr names it. Archiving deletes the worktree, so this one waits for you: merge that branch, or decide the work is abandoned and archive it yourself |
| `2` | Nothing was touched: not a git repository, uncommitted tracked changes, or a ticket number that is not digits |
| `3` | A merge is in conflict and is still in the tree. Resolve it with the `resolving-merge-conflicts` skill, run this repository's checks, commit the merge, then run `land` again |
