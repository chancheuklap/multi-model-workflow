# Running the criteria

## Resolve `<engine>` once

`<engine>` is `scripts/verify-ticket.py`, resolved from this skill's own `SKILL.md` the way its **Resolve `<engine>` once** section says.

## The two runs that execute a `CHECK:`

```bash
<engine> <n>              # you are the worker, and the code is written
<engine> <n> --reverify   # you are the verifier on this ticket
```

Each run lands one `ticket.checked` event on the ticket. Its first line names the run and the commit it ran on and repeats gate-check's summary line; under it is the ledger as the run left it — each criterion ticked or not, each with the `EVIDENCE:` line gate-check recorded. What programs read is the event block: `run` (`self` for the worker's run, `reverify` for the verifier's), the full commit, the `result` (`met`, `unmet` or `handoff`), the counts, each criterion's outcome, the ids left unmet, and a fingerprint of the criteria it ran.

The worker's run takes the criteria not yet met. `--reverify` reads the ticket and runs every criterion again, including the ones the newest run ticked, so the worker's ticks are re-run rather than trusted. The main agent re-runs a landed ticket on the base branch the same way with `--reverify --actor main` (the `dispatch` skill's `reverify` does it), and that run's event names the main agent as its writer.

`verify-ticket.py` reads the ticket and writes its events. The ticket body, the `CHECK` commands and what a criterion means are yours. A wrong `CHECK` is fixed on the ticket: comment saying what is wrong with it, edit the criterion, run again.

## A criterion that runs the product

Before running a `CHECK:` that names `journey.py`, `screen_driver.py` or `lease.py`, this run asks the `drive-target` skill's `lease.py` for the worktree's product slot. A `CHECK:` naming `story-parity.py` asks for none: the story page service it starts has no backend behind it and takes a port the machine hands out. The slot is in that run's `ticket.checked` event. Its lifecycle and limits are in that skill's `references/runtime-environment.md` under **`instance`**.

When no product slot is free, the run posts one `worker.queued` event and runs nothing; the ticket gets no second `worker.queued` for the same wait. What happens next depends on whose run it is.

The worker's own run exits `3` at once. End your turn. A slot comes back only when another ticket's work ends, and at that moment the relay of the `dispatch` skill wakes you with `#<n> worker.queued`. Run the same command again, then acknowledge that wake with the `dispatch` skill's `ack <n> worker.queued`. A run that finds every slot still held exits `3` again, and you are woken again when the next slot is given back.

The verifier's `--reverify`, and the main agent's `--reverify --actor main`, wait inside the command instead: they ask again every 10 seconds, and after 90 seconds exit `3` having run nothing. Run the same command again to keep waiting. `MMW_SLOT_WAIT_S` and `MMW_SLOT_BEAT_S` change the two numbers.

## The verifier's verdict

```bash
<engine> <n> --verdict "<one line>" --model <the model field of the ticket's newest verifier.started event>
```

The verifier runs this after its `--reverify`. It posts one event on the ticket, first line `VERDICT <commit> by <model> — <one line>`: `verifier.passed` when the newest reverify `ticket.checked` has the result `met`, `verifier.failed` otherwise, naming the criteria it left unmet. The commit is `HEAD`, all 40 characters, read by the script, and that reverify must be a run of it: a newest reverify on an older commit is refused, and `--reverify` on this commit comes first. A line that opens `could not start` is a `verifier.failed` whose criteria never ran. Which of the two it is comes from the run, never from the words of the line, so a verdict cannot say more than the run it reports. Exit `0` posted; `2` refused and nothing posted — no `--model`, no `HEAD`, or no reverify `ticket.checked` of `HEAD` on the ticket for a line that does not open `could not start`.

A `CHECK:` may run ten minutes. A criterion that needs longer says so on the ticket, on a `TIMEOUT: <seconds>` line under its `EVIDENCE:`; every run reads those lines off the ticket body, so the worker's own run and the verifier's `--reverify` are held to the same number. `--timeout <seconds>` raises it for one run. Neither lowers it.

## How many rounds a criterion gets

The worker's own judgement; no run names a limit and `--closeout` counts none. `ABANDON: AC<n> failed` says it ran and did not pass, `ABANDON: AC<n> stuck` says it would not run or cannot be done here, and the reason on that line says what was tried.

## `Outside Owns`

The worker's run also records the files this ticket's own commits changed that no `## Owns` glob covers: the first-parent chain since the ticket branch left its base commit, merges excluded, so work merged in from another ticket's branch is not counted. The list is in its `ticket.checked` event, and its comment ends with the same list as an `Outside Owns:` line. A run on any branch but `issue-<n>` cannot answer that question, and writes `Outside Owns: not checked on <branch>, which carries more than this ticket` instead. Copy that line into the closing comment. It is something to explain there, not a verdict on the work.

## A multi-line `CHECK:`

A `CHECK:` is a shell command. One that needs more than a line carries it in a fenced block directly under `CHECK:`, and nothing inside that block is read as ledger syntax: a `- [ ]` line in a heredoc is text the command prints, not the next criterion. A bare line under a `CHECK:` is refused, and the refusal says to use a fenced block.

## Exit codes

A criterion passes only when its `CHECK` exits `0` **and** its output matches `EXPECT`. Expected text in the output of a failed process is still a failure.

`0` every criterion met, `1` something unmet or abandoned, `2` the ticket could not be read or the run could not start — no readable `HEAD`, no `lease.py` for a criterion that runs the product, an unreadable `.mmw/target.json` — the reason is on stderr, and nothing is posted. `3` no product slot was free: follow **A criterion that runs the product** above. `4` the criteria ran and the `ticket.checked` recording them could not be written: the ticket records no run, so treat it as a run that did not happen and run it again.
