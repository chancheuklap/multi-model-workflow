# Drive one product

`exe-release` step 3 reads this file. By then this product's loop is started, or a previous loop is still there to resume.

**The release engine owns the loop.** Progress, next action, repair count, and success come from release engine state. Do not resume from session memory. Do not pick the next stage yourself. Do not keep a second log of what you already tried. You do not assign the tier (P0, P1 or P2).

## State table: do what `where` says

Each round, first run:

```bash
bash scripts/release-flow.sh where
```

Every verdict, `PAUSED` and `CORRUPT:` included, exits 0: read the state from stdout, never from the exit code. Exit 1 is one `ERROR:` line on stderr naming the fact the release engine cannot get past.

| Output | Do | Stop and report to the user? |
| --- | --- | --- |
| `STAGE:<name>` | `bash scripts/release-flow.sh stage run --stage <name>` — when the stage fails, it dispatches a fix and counts the round itself before returning | No |
| `PAUSED:needs-context` | See "Pause: missing context" below. This is not the end | Only after two failed attempts |
| `SUCCESS:all stages done` | `bash scripts/release-flow.sh close` | No |
| `PAUSED:needs-redirection` | Read `bash scripts/release-flow.sh receipt`. Give it to the user as-is | Yes. Circuit breakers and spent budget must not continue on their own |
| `CORRUPT:` | Read `bash scripts/release-flow.sh receipt`. Do not run a stage. Do not `resume` | Yes |
| Any other output, or the command itself errors | Do not guess the state. Do not `init` again | Yes, with the raw output |

After a stage, ask `where` again until the table names a terminal state. **Do not stop to report to the user after every `where`.**

## Pause: missing context

`PAUSED:needs-context` means the release engine lacks information it cannot judge. **Resolve it yourself when you can.**

Goal: the round resumes with the cause gone, or the user holds the one question only they can answer. The engine's receipt and the logs it names are the evidence; do not guess past them. Environment causes you act on; code or config causes you fix and commit (the build ships `git archive HEAD`); then `resume`.

**Same root cause twice, or the cause is billing, a contract, or a product decision the user must make — stop and report to the user.** Do not loop.

The paragraph above says commit because the remote build ships `git archive HEAD`. A change left in the
worktree never reaches the build machine, so the next round rebuilds the same code and fails the
same way. `resume` sees the new HEAD and re-verifies every stage — that is what you want after a
code change.

## Close

- Package paths come from the build stage's `DELIVERED` lines. On gather failure, read the WARN path left in the build directory. If neither exists, say you have no path. Do not invent one.
- `close` leaves a delivery record (product name plus the ship commit). `exe-release` step 4 uses it for the same-commit check. **Do not delete it by hand.**
- `close` refuses a round that has not shipped; `abort` drops it and writes no record.

## An interrupted build

An interrupted build keeps running on the build machine. Run the stage `where` names again: `stage run` asks the build machine whether this round (same commit, same product) is still running and attaches to it. Do not `abort` or `init` to restart it: a fresh round wipes the source tree that build is reading.
