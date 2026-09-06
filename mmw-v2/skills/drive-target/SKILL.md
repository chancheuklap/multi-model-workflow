---
name: drive-target
description: Drive a running product for the two judges of an interface, and make a repository drivable. Use when a repository has no `.mmw/target.json` or its product is a kind the judges have not driven before, when a criterion has to launch, reach or observe the product (the wiring check, interface parity, the skeleton of a handoff package), when a `MISS` or `DIFF` line has to be read, or when a run needs its own share of this machine.
---

# Drive target

A **target** is what kind of product the judges drive. The driver here reaches it, puts it into a state, addresses a scene, reads it back, and gives it back; the two judges — the wiring check and interface parity — are two judgements over that one drive. What the driver cannot know on its own, the repository answers in `.mmw/target.json`.

## Resolve `<scripts>` once

`<scripts>` in every command below is the `scripts/` directory next to this file. Resolve it from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from. Other skills that run these scripts take that directory as `--tools <scripts>`; `verify-ticket.py` puts it on the `PATH` of every `CHECK:`, so a criterion names a judge by its bare name.

## Find your moment

| You are | Run or read |
| --- | --- |
| Writing the criterion that checks a control is wired to the backend as its screen-contract row says, or reading the `MISS` line one printed | [references/wiring-check.md](references/wiring-check.md) |
| Writing the criterion that compares an interface against its handoff package, or reading the `DIFF` line one printed | [references/ui-parity.md](references/ui-parity.md) |
| Rendering a handoff package for its row inventory and target trees (the `align-screens` skill sends you here) | `uv run python <scripts>/extract_skeleton.py <handoff dir> <out.json> [--targets <dir> --contract <yaml>]` |
| Making a repository drivable (it has no `.mmw/target.json`, or a run refused for want of one) | `python3 <scripts>/screen_driver.py target --check` in that repository. It prints every field still to answer, one sentence and one example each; fill them and run it again until it exits 0. The reasons behind the fields are [references/targets/README.md](references/targets/README.md) |
| The product is a kind the judges have not driven | [references/targets/README.md](references/targets/README.md), **Adding a kind** |
| Giving a run its own ports and directories, or reading what `lease.py` refused | `python3 <scripts>/lease.py claim | env | run | release | list | count` — the driver claims one before it runs any command `.mmw/target.json` declares; `dispatch.sh` claims one per worktree it starts |

## Five rules while the product is running

Several runs share one machine, and each gets its own ports and directories from a lease ([references/targets/README.md](references/targets/README.md), **instance**). You never choose a port, start a backing service, or work out who holds what: one command — the `start` in `.mmw/target.json`, which the driver runs for you — brings up everything your criteria need.

1. **Never end a process you did not start.** Stop your own product with the `stop` command its repository declares. Everything else on this machine belongs to another run, and another run's product looks exactly like a stuck one. Your shell refuses `kill`, `pkill`, `killall` and `xargs kill` for this reason (`scripts/hook.py`, registered in every host by `install.sh`).
2. **Never start the product outside the lease.** Running the repository's start script yourself, in your own terminal, is how a run ends up on the ports another run is already using. The script refuses without a lease and prints the command that gives it one: `python3 <scripts>/lease.py run -- <the start command>`.
3. **Never complete a human step by hand.** If a run cannot get past something without a person — an authorization in a browser, a click — that is a defect in the automation. Report it. Satisfying it makes a broken automation look healthy, and the next run has no person in it.
4. **When the product cannot be reached, report the ticket blocked and stop.** Do not wait, do not build a retry loop, do not change the environment, do not touch another run.
5. **A fault in the pipeline itself is reported blocked the same way.** The driver, the lease, a machine fact in `.mmw/target.json` — a fault in one of those is not yours to route around and not a reason to keep trying. A workaround built instead hides it from every ticket after yours.

Reporting blocked is one comment on the ticket saying exactly what you ran and what you saw, and then stopping. Stopping is what brings it to the main agent, who fixes the cause.
