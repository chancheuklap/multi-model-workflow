# Paseo board prototype

## Question

Can a Paseo plugin show one spec's night — what closed, what was opened and by which ticket, what was handed back, where every ticket stands and which live agent is on it — reading only the issue tracker and Paseo's own agent state, without any process that acts?

## Current conclusion

Yes. `mmw-board/` is a working Paseo v0.7 plugin: a sidebar surface, a daemon-side RPC that reads the spec's sub-issues through `gh` and classifies them by the pipeline's fixed first lines, and a client that reads live agents from Paseo's cached state. Run against spec #111 (3 tickets) and #76 (11 tickets) on 2026-09-05: closed / opened / origin attribution correct on both; 8 seconds to read 11 tickets.

What it settled for the spec:

- The tracker is enough: phase, criteria count, abandon lines, decisions, sub-issues opened, files touched — all come off comment first lines and fixed lines already on tickets. No agent label is needed for the ticket side.
- "Opened tonight" must exclude the batch's own tickets; the closeout strips `ready-for-agent`, so a batch ticket is recognised by its `<issue-template>` sections, not by labels.
- Origin of a sub-issue: the `Sub-issues opened:` line of the originating ticket's closing comment is reliable; body mentions are not (a `## Blocked by` reference looks like an origin).
- Paseo's plugin client state carries agent labels that the CLI does not print, so the board can match agents to tickets by `mmw.ticket` once the pipeline sets it, and falls back to the worktree directory name and the agent title meanwhile.
- One `gh issue view` per ticket is the cost; a GraphQL batch would be the fix if a 30-ticket spec gets slow.

Rough in every visual respect. Not folded into real code yet.

## Which parts the real code has taken

None. The spec for the board (see the tracker) cuts its tickets from this leaf.

## Running it

```
cd mmw-board && npm install && npm run typecheck
paseo plugin install "$PWD"
```

`pluginsEnabled` must be on in `~/.paseo/config.json`. The sidebar item is `mmw board`.
