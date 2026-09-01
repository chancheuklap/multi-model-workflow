# Vendored from unlazy

Source: https://github.com/Leonxlnx/unlazy, commit `da0b00a3` (snapshot kept at `docs/research/code-landing-refs/unlazy/`). Vendored 2026-08-29. Licence: MIT, see `LICENSE`.

## Files taken as-is (byte-identical to the snapshot)

`lib/check-supervisor.mjs`, `lib/process-tree.mjs`, `lib/regex-worker.mjs`, `lib/dispatch.mjs`.

The pass/fail logic is upstream's and is not edited here: three states, the exit-0-**and**-EXPECT `both conditions` rule, timeouts, output caps, the regex worker. `lib/dispatch.mjs` is imported by `gate-check.mjs` and returns empty when no scope is set, which is always the case here.

## Files taken with edits

| File | Edit |
| --- | --- |
| `gate-check.mjs` | The approval store is removed: `--approve`, the `~/.unlazy/approved` directory and its ownership and no-follow checks, the per-criterion records and their locks, and the `APPROVAL REQUIRED` / `NOT RUN` path. A `CHECK:` now runs as written. 894 lines upstream, 700 here. |
| `lib/gates.mjs` | A fenced block directly under a `CHECK:` is that command; every other fence is skipped whole, as upstream skips all of them. Upstream reads one line per attribute and drops the rest in silence, so a command longer than a line reaches the shell in half. A bare line under a `CHECK:` is an error naming the fenced block, so no reader has to infer where a command ends. Each criterion also records `attrEnd`, the line past its last attribute — for a fenced command, past the closing fence. |
| `gate-check.mjs` (second edit) | A criterion with no `EVIDENCE:` line gets one inserted at `attrEnd`, so it lands after the whole command rather than inside it. |
| `gate-lint.mjs` | `manual-gate` is an error, not a warning, and says where the criterion belongs instead. Upstream allows a ledger of hand-judged criteria and only warns once they pass half; here a criterion with no `CHECK:` has nobody but its own author to decide it, which is the one thing acceptance criteria exist to prevent. Judgements go to code review, which runs in another session; what only the user can look at gets its own ticket. |
| `tests/run-tests.mjs` | `GATE_CHECK` now resolves to `../gate-check.mjs` (upstream: `../scripts/gate-check.mjs`); the `STOP_HOOK` and `INSTALL` constants and the 13 `hook:` / `install:` cases that use them are removed, because `stop-hook.mjs` and `install-hooks.mjs` are not vendored; the runner no longer injects `--approve` and `UNLAZY_APPROVAL_DIR`. 19 of upstream's 32 cases remain. |
| `tests/lint-tests.mjs` | `LINT` now resolves to `../gate-lint.mjs`; the `lint: shipped leaf and node templates satisfy the documented size policy` case is removed, because `templates/` is not vendored — a ledger here is derived from the ticket body, never written from a template. Three cases used a command-less criterion to demonstrate advisory behaviour and now assert it as an error; they run against a new warnings-only ledger, and a new case pins the error in both modes. 19 cases. |

### Why the approval store went

Upstream's safety boundary is someone reading an inherited ledger and approving it once (`SECURITY.md:3`), because there a ledger arrives inside a repository someone else wrote. Here the `CHECK:` lines are written by the main agent onto a ticket in this user's own tracker, `--lint` audits how they are written before the ticket goes out, and the ticket is the thing the user reads. Nothing is inherited, so nobody ever read those records: `--approve` was passed on every run. Nothing reused them either — a record is keyed on the ledger's absolute path, and the ledger is a fresh temp file each run. What was left was a directory outside the repository that every host's sandbox then had to be widened for.

## Not vendored

`stop-hook.mjs`, `install-hooks.mjs`, `dispatch-check.mjs`, `templates/`, `references/`, `agents/`, and the remaining test files (`contract-tests.mjs`, `dispatch-tests.mjs`, `hardening-tests.mjs`) — all cover scope, leases, or the Stop hook, none of which this skill uses.

## Running the tests

```sh
cd tests && node run-tests.mjs && node lint-tests.mjs
```
