# Drive one product

`mmw-release` step 3 reads this file. By then this product's loop is started, or a previous loop is still there to resume.

`<engine>` below is `bash <absolute path of scripts/release-flow.sh>`, the same path step 3 resolved.

**The engine owns the loop. You are its hands.** Progress, next action, repair count, and success come from engine state. Do not resume from session memory. Do not pick the next stage yourself. Do not keep a second log of what you already tried.

## State table: do what `where` says

Each round, first run:

```bash
<engine> where
```

Act on this output only. Do not predict the next state. A stage, a dispatch, or a self-heal after shipping starts can create new commits. Those commits are verified by that stage and by the final full-package result.

| Output | Do | Hand back? |
| --- | --- | --- |
| `STAGE:<name>` or `RETRY-STAGE:<name>` | `<engine> stage run --stage <name>`. The engine expands args, routes remote builds, runs diagnostics, writes the result from the exit code, and records findings | No |
| `SUCCESS:all stages done` | `<engine> exit-check` must return `DONE`, then `<engine> close` | No. Success without `DONE` is an engine bug. Do not announce success |
| `PAUSED:needs-context` | See "Pause: missing context" below. This is not the end | Hand back only after two failed attempts |
| `PAUSED:needs-redirection` | Read `<engine> receipt`. Give it to the user as-is | Yes. Protected paths, circuit breakers, and spent budget must not continue on their own |
| `CORRUPT:` / `FAILED-STAGE:` / `NO-STAGES:` | Read `<engine> receipt`. Do not run a stage. Do not `resume` | Yes |
| Any other output, or the command itself errors | Do not guess the state. Do not `init` again | Yes, with the raw output |

After a stage, ask `where` again until the table names a terminal state. **Do not stop to report to the user after every `where`.**

## After a stage fails

When `stage run` fails, the engine has already diagnosed and graded. Read `where`:

- `PAUSED` — the engine already stopped it. Read the state. Do not dispatch a fix.
- `RETRY-STAGE` — run `<engine> dispatch --stage <name>` once. The engine decides the fix from its ledger.
- After `dispatch`, `where` is still `STAGE` or `RETRY-STAGE` — run `<engine> round next` once, then return to the state table and re-run that stage.

`round next` records "already handled once". A clean full run does not consume a round.

**You do not grade P0, P1, or P2.** You do not edit the worktree to bypass a guard. You do not build a second executor. Grades, repair commits, and human-approval gates belong to the engine.

## Pause: missing context

`PAUSED:needs-context` means the engine lacks information it cannot judge. **Resolve it yourself when you can.**

1. `<engine> receipt` for what was already tried. Read engine logs, builder logs, and finding text from the latest record.
2. Diagnose from log text. Do not guess.
3. If you can act: environment issues (network, busy builder) you may handle. Code or config changes commit to the current branch as usual, and the current stage re-verifies them.
4. Run `<engine> resume`, then follow engine state through this stage and the remaining full-package checks.
5. **Same root cause twice, or the cause is billing, a contract, a protected path, or a product decision the user must make — stop and hand it over.** Do not loop.

## Remote build machine

A product that builds on another machine needs two facts: which machine, and which folder on it. The engine takes them from `RELEASE_REMOTE_HOST` and `RELEASE_REMOTE_ROOT`, and when either is empty it falls back to `remote-build.json` sitting next to that product's `.release-adapter.json`:

```json
{"host": "pc", "root": "D:/agentflow-release-input"}
```

Missing in both places is a `PAUSED:needs-context` you can often close yourself: the engine's log names the variable. Write the file so the next run does not stop here again. The environment variables win over the file — that is how a one-off switch to another machine is done.

## Close

- `SUCCESS` is not spoken success. Only `<engine> exit-check` returning `DONE` means the package is ready. Then `<engine> close`.
- Package paths come from this stage's `DELIVERED` lines. On gather failure, read the WARN path left in the build directory. If neither exists, say you have no path. Do not invent one.
- `close` leaves a delivery record (product name plus the ship commit). `mmw-release` step 4 uses it for the same-commit check. **Do not delete it by hand.**
- `CORRUPT`, `FAILED-STAGE`, and `NO-STAGES` never run the next stage and never `resume` on their own. The receipt is the only log of what was tried. Give it to the user as-is.
