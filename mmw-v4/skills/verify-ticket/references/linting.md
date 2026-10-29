# Linting a batch

You are about to publish a batch of tickets, have just published one, or are opening a night on a spec before its first `advance`.

```bash
python3 scripts/verify-ticket.py <spec> --lint --drafts <dir>   # the batch's drafts, before any is published
python3 scripts/verify-ticket.py <n> --lint                     # one ticket, and the graph of the batch it sits under
python3 scripts/verify-ticket.py <spec> --lint                  # every sub-issue of the spec, then the graph once
```

A draft is one file `<draft name>.md` in a directory of its own: the header lines `TITLE:`, `LABELS:` (comma-separated) and `BLOCKED BY:` (comma-separated draft names, `#<n>` for an issue already on the tracker, or `(none)`), all three required, then a line `---`, then the body exactly as it will be published. A draft's name stands in for the issue number it does not have yet, in `BLOCKED BY:` and in everything the lint prints. `python3 scripts/verify-ticket.py <spec> --publish --drafts <dir>` publishes them as they stand, as native sub-issues of the spec, with their labels and blocking edges, prints each draft's name beside its issue number, and ends by running `--lint` on the spec once; its exit is that lint's, or 1 when a blocking edge could not be recorded.

The graph it checks is the tracker's blocking edges, the same ones `--preflight` refuses on and `advance` dispatches from, so an edge is fixed there, not in a ticket body. The batch is ready when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose.

## Run draft checks on the base

`--lint --drafts <dir> --base <ref>` runs every draft's `CHECK:` once through gate-check in a throwaway detached checkout. The default ref is `origin/<current checkout branch>`, the project branch. If the ref does not exist, lint exits 2, names `--base`, and runs nothing. Pass `--base <ref>` to select an existing base explicitly.

Each draft uses its `TIMEOUT:` limit, with `MMW_BASE_REF` set to the selected ref and `MMW_TICKET` set to its draft name. The checkout is removed after the run. For every criterion, lint prints `PASS` or `FAIL` on the base and the last five lines of captured output.

- `passes-on-base` is a `WARN` when both the exit code and `EXPECT:` pass on the base. The criterion is either a pin or a `CHECK:` that cannot see this ticket's work. Read the warning and either fix the command or keep the pin on purpose.
- `no-runner-summary` is an `ERROR` when a `CHECK:` runs pytest or Vitest but prints none of that runner's known summary forms from [runner-summaries.json](../scripts/runner-summaries.json). Success and failure summaries both count. pytest's `no tests ran` and Vitest's `No test files found` count as failure summaries when a ticket's test file does not exist on the base.

A failed base check alone is not a lint error. New behaviour is expected to fail there. Published-ticket and published-spec `--lint` runs only static checks and never runs acceptance commands on a base.

## Build points name their criteria

`build-point-without-criterion` is an `ERROR` on drafts and published tickets when a numbered point under `## What to build` names no `AC<n>`, or names an `AC<n>` absent from `## Acceptance criteria`. The error identifies the point and any nonexistent criterion. `## What to build` must contain at least one numbered point. Tickets without acceptance criteria, including `mmw:problem` drafts and `ready-for-human` tickets, are exempt. A `ready-for-agent` ticket without acceptance criteria still fails with `no-criteria`.

`dispatch.sh route <ticket> <child> fixed` runs `verify-ticket.py <ticket> --lint` before closing the child or recording its resolution. If lint exits 1 or 2, route passes on its output, exits 2, and closes and records nothing. Correct the ticket and retry the route command.

## Read first sources workers can open

`unreadable-read-first` is an `ERROR` on drafts and published tickets for each line under `## Read first` that links to `claude.ai`, including `/artifact/` and `/code/artifact/` paths. The error names the line and asks the author to copy what the page settles into a file in the repository, commit it, and cite that path. Links to `claude.ai` elsewhere in the ticket do not raise this error.

## Runner EXPECT standards

`runner-expect` is an `ERROR` on drafts and published tickets when a `CHECK:` stage runs `pytest` or `vitest` as its command but its `EXPECT:` is not that runner's standard. The error names a real summary the pattern rejects on success or accepts on failure, when one exists, and prints the standard to copy. Count-pinned patterns and markers echoed by the command are not substitutes. Commands behind `uv run`, `pnpm`, `npx` and `python -m` count. A runner name used only as an argument, such as `grep -q vitest package.json`, does not. A criterion running both runners gets `runner-expect` and must be split into one criterion per runner.

[runner-summaries.json](../scripts/runner-summaries.json) is the only home of the standard patterns and their real-run samples. Each runner's `summary_pattern` recognises both success and failure summaries for the draft base run. Each sample records its command, output, exit code and acceptance outcome. Each runner names its version and the script that recorded its samples.

| Runner | Standard EXPECT to copy | Acceptance outcome |
| --- | --- | --- |
| pytest | `pytest.expect` in `runner-summaries.json` | Passed, passed subtests, xfailed and xpassed count as success. Skipped, failed, error and no tests ran count as failure. |
| Vitest | `vitest.expect` in `runner-summaries.json` | Passed counts as success, with skipped and todo allowed beside it. Failed, No test files found, and a summary with no passed test count as failure. |

Copy the value unchanged, including its flags. Do not write another pattern from a sample output line.

Exit 0: no `ERROR`. Exit 1: fix each `ERROR` on its ticket, except one saying the tracker could not answer (tagged `[parent-unreadable]` or `[sub-issues-unreadable]`, or a traceback from a `gh` call): nothing about the tickets was established, so run the same command again once the tracker answers. Exit 2 on drafts also reports an unavailable `--base` or a base checkout that could not run. Fix the named ref or checkout failure and retry. Exit 2 from a tracker read means nothing was read, because the tracker did not answer (stderr says `retry the same command`); run the same command again once it answers.
