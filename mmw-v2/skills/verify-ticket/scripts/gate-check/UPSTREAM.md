# Vendored from unlazy

Source: https://github.com/Leonxlnx/unlazy, commit `16671491` (2026-09-03). Licence: MIT, see `LICENSE`. Compare against that commit: `docs/research/code-landing-refs/unlazy/` is an older research snapshot (`da0b00a3`) and no longer matches these files.

## Files taken as-is (byte-identical to upstream at that commit)

`lib/check-supervisor.mjs`, `lib/process-tree.mjs`, `lib/regex-worker.mjs`, `lib/dispatch.mjs`.

The pass/fail logic is upstream's and is not edited here: the gate states `gateState` returns, the exit-0-**and**-EXPECT `both conditions` rule, evidence bound to the definition that produced it (`automatic-evidence=v1; definition-sha256=…`, so a pass recorded for a `CHECK:`, `EXPECT:` or `CWD:` that has since changed reads as unmet), timeouts, the output cap on the joined stdout and stderr, the regex worker. `lib/dispatch.mjs` is imported by `gate-check.mjs` and returns empty when no scope is set, which is always the case here.

## Files taken with edits

| File | Edit |
| --- | --- |
| `gate-check.mjs` | The approval store is removed: `--approve`, the `~/.unlazy/approved` directory and its ownership and no-follow checks, the per-criterion records and their locks, and the `APPROVAL REQUIRED` / `NOT RUN` path. A `CHECK:` now runs as written. The runtime oracle signature that discards a result whose criterion changed while it ran stays, named `oracleSignature` (upstream: `approvalOracleSignature`). 960 lines upstream, 769 here. |
| `lib/gates.mjs` | A fenced block directly under a `CHECK:` is that command; every other fence is skipped whole, as upstream skips all of them. Upstream reads one line per attribute and drops the rest in silence, so a command longer than a line reaches the shell in half. A bare line under a `CHECK:` is an error naming the fenced block, so no reader has to infer where a command ends. Each criterion also records `attrEnd`, the line past its last attribute — for a fenced command, past the closing fence. |
| `gate-check.mjs` (second edit) | A criterion with no `EVIDENCE:` line gets one inserted at `attrEnd`, so it lands after the whole command rather than inside it. |
| `gate-check.mjs` (third edit) | A criterion that fails records its evidence instead of `pending`: exit code (and signal or error when there is one), whether EXPECT matched, the output's sha256 and byte count, shell, cwd, the `path=` fingerprint, and the same output summary the `FAIL` console line already prints — a pass's fields in a pass's order, without the `automatic-evidence` prefix, which binds a pass and nothing else. Upstream writes nothing for a failure on an unticked criterion and demotes a ticked or stale one to `pending`; here the condition that decides between the two (`mustWriteFailure`) is removed, so every failure is written. Before this edit a `--reverify` that turned a met criterion red wrote `pending` over it — so a red that did not repeat could never be explained, because its output was on a stdout nobody kept (measured 2026-09-10, #320 and #327). The pass/fail decision is untouched: the checkbox is still the authority, and every reader (`gateState`, and `verify-ticket.py`'s tally) counts a criterion met only when it is ticked. |
| `gate-lint.mjs` | `manual-gate` is an error, not a warning, and says where the criterion belongs instead. Upstream allows a ledger of hand-judged criteria and only warns once they pass half; here a criterion with no `CHECK:` has nobody but its own author to decide it, which is the one thing acceptance criteria exist to prevent. Judgements go to code review, which runs in another session; what only the user can look at gets its own ticket. |
| `tests/run-tests.mjs` | `GATE_CHECK` now resolves to `../gate-check.mjs` (upstream: `../scripts/gate-check.mjs`); the `STOP_HOOK` and `INSTALL` constants and the 15 `hook:` / `install:` cases that use them are removed, because `stop-hook.mjs` and `install-hooks.mjs` are not vendored; the runner no longer injects `--approve` and `UNLAZY_APPROVAL_DIR`. 19 of upstream's 34 cases remain, plus two added here for failure evidence and four taken from upstream's `hardening-tests.mjs` with their approval steps removed and a failure expected to record itself: the definition digest's golden vector and state table, a changed `CHECK:` making old evidence stale, a long transcript not truncating the digests, and the output cap on the joined streams (25). |
| `tests/lint-tests.mjs` | `LINT` now resolves to `../gate-lint.mjs`; the `lint: shipped leaf and node templates satisfy the documented size policy` case is removed, because `templates/` is not vendored — a ledger here is derived from the ticket body, never written from a template. Three cases used a command-less criterion to demonstrate advisory behaviour and now assert it as an error; they run against a new warnings-only ledger, and a new case pins the error in both modes. Three more (terminal escaping in text and JSON, bounded field expansion) and the finding-cap case give their criteria a `CHECK:` and `EXPECT:` so they stay warnings-only; the finding-cap case's totals follow (80 warnings, 16 omitted, where upstream's command-less gates gave 241 and 177). 29 cases. |

### Why the approval store went

Upstream's safety boundary is someone reading an inherited ledger and approving it once (`SECURITY.md:3`), because there a ledger arrives inside a repository someone else wrote. Here the `CHECK:` lines are written by the main agent onto a ticket in this user's own tracker, `--lint` audits how they are written before the ticket goes out, and the ticket is the thing the user reads. Nothing is inherited, so nobody ever read those records: `--approve` was passed on every run. Nothing reused them either — a record is keyed on the ledger's absolute path, and the ledger is a fresh temp file each run. What was left was a directory outside the repository that every host's sandbox then had to be widened for.

## Not vendored

`stop-hook.mjs`, `install-hooks.mjs`, `dispatch-check.mjs`, `templates/`, `references/`, `agents/`, and the remaining test files (`contract-tests.mjs`, `dispatch-tests.mjs`, `hardening-tests.mjs` apart from the four cases named above, `stress-tests.mjs`, `self-check.mjs`) — they cover scope, leases, the Stop hook and its installer, the approval store, Windows file identity, and the shipped skill package, none of which this skill uses.

## Running the tests

```sh
cd tests && node run-tests.mjs && node lint-tests.mjs
```
