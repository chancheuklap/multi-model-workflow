# Orchestrator wakes

**Handle each wake** in **Run a night** and in **Land one ticket** sends you here: find the row of what woke you, or of each row `status` printed, and do what your column says.

`Same` means: do what the Night orchestrator cell says, reading `events.py fold <n>` where it says `status`.

`n/a` marks a row that only `advance` produces, and no `advance` collects a ticket outside a night.

Commands of this skill's `bash scripts/dispatch.sh` and `python3 scripts/events.py` are named bare below.

## What you see

| What you see | Night orchestrator | One-ticket orchestrator |
| --- | --- | --- |
| `ticket.passed`, or a `ready` frontier row | The `advance` in **Handle each wake** handles it | `ticket.passed` goes to **Land**; a `ready` frontier row is `n/a` |
| A live worker should continue | `bash scripts/dispatch.sh resume <n> "<what you settled, then: continue>"`; act on exit 0, 4, 3 or 2 as **Exit codes of `resume`** below says | Same |
| `child.opened` of kind `fault` | Read `events.py fold <n>`. A `fault` in this repository's environment (a credential, a service, `.mmw/target.json`) you fix, then `bash scripts/dispatch.sh resume <n> "… continue"`. A `fault` in the pipeline's own scripts you do not patch while they run the night: tell the user what failed, and suspend when the rest of the batch would hit it too | A `fault` stopped the worker: fix what the child names, then `bash scripts/dispatch.sh resume <n> "<what you fixed>, then: continue"` |
| `child.opened` of kind `contract` | Read the child and the authority it cites. Apply the authority order in `#### Contract children` in **Run a night**; then either correct the source the child names and every unlanded derived ticket, close the child and resume its worker, or move the affected not-yet-started tickets to `needs-triage` and leave the child open | Same |
| `child.opened` of kind `contract` naming a Claude Design page | The design package is written only by the `design-pages` skill's `references/pull.md`, so there is nothing to correct in this night. Move the affected not-yet-started tickets to `needs-triage`, comment on the child with the pages it names, the ticket numbers moved, and that it needs a session whose host has the Claude Design MCP tools, and leave it open for the user. That session finishes the child as `#### A contract child answered by a pull` in **Design a UI** says | Same |
| `child.opened` of kind `decision` | Nothing; the worker took the default | Same |
| `ticket.returned` | Leave its workspace for triage; the `advance` in **Handle each wake** continues the batch | **Land** |
| The `advance` summary has `bounced` | After the second bounce the ticket stays in `needs-triage` | n/a |
| `ticket.refused` | Fix the event's `reason`; the `advance` in **Handle each wake** starts it if the frontier permits | The worker refused to claim the ticket, and the event's `reason` says why. Fix that, then `bash scripts/dispatch.sh start <n> worker` again. |
| `worker.lost` | The `advance` in **Handle each wake** gives back the claim and starts another worker in the standing workspace | The worker's session stopped. `bash scripts/dispatch.sh start <n> worker` starts another in the same workspace; it first commits tracked edits and pushes the ticket branch to origin. |
| `relay.recovered since <time>` | Nothing; later wakes carry the recovered events | Same |
| A worker whose session is gone while its worktree, slot or claim still stand (`advance` says "if the worker … is gone, retract it") | `bash scripts/dispatch.sh retract <n>`; a `0` on its summary line is something it could not release, and the line above says why. The `advance` in **Handle each wake** starts the replacement | n/a |
| `watchdog: relay down (…)` | `advance <spec>` starts the relay again for the recorded orchestrator | `open-ticket-watch <n>` starts the relay again |
| `watchdog: relay not reading (…)` | Nothing while it clears: the relay recovers with its first read that works, and opening the night again replaces nothing. When it repeats without clearing, tell the user the relay cannot read the tracker | Same |
| `watchdog: #<n> events unreadable` | Leave the alert as a comment on #<n> for the user | Same |
| `watchdog: #<n> is held with no session to ask, silent since <time>` | Read `status`; when nothing works the ticket, `retract <n>` | Read `events.py fold <n>`; when nothing works the ticket, `retract <n>`, then `start <n> worker` |
| `watchdog: #<n> liveness unknown: <runner> could not say whether the <kind> session <session> is alive` | Send the `resume` the alert names, and act on its exit as **Exit codes of `resume`** says | Same |
| `watchdog: #<n> liveness unknown: the <kind> session <session> was started on <machine>, not on <this machine>` | As for the row above | Same |
| `watchdog: #<n> silent since <time> with nothing to wait on` | When `events.py fold <n>` lists an open `contract` child, the worker is waiting on you; settle that child first. Otherwise send the `resume` the alert names, and act on its exit as **Exit codes of `resume`** says | Same |
| `watchdog: cannot read the tracker since <time>: …` | Run `gh issue view` on the ticket the alert names; wait for the tracker or the network to recover, and leave credential repair to the user | Same |
| An `MMW turn guard:` line | Do what the line says: run the `watchdog.py arm` command it names, act on what that prints, and when it exits non-zero open a `fault` child on a held ticket with that command and its output; the line is not acked | Same |
| Any other live worker | Nothing; its result wakes you or its worker | n/a |
| The ticket needs the other worker grade | Give it exactly one of the `junior-worker` / `senior-worker` labels; the next `start` reads it | n/a |

## Exit codes of `resume`

- Exit 0: the worker took the message and a turn started on it; its result wakes you, and `worker.resumed` is on the ticket unless stderr says it was not written.
- Exit 4: do what stderr says; the text is in the session, so do not send it again.
- Exit 3: do what stderr says.
- Exit 2: nothing was sent, and stderr names why and what to run. When stderr says the worker is not on its runner any more, run `bash scripts/dispatch.sh retract <n>`, then `bash scripts/dispatch.sh advance <spec>` inside a night or `bash scripts/dispatch.sh start <n> worker` outside one; when `retract` cannot tell whether the session stopped, tell the user.

When you run `resume` again after exit 3, word it so a worker that receives both messages reads them as one instruction. A worker that `start <n> worker` puts in place of the old one has none of the instructions given only inside the old session; send them again with `resume`.
