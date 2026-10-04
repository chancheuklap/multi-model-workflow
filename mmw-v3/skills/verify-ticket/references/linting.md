# Linting a batch

You are about to publish a batch of tickets, have just published one, or are opening a night on a spec before its first `advance`.

```bash
python3 scripts/verify-ticket.py <spec> --lint --drafts <dir>   # the batch's drafts, before any is published
python3 scripts/verify-ticket.py <n> --lint                     # one ticket, and the graph of the batch it sits under
python3 scripts/verify-ticket.py <spec> --lint                  # every sub-issue of the spec, then the graph once
```

The graph it checks is the tracker's blocking edges, the same ones `--preflight` refuses on and `advance` dispatches from, so an edge is fixed there, not in a ticket body. The batch is ready when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose.

Exit 0: no `ERROR`. Exit 1: fix each `ERROR` on its ticket, except one saying the tracker could not answer (tagged `[parent-unreadable]` or `[sub-issues-unreadable]`, or a traceback from a `gh` call): nothing about the tickets was established, so run the same command again once the tracker answers. Exit 2: a criterion names an oracle this run cannot reach, and nothing was read.
