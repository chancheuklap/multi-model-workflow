# Linting a batch

```bash
python3 scripts/verify-ticket.py <spec> --lint --drafts <dir>   # the batch's drafts, before any is published
python3 scripts/verify-ticket.py <n> --lint                     # one ticket, and the graph of the batch it sits under
python3 scripts/verify-ticket.py <spec> --lint                  # every sub-issue of the spec, then the graph once
```

The graph it checks is the tracker's blocking edges, the ones the `mmw` skill's `scripts/ticket_state.py` reads before a ticket may start, so an edge is fixed there, not in a ticket body (**principle-resume-from-durable-state**). Done when `ERROR` is at zero and every `WARN` has been either fixed or kept on purpose.

## Output

One `ERROR` or `WARN` line per finding, each naming its rule, then one verdict line per ticket: `#<n> LINT OK`, `#<n> LINT OK (<k> warning(s))` or `#<n> LINT FINDINGS: <e> error(s), <w> warning(s)`. A draft is named by its draft name instead of `#<n>`. A closed ticket's `ERROR` is printed and counts for nothing.
