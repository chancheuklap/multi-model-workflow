---
name: verify-ticket
description: Runs a ticket's acceptance criteria and says which pass, lints tickets and the blocking graph of their batch, publishes a spec and its tickets to the tracker, and reads the tree of issues under a map, a spec or a ticket. Use when a ticket's criteria have to be run, when something has to be cut out of a ticket, and when a batch is about to be published.
---

# Verify ticket

Each acceptance criterion on a ticket carries a `CHECK:` command and the `EXPECT:` string a passing run prints. This skill runs them and prints the outcome. A criterion passes only when its `CHECK` exits 0 and its output matches `EXPECT`. Your reading of the output never stands in for either. The user accepts a closed ticket on these runs without reading its code, so a pass the product did not earn ships that behaviour unseen. The batch those tickets come in is linted and published here too, because a ticket published with a broken criterion or blocking edge is worked at night by an agent who cannot ask anyone about it.

The ticket is the only state (**principle-resume-from-durable-state**). Every run reads it fresh and carries nothing to the next run.

A criterion names an oracle by its bare name (`story-parity.py …`); `python3 scripts/verify-ticket.py` puts the `ui-acceptance` skill's `scripts/` on the `PATH` of the shell that runs a `CHECK:`, so an oracle run by hand needs that directory on `PATH`.

## Pick a branch

| When | Read |
| --- | --- |
| Something has to leave a ticket, and you have to say which kind of child it becomes | `references/child-issues.md` |
| A batch has to be linted: its drafts before any is published, one ticket and the graph it sits in, or every ticket under a published spec | `references/linting.md` |

## Run a ticket's criteria

`python3 scripts/verify-ticket.py <n>` runs the ticket's criteria; `--reverify` runs every criterion again, including the ones already ticked. It posts nothing on the ticket. A criterion that has to launch, reach or observe the running product binds the run to the `ui-acceptance` skill's `## Five rules while the product is running`.

- **Exit 0.** Every criterion met.
- **Exit 1.** Something is unmet or abandoned; a `FAIL` line above the summary shows what each failing criterion printed, and the line under the summary names the criteria it counts.
- **Exit 2.** The ticket could not be read or the run could not start, and nothing ran. Fix what stderr names and run it again.
- **Exit 3.** No product slot was free, and nothing ran. Nothing signals when a slot frees, so do not retry in a loop: carry on with other work and run the same command again when you next need its result. A run that waits for a slot is not a run that failed.

Done when the run has exited 0 or 1 and printed its summary line; exits 2 and 3 ran nothing and prove nothing about the ticket.

## Read the tree under an issue

When you need what is still open under a map, a spec or a ticket, read its tree. `python3 scripts/issue_tree.py <issue> [--root map|spec|ticket]` prints, as JSON, the tree of issues under one issue: a map, its specs, each spec's tickets, each ticket's children. `--root` says which layer `<issue>` is (default `spec`). It exits 2, with the reason on stderr, when the tracker could not be asked, answered with an error, has no such issue, or returned a list shorter than its count. Exit 2 means the tree was not read, not that it is small: a page left unread reads exactly like an issue with fewer children.

## Publish a spec or a batch

- `python3 scripts/verify-ticket.py --publish --spec-body <file> --title <title> [--map <map>]` publishes a spec, and with `--map` as a native sub-issue of that map. Exit 0: published, printed as the issue number. Exit 1: published, but the native parent could not be confirmed as `--map`; stderr says so. Exit 2: refused, nothing published; fix what stderr names and run it again.
- `python3 scripts/verify-ticket.py <spec> --publish --drafts <dir>` publishes a directory of ticket drafts as native sub-issues of the spec, in the draft shape the script's `--help` gives. Exit 0: every draft published, every blocking edge recorded, and `--lint` on the published spec reported no `ERROR`. Exit 1: published with a blocking edge that could not be recorded, or `--lint` on the published spec found one. Exit 2: refused before anything was created, or stopped after publishing some drafts; fix what stderr names. Every draft printed as `<draft> -> #<n>` is published (after a tracker failure, stderr lists them again as `already published: …`), and running `--drafts` again on a directory that still holds one publishes it a second time. So move the printed drafts out, write their `#<n>` in place of their names in the other drafts' `BLOCKED BY:` lines, and publish the rest. When the run stopped before every draft was printed, it recorded no blocking edge: record the edges among the drafts already published on the tracker yourself. When every draft was printed, only `--lint` on the spec is left to run.

Neither writes an event.

## Output

- **A criteria run.** For each criterion it runs, a `RUN` line, then a `PASS` or `FAIL` line with its exit, whether `EXPECT` matched, and its output (for a pass, only its fingerprint); then one summary line, `ALL MET`, `UNMET: …` or `HANDOFF REQUIRED: …`; under `UNMET` and `HANDOFF REQUIRED`, one line naming the criteria each counts. Without `--reverify`, a criterion already ticked is not run and gets no line.
- **`--lint`.** One `ERROR` or `WARN` line per finding, each naming its rule, then one verdict line per ticket: `#<n> LINT OK`, `#<n> LINT OK (<k> warning(s))` or `#<n> LINT FINDINGS: <e> error(s), <w> warning(s)`. A draft is named by its draft name instead of `#<n>`. Exit 0: no `ERROR` counts (a closed ticket's `ERROR` is printed and counts for nothing). Exit 1: a ticket or the graph has an `ERROR`; fix it and lint again. Exit 2: a criterion names an oracle this run cannot reach, and nothing was read; do what stderr names and lint again. No exit runs a `CHECK:` or posts a comment.
- **`--publish`.** With `--spec-body`, the spec's issue number. With `--drafts`, one `<draft> -> #<n>` line per draft, then the `--lint` output for the published spec.
- **`issue_tree.py`.** The tree as JSON: each issue's number, title and state; a spec's and a ticket's labels and blockers; for each issue with a layer below it, the tracker's `total` and `completed` count of that layer.

## Composing this skill

Another skill that has to run a ticket's criteria, or to record such a run, names this skill and lets it own what a criterion is and when it passes. It does not restate `CHECK:` and `EXPECT:`.
