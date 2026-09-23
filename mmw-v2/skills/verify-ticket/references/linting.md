# Linting a batch

`<engine>` is resolved in this skill's `SKILL.md`.

You are about to publish a batch of tickets, have just published one, or are opening a night on a spec before its first `advance`.

```bash
<engine> <spec> --lint --drafts <dir>   # the batch's drafts, before any is published
<engine> <n> --lint                     # one ticket, and the graph of the batch it sits under
<engine> <spec> --lint                  # every sub-issue of the spec, then the graph once
```

A batch is linted twice: its drafts before publishing, so the fixes are made while nothing is live, and the published batch after, because only the tracker shows what publishing did.

## `--drafts` before publishing

`<dir>` holds one file per ticket, named `<draft name>.md`. Each opens with header lines, then a line `---`, then the issue body exactly as it will be published:

```
TITLE: <the issue title>
LABELS: mmw:ticket, ready-for-agent, junior-worker
BLOCKED BY: T1-contract, #412
---
## Parent
...
```

`TITLE:`, `LABELS:` (comma-separated) and `BLOCKED BY:` (comma-separated draft names, `#<n>` for an issue already on the tracker, or `(none)`) are required; any other header line is the drafter's note and is not read. A draft's name, its file name without `.md`, stands in for the issue number it does not have yet, in `BLOCKED BY:` and in everything the run prints. The spec named on the command line is the spec every draft will sit under.

Each draft gets everything a published ticket gets under **`--lint` on a batch** below, with its labels read from `LABELS:`: its criteria, its worker label, its interface rules, and `## Parent` naming that spec first. A draft whose `LABELS:` lacks `mmw:ticket` is an `ERROR  … [layer-label]`, a `BLOCKED BY:` name that is no draft in `<dir>` an `ERROR  … [unknown-draft]`, and a file whose header cannot be read an `ERROR  … [draft-unreadable]`. The graph is built from the `BLOCKED BY:` headers and checked like the tracker's; a `#<n>` blocker is looked up on the tracker. The spec's own body is read from the tracker for the **Critical flows** rule and the section count; when it cannot be read, the run prints `WARN  … [spec-unreadable]`, skips the count, and the journey rule reports the unread spec as it does for a published ticket.

The run ends with the checks it could not run, because only a published batch has them: that each ticket is a sub-issue of the spec and carries its labels on the tracker, the blocking links the tracker records, and each title against its `## What to build`.

## `--lint` on a batch

Given a ticket, `--lint` checks that ticket and the graph of the batch it sits under. Given the spec — an issue with no `## Acceptance criteria` carrying the layer label `mmw:spec`, or, when it carries no layer label at all, one with no parent and sub-issues of its own — it checks every sub-issue the same way, each under a line naming the ticket and its state, then the graph once, and ends with the list of tickets that had an `ERROR`. Closed tickets are included: a finding on one is stale text on the tracker, not a reason to stop, and the reader can see the state on the line above it.

Three things at once: how the criteria are written, which worker the ticket asks for, and whether the batch under the same spec is a startable graph — every ticket the spec lists as a sub-issue, the blocking links between them, and which of them nothing blocks. The graph comes from the tracker's blocking links, the same ones `--preflight` refuses on and `advance` dispatches from.

For the worker: `dispatch.sh` starts a ticket on the `models.json` row its `junior-worker` or `senior-worker` label names, so a ticket in the agent queue carrying both is an `ERROR  … [worker-label]`, and one carrying neither is a `WARN` and starts on the `junior-worker` row.

The same run checks the criterion shapes against the screen contract. A `screen-contract.yaml rows: …` line under `## Read first` makes the ticket an interface ticket even when it omitted every judge; conversely, a ticket that runs `story-parity.py` without that line is an `ERROR`. Every named row must exist in the contract. For each row, the contract's `component` and `pages` declarations determine its design page and mount; a cross-component row uses its `app` page. Every claimed mount, including an `App · ` mount, must appear in a story criterion, and a mount named by `--pages` but declared by no contract page is an `ERROR`. Every row whose `calls` is not `none` or whose `next` is not `stay` needs a boundary criterion, and every cross-component row needs one regardless of those two columns.

A `boundary-check.py --run` must name a non-empty command and a test file. When a named test file exists, each owned row's string `trigger` data-ui id must appear in one of the readable files; absence, an unreadable file, and a non-string `trigger` are `ERROR`. A test file that has not been written yet is `WARN`, because batch publication happens before implementation, and the message names the rows whose ids that file did not check.

A `journey.py run <name>` must exist under the repository's `.mmw/journeys/`, unless the ticket's `## Owns` covers that directory — then this is the ticket that builds it, and it is absent until the work lands. A smoke journey and the contract ticket need no `--break`. A journey whose flow is under the spec's **Critical flows** and whose Implementation Decisions sections the ticket names is an acceptance journey: omitting `--break` is `ERROR`. A **Critical flows** line is read in one shape, ``- `<flow>`: Implementation Decisions sections <n>, <n>``, nested under the marker or on the marker line itself; the section numbers follow the words `Implementation Decisions`, in English as `## Parent` names them, in whatever language the rest of the line is (`Implementation Decisions 第 6、8、9 节` reads). The bullet ends where its own list ends, at the next line indented no deeper than the marker. A line in it that lacks the flow name or those words is an `ERROR` that quotes the expected shape. Omitting it on another user-named journey is `WARN`, because the journey cannot reject a script that only reads a success message and the flow may have no write to break. If the parent spec cannot be read, the lint reports an `ERROR`.

A flag inside a quoted `--run` value belongs to the command that value carries, not to the judge. `vi.stubGlobal('fetch')`, and the whole names msw, nock and fetch-mock, are refused; a larger ordinary word that merely contains those letters is not. Mocking the product's own outbound call module is allowed.

After the ticket graph, the same run reads `## Implementation Decisions` on the spec for each `### <n>.` heading and, from every sub-issue's `## Parent` (open and closed), the section numbers `parent_sections` finds. Each spec section no ticket names is one line `WARN #<spec> Implementation Decisions section <n> is named by no ticket's ## Parent [uncovered-section]`. Only an explicit section number in `## Parent` counts; a keyword in the ticket body does not.

Two `CHECK:` shapes are refused as `[undecidable-check]`, because neither can decide the criterion it is written under: one ending in a `grep` whose EXPECT is satisfied by exactly what a run that selected nothing prints, which no code can ever make exit 0; and one that sends the command's stdout and stderr to `/dev/null` and matches a line the CHECK itself echoes from `$?`, which any command exiting that way passes, including one that failed for another reason.

The batch is ready when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose.

`## Parent` names the spec the ticket sits under first: the first issue there is what the scripts read as its spec when the tracker has no parent link, and what `--drafts` has in place of one. A contract row may cite an earlier spec's section as its source; that spec and its sections are named after the parent spec, in the same words (`#555, Implementation Decisions sections 4 and 11; #318 Implementation Decisions section 4`), and the row's source is then satisfied. A `## Parent` that names another issue first is an `ERROR  … [parent-order]` wherever the spec is known: on `--drafts`, on a spec's sub-issues, and on a ticket the tracker links to its spec.

The `[screen-contract]` findings are those interface rules made mechanical, plus a pipeline script called without `--contract` (and `--pages` or `--run`), with a flag its `--help` does not list, or with an address that belongs in `.mmw/target.json`; a story criterion whose `--pages` mount is absent from the contract; an interface ticket that omitted `screen-contract.yaml rows: …`; and a row source that is not under **Read first** or a spec section **Parent** does not name.

## Exit codes

`0` nothing reported an `ERROR`. `1` a ticket or the graph has one; on a spec, any of its open sub-issues having one (a closed one's `ERROR` is printed and counts for nothing). `2` a criterion names a judge this run cannot reach, which is refused before anything is read.

No `CHECK:` runs and no comment is posted on any exit.
