# Vendored from unlazy

Source: https://github.com/Leonxlnx/unlazy, commit `da0b00a3` (snapshot kept at
`docs/research/code-landing-refs/unlazy/`). Vendored 2026-08-29. Licence: MIT, see `LICENSE`.

## Files taken as-is (byte-identical to the snapshot)

`gate-check.mjs`, `gate-lint.mjs`, `lib/gates.mjs`, `lib/check-supervisor.mjs`,
`lib/process-tree.mjs`, `lib/regex-worker.mjs`, `lib/dispatch.mjs`.

The pass/fail logic is upstream's and is not edited here: three states, the
exit-0-**and**-EXPECT double condition, timeouts, output caps, the regex worker.
`lib/dispatch.mjs` is imported by `gate-check.mjs` and returns empty when no scope is
set, which is always the case here.

## Files taken with edits

| File | Edit |
| --- | --- |
| `tests/run-tests.mjs` | `GATE_CHECK` now resolves to `../gate-check.mjs` (upstream: `../scripts/gate-check.mjs`); the `STOP_HOOK` and `INSTALL` constants and the 13 `hook:` / `install:` cases that use them are removed, because `stop-hook.mjs` and `install-hooks.mjs` are not vendored. 19 of upstream's 32 cases remain. |
| `tests/lint-tests.mjs` | `LINT` now resolves to `../gate-lint.mjs`; the `lint: shipped leaf and node templates satisfy the documented size policy` case is removed, because `templates/` is not vendored — a ledger here is derived from the ticket body, never written from a template. 18 of upstream's 19 cases remain. |

## Not vendored

`stop-hook.mjs`, `install-hooks.mjs`, `dispatch-check.mjs`, `templates/`, `references/`,
`agents/`, and the remaining test files (`contract-tests.mjs`, `dispatch-tests.mjs`,
`hardening-tests.mjs`) — all cover scope, leases, or the Stop hook, none of which this
skill uses.

## Running the tests

```sh
cd tests && node run-tests.mjs && node lint-tests.mjs
```
