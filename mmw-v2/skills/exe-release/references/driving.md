# Drive one product

`exe-release` step 3 reads this file. By then this product's loop is started, or a previous loop is still there to resume.

**The release engine owns the loop.** Progress, next action, repair count, and success come from release engine state. Do not resume from session memory. Do not pick the next stage yourself. Do not keep a second log of what you already tried.

## State table: do what `where` says

Each round, first run:

```bash
<release> where
```

Every verdict, `PAUSED` and `CORRUPT:` included, exits 0: read the state from stdout, never from the exit code. Exit 1 is one `ERROR:` line on stderr naming the fact the release engine cannot get past.

| Output | Do | Stop and report to the user? |
| --- | --- | --- |
| `STAGE:<name>` | `<release> stage run --stage <name>` | No |
| `RETRY-STAGE:<name>` | The stage failed. See "After a stage fails" below | No |
| `PAUSED:needs-context` with a `FIX-BRIEF=` line on `dispatch`'s output (a later session finds it as `release-fix-brief.md` beside the findings file `receipt` lists) | Read that brief. It names the findings and what to change. Fix, **commit**, then `<release> resume` | No |
| `SUCCESS:all stages done` | `<release> exit-check` must return `DONE`, then `<release> close` | No. Success without `DONE` is a release engine bug. Do not announce success |
| `PAUSED:needs-context` | See "Pause: missing context" below. This is not the end | Only after two failed attempts |
| `PAUSED:needs-redirection` | Read `<release> receipt`. Give it to the user as-is | Yes. Protected paths, circuit breakers, and spent budget must not continue on their own |
| `CORRUPT:` / `NO-STAGES:` | Read `<release> receipt`. Do not run a stage. Do not `resume` | Yes |
| Any other output, or the command itself errors | Do not guess the state. Do not `init` again | Yes, with the raw output |

After a stage, ask `where` again until the table names a terminal state. **Do not stop to report to the user after every `where`.**

## After a stage fails

When `stage run` fails, the release engine has already diagnosed the failure and assigned its tier. Read `where`:

- `PAUSED` — the release engine already stopped it. Read the state. Do not dispatch a fix.
- `RETRY-STAGE` — run `<release> dispatch --stage <name>` once. The release engine decides the fix from its ledger.
- After `dispatch`, `where` is still `STAGE` or `RETRY-STAGE` — run `<release> round next` once, then run the stage `where` names (`<release> stage run --stage <name>`), then return to the state table.

`round next` records "already handled once". A clean full run does not consume a round.

**You do not assign the tier (P0, P1 or P2).** You do not edit the worktree to bypass a guard. You do not build a second executor. Tiers, repair commits, and human-approval gates belong to the release engine.

## Pause: missing context

`PAUSED:needs-context` means the release engine lacks information it cannot judge. **Resolve it yourself when you can.**

1. `<release> receipt` for what was already tried. Read release engine logs, builder logs, and finding text from the latest record.
2. Diagnose from log text. Do not guess.
3. If you can act: environment issues (network, busy builder) you may handle. When `dispatch` printed an `ENV-ACTION:` line, that line already names the environment action this step is asking for, and no fix was dispatched — do that action, and `resume` is the whole of step 4. **Code or config changes commit to the current branch**, and the current stage re-verifies them.
4. Run `<release> resume`, then follow release engine state through this stage and the remaining full-package checks.
5. **Same root cause twice, or the cause is billing, a contract, a protected path, or a product decision the user must make — stop and report to the user.** Do not loop.

Step 3 says commit because the remote build ships `git archive HEAD`. A change left in the
worktree never reaches the build machine, so the next round rebuilds the same code and fails the
same way. `resume` sees the new HEAD and re-verifies every stage — that is what you want after a
code change.

## Close

- Package paths come from the build stage's `DELIVERED` lines. On gather failure, read the WARN path left in the build directory. If neither exists, say you have no path. Do not invent one.
- `close` leaves a delivery record (product name plus the ship commit). `exe-release` step 4 uses it for the same-commit check. **Do not delete it by hand.**
- **A round that is not going to produce a package ends with `<release> abort`, never `close`.** `close` writes that delivery record unconditionally — use it on a round that failed, or on one you are abandoning to ship a different product first, and you have written down a package that does not exist, on top of the last record that was true. `abort` drops the round and keeps the artifacts; it writes no record.

## An interrupted build

An interrupted build keeps running on the build machine. Run the stage `where` names again: `stage run` asks the build machine whether this round (same commit, same product) is still running and attaches to it. Do not `abort` or `init` to restart it: a fresh round wipes the source tree that build is reading.
