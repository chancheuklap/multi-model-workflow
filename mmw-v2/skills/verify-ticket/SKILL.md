---
name: verify-ticket
description: Run one ticket's acceptance criteria, and close the ticket when they pass. Use to claim a ticket before starting work on it, to run its criteria after writing code, to re-run them as its verifier, to close it out from a written draft, to lint a batch of tickets before publishing them, or to write or read the criterion that compares an interface against its handoff package.
---

# Verify ticket

Each acceptance criterion on a ticket carries a `CHECK:` command and the `EXPECT:` string a passing run prints. This skill runs them and comments the outcome on the ticket.

The ticket is the only state. Every run reads it fresh, writes at most one comment, and carries nothing to the next run.

## Resolve `<engine>` once

`<engine>` in every command below is `scripts/verify-ticket.py`, next to this file, and means:

```bash
python3 <absolute path to that script>
```

Resolve it from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from.

## Find your run

| You are | Run | What lands on the ticket |
| --- | --- | --- |
| A **worker** about to touch ticket `<n>` | `<engine> <n> --preflight` | The ticket assigned to you. If it is not yours to start: a `NOT_READY: <reason>` comment instead, exit 2, and you stop — the reason is already on the ticket, so there is nothing to report twice |
| A **worker** who has finished writing code | `<engine> <n>` | A comment whose first line is `self-run`: each criterion ticked or not, each with the `EVIDENCE:` line gate-check recorded |
| The **verifier** on ticket `<n>` | `<engine> <n> --reverify` | A comment whose first line is `reverify`: every criterion run again, the ones the worker's `self-run` ticked included, instead of trusted |
| A **worker** whose closing comment is written to a file | `<engine> <n> --closeout <draft>` | The draft posted, `ready-for-agent` taken off, and the ticket closed. A draft whose first line is `HANDOFF REQUIRED` posts and swaps `ready-for-agent` for `needs-triage`, leaving the ticket open to be judged fresh |
| A **worker** posting the decisions comment | `<engine> <n> --decisions <file>` | A comment whose first line is `DECISIONS`. If the ticket already has one, or the file is missing a section: exit 2, the reason on stderr, nothing posted |
| A **worker** telling the tickets whose files moved | `<engine> <n> --touched` | A `TOUCHED BY #<n>` comment on each open sibling whose `## Owns` covers a file on the newest `self-run`'s `Outside Owns:` line. If there is no `REVIEW` comment: exit 2. If that line is `None`: nothing posted, exit 0 |
| A **worker** assembling the closing-comment skeleton | `<engine> <n> --draft <out-file>` | Nothing on the ticket. The skeleton is written to `<out-file>`, with `skipped:` and `Decisions I made on my own` left as `<fill>`. `--closeout` refuses it until those are filled |
| A **worker** opening a sub-issue under this ticket | `<engine> <n> --sub-issue <kind> <file>` | A new issue labelled `needs-triage`, parented to this ticket, first line `SUB-ISSUE <kind> from #<n>`. `kind` is `baseline`, `outside-owns`, `review`, `decision`, or `pipeline`. Empty file or unknown kind: exit 2 |
| The **agent publishing a batch**, at the read-back step | `<engine> <n> --lint` | Nothing. Findings print to your terminal; no `CHECK:` runs and no comment is posted |

Exit code: `0` every criterion met, `1` something unmet or abandoned, `2` the ticket could not be read or the run could not start. `--preflight`, `--decisions`, `--touched` and `--sub-issue` use `2` for a refusal; `--closeout` uses `1`.

A `CHECK:` may run ten minutes. A criterion that needs longer says so on the ticket, on a `TIMEOUT: <seconds>` line under its `EVIDENCE:`; every run reads those lines off the ticket body, so the worker's own run and the verifier's `--reverify` are held to the same number. `--timeout <seconds>` raises it for one run. Neither lowers it.

## What `verify-ticket.py` decides

A criterion passes only when its `CHECK` exits `0` **and** its output matches `EXPECT`. Expected text in the output of a failed process is still a failure.

`verify-ticket.py` reads the ticket and writes one comment. The ticket body, the `CHECK` commands and what a criterion means are yours. A wrong `CHECK` is fixed on the ticket: comment saying what is wrong with it, edit the criterion, run again. The `VERDICT` line is the verifier's own comment, written after `--reverify`, not something `verify-ticket.py` emits.

## How many rounds a criterion gets

The worker's own judgement; no run names a limit and `--closeout` counts none. `ABANDON: AC<n> failed` says it ran and did not pass, `ABANDON: AC<n> stuck` says it would not run or cannot be done here, and the reason on that line says what was tried.

## `Outside Owns`

The `self-run` and `reverify` comment ends with the files this ticket's own commits changed that no `## Owns` glob covers: the first-parent chain since the ticket branch left its base commit, merges excluded, so work merged in from another ticket's branch is not counted. A run on any branch but `issue-<n>` — the base branch after `advance`, say — cannot answer that question, and writes `Outside Owns: not checked on <branch>, which carries more than this ticket` instead. Copy that line into the closing comment. It is something to explain there, not a verdict on the work.

## A multi-line `CHECK:`

A `CHECK:` is a shell command. One that needs more than a line carries it in a fenced block directly under `CHECK:`, and nothing inside that block is read as ledger syntax: a `- [ ]` line in a heredoc is text the command prints, not the next criterion. A bare line under a `CHECK:` is refused, and the refusal says to use a fenced block.

## `--lint` on a batch

Three things at once: how the criteria are written, which worker the ticket asks for, and whether the batch under the same spec is a startable graph — every ticket the spec lists as a sub-issue, the blocking links between them, and which of them nothing blocks. The graph comes from the tracker's blocking links, the same ones `--preflight` refuses on and `board.py` dispatches from. A ticket's `## Blocked by` section is the human-readable copy of those links, and a mismatch is a `WARN  … [blocked-by-mismatch]` naming the numbers each side has that the other does not.

The worker reads the same way. `dispatch.sh` starts a ticket on the `models.md` row its `junior-worker` or `senior-worker` label names, so a ticket in the agent queue wearing no such label is an `ERROR  … [worker-label]`, and so is one wearing both. Its `## Worker` section is the human-readable copy, and a section that is missing or names the other one is a `WARN  … [worker-mismatch]`.

The batch converges when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose.

## Five rules while the product is running

Several runs share one machine, and each gets its own ports and directories from a lease
(`references/targets/README.md`, question 8). You never choose a port, start a backing
service, or work out who holds what: one command — the `start` in `.mmw/target.json`,
which the driver runs for you — brings up everything your criteria need.

1. **Never end a process you did not start.** Stop your own product with the `stop`
   command its repository declares. Everything else on this machine belongs to another
   run, and another run's product looks exactly like a stuck one. Your shell refuses
   `kill`, `pkill`, `killall` and `xargs kill` for this reason.
2. **Never start the product outside the lease.** Running the repository's start script
   yourself, in your own terminal, is how a run ends up on the ports another run is
   already using. The script refuses without a lease and prints the command that gives
   it one.
3. **Never complete a human step by hand.** If a run cannot get past something without a
   person — an authorization in a browser, a click — that is a defect in the automation.
   Report it. Satisfying it makes a broken automation look healthy, and the next run has
   no person in it.
4. **When the product cannot be reached, report the ticket blocked and stop.** Do not
   wait, do not build a retry loop, do not change the environment, do not touch another
   run.
5. **A fault in the pipeline itself is reported blocked the same way.** The acceptance
   driver, the instance lease, the `verify-ticket` scripts, a machine fact in
   `.mmw/target.json` — a fault in one of those is not yours to route around and not a
   reason to keep trying. A workaround built instead hides it from every ticket after
   yours.

Reporting blocked is one comment on the ticket saying exactly what you ran and what you
saw, and then stopping. Stopping is what brings it to the main agent, who fixes the
cause.

## Reached from here

- **`--closeout` refused your draft** → [references/closeout.md](references/closeout.md), the conditions it reads the draft against. The refusal itself is on stderr: the first line counts the problems, names the first, and gives the `--check-only` command that prints them all; every problem after the first is one more line opening `also:`. Go to the reference file when a line names a condition you cannot place. `--closeout <draft> --check-only` reports on a draft and changes nothing, at any time.
- **You are writing the criterion that checks a control is wired to the backend as its screen-contract row says, or reading the `MISS` line one printed** → [references/wiring-check.md](references/wiring-check.md). Its one fixed shape names the contract and the rows and nothing about the machine; the row's `observe` lines are what it asserts, through the target's read surface, and `--negative` is how it proves it can fail.
- **You are writing the criterion that compares an interface against its handoff package, or reading the `DIFF` line one printed** → [references/ui-parity.md](references/ui-parity.md). It carries that criterion's one fixed shape, path and all, to copy onto the ticket — the contract and the `data-screen` values the ticket owns — and the three exit codes and reasons a parity run prints. A `CHECK` that runs `visual-parity.py` prints one `DIFF` line and nothing that explains it; that reference file is where the line is read.
- **The product is of a kind the two judges have not driven before, or the repository has to say how its product is reached (`.mmw/target.json`)** → [references/targets/README.md](references/targets/README.md): the nine questions every target answers, and the three kinds answered so far.
