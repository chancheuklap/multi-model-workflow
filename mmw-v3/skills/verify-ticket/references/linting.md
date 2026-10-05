# Linting a batch

You are about to publish a batch of tickets, have just published one, or are opening a night on a spec before its first `advance`.

```bash
python3 scripts/verify-ticket.py <spec> --lint --drafts <dir>   # the batch's drafts, before any is published
python3 scripts/verify-ticket.py <n> --lint                     # one ticket, and the graph of the batch it sits under
python3 scripts/verify-ticket.py <spec> --lint                  # every sub-issue of the spec, then the graph once
```

A draft is one file `<draft name>.md` in a directory of its own: the header lines `TITLE:`, `LABELS:` (comma-separated) and `BLOCKED BY:` (comma-separated draft names, `#<n>` for an issue already on the tracker, or `(none)`), all three required, then a line `---`, then the body exactly as it will be published. A draft's name stands in for the issue number it does not have yet, in `BLOCKED BY:` and in everything the lint prints. `python3 scripts/verify-ticket.py <spec> --publish --drafts <dir>` publishes them as they stand, as native sub-issues of the spec, with their labels and blocking edges, prints each draft's name beside its issue number, and ends by running `--lint` on the spec once; its exit is that lint's, or 1 when a blocking edge could not be recorded. The drafts run does not stand in for that run on the published spec: only that one sees the tracker's labels, sub-issues and blocking edges.

The graph it checks is the tracker's blocking edges, the same ones `--preflight` refuses on and `advance` dispatches from, so an edge is fixed there, not in a ticket body. The batch is ready when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose.

Exit 0: no `ERROR`. Exit 1: fix each `ERROR` on its ticket, except one saying the tracker could not answer (tagged `[parent-unreadable]` or `[sub-issues-unreadable]`, or a traceback from a `gh` call): nothing about the tickets was established, so run the same command again once the tracker answers. Exit 2: nothing was read, because a criterion names an oracle this run cannot reach, or the tracker did not answer (stderr says `retry the same command`); for the tracker, run the same command again once it answers.
