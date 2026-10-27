# Linting a batch

You are about to publish a batch of tickets, have just published one, or are opening a night on a spec before its first `advance`.

```bash
python3 scripts/verify-ticket.py <spec> --lint --drafts <dir>   # the batch's drafts, before any is published
python3 scripts/verify-ticket.py <n> --lint                     # one ticket, and the graph of the batch it sits under
python3 scripts/verify-ticket.py <spec> --lint                  # every sub-issue of the spec, then the graph once
```

A draft is one file `<draft name>.md` in a directory of its own: the header lines `TITLE:`, `LABELS:` (comma-separated) and `BLOCKED BY:` (comma-separated draft names, `#<n>` for an issue already on the tracker, or `(none)`), all three required, then a line `---`, then the body exactly as it will be published. A draft's name stands in for the issue number it does not have yet, in `BLOCKED BY:` and in everything the lint prints. `python3 scripts/verify-ticket.py <spec> --publish --drafts <dir>` publishes them as they stand, as native sub-issues of the spec, with their labels and blocking edges, prints each draft's name beside its issue number, and ends by running `--lint` on the spec once; its exit is that lint's, or 1 when a blocking edge could not be recorded.

The graph it checks is the tracker's blocking edges, the same ones `--preflight` refuses on and `advance` dispatches from, so an edge is fixed there, not in a ticket body. The batch is ready when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose.

## Runner EXPECT standards

`runner-expect` is an `ERROR` on drafts and published tickets when a `CHECK:` contains `pytest` or `vitest` but its `EXPECT:` is not that runner's standard. The error names a real summary the pattern rejects on success or accepts on failure, when one exists, and prints the standard to copy. Count-pinned patterns and markers echoed by the command are not substitutes.

[runner-summaries.json](../scripts/runner-summaries.json) is the only home of the standard patterns and their real-run samples. Each sample records its command, output, exit code and acceptance outcome. Each runner names its version and the script that recorded its samples.

| Runner | Standard EXPECT to copy | Acceptance outcome |
| --- | --- | --- |
| pytest | `pytest.expect` in `runner-summaries.json` | Passed, xfailed and xpassed count as success. Skipped, failed, error and no tests ran count as failure. |
| Vitest | `vitest.expect` in `runner-summaries.json` | Passed with filtered skipped tests counts as success. Failed and No test files found count as failure. |

Copy the value unchanged, including its flags. Do not write another pattern from a sample output line.

Exit 0: no `ERROR`. Exit 1: fix each `ERROR` on its ticket, except one saying the tracker could not answer (tagged `[parent-unreadable]` or `[sub-issues-unreadable]`, or a traceback from a `gh` call): nothing about the tickets was established, so run the same command again once the tracker answers. Exit 2: nothing was read, because the tracker did not answer (stderr says `retry the same command`); run the same command again once it answers.
