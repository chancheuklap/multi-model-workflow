---
name: verify-ticket
description: Run one ticket's acceptance criteria, and close the ticket when they pass. Use when something has to be cut out of a ticket, and when a batch is about to be published.
---

# Verify ticket

Each acceptance criterion on a ticket carries a `CHECK:` command and the `EXPECT:` string a passing run prints. This skill runs them and posts the outcome on the ticket as an event.

The ticket is the only state. Every run reads it fresh, writes its events, and carries nothing to the next run. Every comment it posts is an event: a first line for a person and a trailing `<!-- mmw {...} -->` block, which is the only part any program reads.

A criterion names an oracle by its bare name (`story-parity.py …`); `python3 scripts/verify-ticket.py` puts the `ui-acceptance` skill's `scripts/` on the `PATH` of the shell that runs a `CHECK:`, so an oracle run by hand needs that directory on `PATH`.

Cutting a piece of work out of a ticket into a child issue is [references/sub-issues.md](references/sub-issues.md); checking a batch of tickets before it is published or run is [references/linting.md](references/linting.md).
