# Running the criteria

## Resolve `<engine>` once

`<engine>` is `scripts/verify-ticket.py`, resolved from this skill's own `SKILL.md` the way its **Resolve `<engine>` once** section says.

## The two runs that execute a `CHECK:`

```bash
<engine> <n>              # you are the worker, and the code is written
<engine> <n> --reverify   # you are the verifier on this ticket
```

The worker's run takes the criteria not yet met and lands a comment whose first line is `self-run`: each criterion ticked or not, each with the `EVIDENCE:` line gate-check recorded.

`--reverify` reads the ticket, runs every criterion again including the ones already ticked, and comments the outcome of each one on the ticket. Its comment opens `reverify`, and the worker's ticks are re-run rather than trusted.

`verify-ticket.py` reads the ticket and writes one comment. The ticket body, the `CHECK` commands and what a criterion means are yours. A wrong `CHECK` is fixed on the ticket: comment saying what is wrong with it, edit the criterion, run again.

## The verifier's verdict

```bash
<engine> <n> --verdict "<one line>" --model <the model you run on>
```

The verifier runs this after its `--reverify`. It posts one event on the ticket, first line `VERDICT <commit> by <model> — <one line>`: `verifier.passed` when that newest `reverify` comment summarises `ALL MET`, `verifier.failed` otherwise, naming the criteria it left unmet. The commit is `HEAD`, all 40 characters, read by the script. A line that opens `could not start` is a `verifier.failed` whose criteria never ran. Which of the two it is comes from the run, never from the words of the line, so a verdict cannot say more than the run it reports. Exit `0` posted; `2` refused and nothing posted — no `--model`, no `HEAD`, or no `reverify` comment on the ticket for a line that does not open `could not start`.

A `CHECK:` may run ten minutes. A criterion that needs longer says so on the ticket, on a `TIMEOUT: <seconds>` line under its `EVIDENCE:`; every run reads those lines off the ticket body, so the worker's own run and the verifier's `--reverify` are held to the same number. `--timeout <seconds>` raises it for one run. Neither lowers it.

## How many rounds a criterion gets

The worker's own judgement; no run names a limit and `--closeout` counts none. `ABANDON: AC<n> failed` says it ran and did not pass, `ABANDON: AC<n> stuck` says it would not run or cannot be done here, and the reason on that line says what was tried.

## `Outside Owns`

The `self-run` and `reverify` comment ends with the files this ticket's own commits changed that no `## Owns` glob covers: the first-parent chain since the ticket branch left its base commit, merges excluded, so work merged in from another ticket's branch is not counted. A run on any branch but `issue-<n>` — the base branch after `advance`, say — cannot answer that question, and writes `Outside Owns: not checked on <branch>, which carries more than this ticket` instead. Copy that line into the closing comment. It is something to explain there, not a verdict on the work.

## A multi-line `CHECK:`

A `CHECK:` is a shell command. One that needs more than a line carries it in a fenced block directly under `CHECK:`, and nothing inside that block is read as ledger syntax: a `- [ ]` line in a heredoc is text the command prints, not the next criterion. A bare line under a `CHECK:` is refused, and the refusal says to use a fenced block.

## Exit codes

A criterion passes only when its `CHECK` exits `0` **and** its output matches `EXPECT`. Expected text in the output of a failed process is still a failure.

`0` every criterion met, `1` something unmet or abandoned, `2` the ticket could not be read or the run could not start — the reason is on stderr, and nothing is posted.
