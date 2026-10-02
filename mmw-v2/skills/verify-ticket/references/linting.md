# Linting a batch

```bash
python3 scripts/verify-ticket.py <spec> --lint --drafts <dir>   # the batch's drafts, before any is published
python3 scripts/verify-ticket.py <n> --lint                     # one ticket, and the graph of the batch it sits under
python3 scripts/verify-ticket.py <spec> --lint                  # every sub-issue of the spec, then the graph once
```

The graph it checks is the tracker's blocking edges, the same ones `ticket_state.py --claim` refuses on and `advance` dispatches from, so an edge is fixed there, not in a ticket body (**principle-resume-from-durable-state**). The batch is ready when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose.
