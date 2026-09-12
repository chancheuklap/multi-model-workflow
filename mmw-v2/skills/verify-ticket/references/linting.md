# Linting a batch

## Resolve `<engine>` once

`<engine>` is `scripts/verify-ticket.py`, resolved from this skill's own `SKILL.md` the way its **Resolve `<engine>` once** section says.

You are publishing a batch of tickets, or opening a night on a spec before its first `advance`.

```bash
<engine> <n> --lint       # one ticket, and the graph of the batch it sits under
<engine> <spec> --lint    # every sub-issue of the spec, then the graph once
```

## `--lint` on a batch

Given a ticket, `--lint` checks that ticket and the graph of the batch it sits under. Given the spec — an issue with no `## Acceptance criteria` carrying the layer label `mmw:spec`, or, when it carries no layer label at all, one with no parent and sub-issues of its own — it checks every sub-issue the same way, each under a line naming the ticket and its state, then the graph once, and ends with the list of tickets that had an `ERROR`. Closed tickets are included: a finding on one is stale text on the tracker, not a reason to stop, and the reader can see the state on the line above it.

Three things at once: how the criteria are written, which worker the ticket asks for, and whether the batch under the same spec is a startable graph — every ticket the spec lists as a sub-issue, the blocking links between them, and which of them nothing blocks. The graph comes from the tracker's blocking links, the same ones `--preflight` refuses on and `advance` dispatches from.

The worker reads the same way. `dispatch.sh` starts a ticket on the `models.json` row its `junior-worker` or `senior-worker` label names, so a ticket in the agent queue wearing no such label is an `ERROR  … [worker-label]`, and so is one wearing both.

The same run checks three criterion shapes. An interface ticket's `--pages` values must each be a `pages` mount of the contract and must not be an `App · ` page. A `boundary-check.py --run` must name a non-empty command. A `journey.py run <name>` must exist under the repository's `.mmw/journeys/`, unless the ticket's `## Owns` covers that directory — then this is the ticket that builds it, and it is absent until the work lands. A flag inside a quoted `--run` value belongs to the command that value carries, not to the judge. `vi.stubGlobal('fetch')`, msw, nock and fetch-mock are refused; mocking the product's own API client module is not.

The batch converges when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose.

The `[screen-contract]` findings are the interface rules made mechanical: an interface ticket without row ids in **Read first**, a `--pages` mount the contract does not declare or that names an `App · ` page, a `boundary-check.py --run` that is empty, a `journey.py run <name>` that is not under `.mmw/journeys/`, a `CHECK:` that stubs the application's own `fetch`, a pipeline script called without `--contract` (and `--pages` or `--run`) or with a flag its `--help` does not list or an address that belongs in `.mmw/target.json`, and a row source that is not under **Read first** or a spec section **Parent** does not name.

## Exit codes

`0` nothing reported an `ERROR`. `1` a ticket or the graph has one; on a spec, any of its sub-issues having one. `2` a criterion names a judge this run cannot reach, which is refused before anything is read.

No `CHECK:` runs and no comment is posted on any exit.
