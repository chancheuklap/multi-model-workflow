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

The same run checks the criterion shapes against the screen contract. A `screen-contract.yaml rows: …` line under `## Read first` makes the ticket an interface ticket even when it omitted every judge. For each named row, the contract's `component` and `pages` declarations determine its design page and mount; a cross-component row uses its `app` page. Every claimed mount, including an `App · ` mount, must appear in a story criterion. Every row whose `calls` is not `none` or whose `next` is not `stay` needs a boundary criterion, and every cross-component row needs one regardless of those two columns.

A `boundary-check.py --run` must name a non-empty command. When its named test file exists, each owned row's `trigger` data-ui id must appear in one of those files; absence and an unreadable file are `ERROR`. A test file that has not been written yet is `WARN`, because batch publication happens before implementation, and the message states that its ids were not checked.

A `journey.py run <name>` must exist under the repository's `.mmw/journeys/`, unless the ticket's `## Owns` covers that directory — then this is the ticket that builds it, and it is absent until the work lands. A smoke journey and the contract ticket need no `--break`. A journey whose flow is under the spec's **Critical flows** and whose Implementation Decisions sections the ticket names is an acceptance journey: omitting `--break` is `ERROR`. Omitting it on another owner-named journey is `WARN`, because the journey cannot reject a script that only reads a success message and the flow may have no write to break.

A flag inside a quoted `--run` value belongs to the command that value carries, not to the judge. `vi.stubGlobal('fetch')`, and the whole names msw, nock and fetch-mock, are refused; a larger ordinary word that merely contains those letters is not. Mocking the product's own outbound call module is allowed.

After the ticket graph, the same run reads `## Implementation Decisions` on the spec for each `### <n>.` heading and, from every sub-issue's `## Parent` (open and closed), the section numbers `parent_sections` finds. Each spec section no ticket names is one line `WARN #<spec> Implementation Decisions section <n> is named by no ticket's ## Parent [uncovered-section]`. The run ends that pass with `sections named by a ticket: <k>/<n>`. A WARN does not change the exit code. Only an explicit section number in `## Parent` counts; a keyword in the ticket body does not.

The batch converges when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose.

The `[screen-contract]` findings are those interface rules made mechanical, plus a pipeline script called without `--contract` (and `--pages` or `--run`), with a flag its `--help` does not list, or with an address that belongs in `.mmw/target.json`; and a row source that is not under **Read first** or a spec section **Parent** does not name.

## Exit codes

`0` nothing reported an `ERROR`. `1` a ticket or the graph has one; on a spec, any of its sub-issues having one. `2` a criterion names a judge this run cannot reach, which is refused before anything is read.

No `CHECK:` runs and no comment is posted on any exit.
