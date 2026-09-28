# Linting a batch

`<engine>` is resolved in this skill's `SKILL.md`.

You are about to publish a batch of tickets, have just published one, or are opening a night on a spec before its first `advance`.

```bash
<engine> <spec> --lint --drafts <dir>   # the batch's drafts, before any is published
<engine> <n> --lint                     # one ticket, and the graph of the batch it sits under
<engine> <spec> --lint                  # every sub-issue of the spec, then the graph once
```

The graph it checks is the tracker's blocking links, the same ones `--preflight` refuses on and `advance` dispatches from, so an edge is fixed there, not in a ticket body. The batch is ready when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose.
