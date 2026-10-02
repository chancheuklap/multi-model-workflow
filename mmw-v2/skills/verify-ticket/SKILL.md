---
name: verify-ticket
description: Runs a ticket's acceptance criteria and says which pass, lints tickets and the blocking graph of their batch, publishes a spec and its tickets to the tracker, and reads the tree of issues under a map, a spec or a ticket. Use when a ticket's criteria have to be run, and when a batch is about to be published.
---

# Verify ticket

Each acceptance criterion on a ticket carries a `CHECK:` command and the `EXPECT:` string a passing run prints. This skill runs them and prints the outcome. A criterion passes only when its `CHECK` exits 0 and its output matches `EXPECT`. Your reading of the output never stands in for either. The user accepts a closed ticket on these runs without reading its code, so a pass the product did not earn ships that behaviour unseen. The batch those tickets come in is linted and published here too, because a ticket published with a broken criterion or blocking edge is worked at night by an agent who cannot ask anyone about it.

The ticket is the only state (**principle-resume-from-durable-state**). Every run reads it fresh and carries nothing to the next run.

A criterion names an oracle by its bare name (`story-parity.py …`); `python3 scripts/verify-ticket.py` puts the `ui-acceptance` skill's `scripts/` on the `PATH` of the shell that runs a `CHECK:`, so an oracle run by hand needs that directory on `PATH`.

## Pick a branch

| When | Read |
| --- | --- |
| A batch has to be linted: its drafts before any is published, one ticket and the graph it sits in, or every ticket under a published spec | `references/linting.md` |

## Run a ticket's criteria

`python3 scripts/verify-ticket.py <n>` runs the ticket's criteria; `--reverify` runs every criterion again, including the ones already ticked. A criterion that has to launch, reach or observe the running product binds the run to the `ui-acceptance` skill's `## Five rules while the product is running`.

Exit 3 means no product slot was free, and nothing ran. Nothing signals when a slot frees, so do not retry in a loop: carry on with other work and run the same command again when you next need its result. A run that waits for a slot is not a run that failed.

Done when the run has exited 0 or 1 and printed its summary line; exits 2 and 3 ran nothing and prove nothing about the ticket.

## Read the tree under an issue

When you need what is still open under a map, a spec or a ticket, read its tree. `python3 scripts/issue_tree.py <issue> [--root map|spec|ticket]` prints, as JSON, the tree of issues under one issue: a map, its specs, each spec's tickets, each ticket's children. `--root` says which layer `<issue>` is (default `spec`). It exits 2, with the reason on stderr, when the tracker could not be asked, answered with an error, has no such issue, or returned a list shorter than its count. Exit 2 means the tree was not read, not that it is small: a page left unread reads exactly like an issue with fewer children.

Done when `issue_tree.py` has exited 0; exit 2 read no tree.

## Publish a spec or a batch

- `python3 scripts/verify-ticket.py --publish --spec-body <file> --title <title> [--map <map>]` publishes a spec, and with `--map` as a native sub-issue of that map.
- `python3 scripts/verify-ticket.py <spec> --publish --drafts <dir>` publishes a directory of ticket drafts as native sub-issues of the spec, in the draft shape the script's `--help` gives. Every draft printed as `<draft> -> #<n>` is published (after a tracker failure, stderr lists them again as `already published: …`), and running `--drafts` again on a directory that still holds one publishes it a second time. So move the printed drafts out, write their `#<n>` in place of their names in the other drafts' `BLOCKED BY:` lines, and publish the rest. When the run stopped before every draft was printed, it recorded no blocking edge: record the edges among the drafts already published on the tracker yourself. When every draft was printed, only `--lint` on the spec is left to run.

Done when the spec's number is printed, or every draft is published with its blocking edges recorded and `--lint` on the spec reports no `ERROR`.

## Output

- **A criteria run.** For each criterion it runs, a `RUN` line, then a `PASS` or `FAIL` line with its exit, whether `EXPECT` matched, and its output (for a pass, only its fingerprint); then one summary line, `ALL MET`, `UNMET: …` or `HANDOFF REQUIRED: …`; under `UNMET` and `HANDOFF REQUIRED`, one line naming the criteria each counts. Without `--reverify`, a criterion already ticked is not run and gets no line.
- **`--lint`.** As `references/linting.md` `## Output` says.
- **`--publish`.** With `--spec-body`, the spec's issue number. With `--drafts`, one `<draft> -> #<n>` line per draft, then the `--lint` output for the published spec.
- **`issue_tree.py`.** The tree as JSON: each issue's number, title and state; a spec's and a ticket's labels and blockers; for each issue with a layer below it, the tracker's `total` and `completed` count of that layer.

## Composing this skill

Another skill that has to run a ticket's criteria, or to record such a run, names this skill and lets it own what a criterion is and when it passes. It does not restate `CHECK:` and `EXPECT:`.
