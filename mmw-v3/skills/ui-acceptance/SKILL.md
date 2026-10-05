---
name: ui-acceptance
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# UI acceptance

The **product under test** (the product, for short) is the application a consuming repository runs under automation; the repository answers in `.mmw/` what this skill cannot know. `lease.py` gives each ticket worktree its own ports and directories. `design_render.py` renders a design package's pages offline, for the `design-pages` skill's pull and the `write-screen-contract` skill's skeleton.

<!--
Shell. The four oracles (the story oracle story-parity.py, boundary-check.py, journey.py,
harness-guard.py), target_config.py, the rest of this skill's opening, its
`## Find your moment` table and its references come here. Source in MMW v2 at 9df1ab67d:
mmw-v2/skills/ui-acceptance/. A lesson that brings in UI acceptance writes them. Until
then a `CHECK:` that names an oracle is refused by the verify-ticket skill's
verify-ticket.py before anything runs.
-->

## Five rules while the product is running

Several runs share one machine, and each gets its own ports and directories from a lease (`lease.py`). You never choose a port, start a backing service, or work out who holds what: one command — the `start` in `.mmw/target.json` — brings up everything a journey needs.

1. **Never end a process you did not start.** Stop your own product with the `stop` command its repository declares. Everything else on this machine belongs to another run, and another run's product looks exactly like a stuck one. Your shell refuses `kill`, `pkill`, `killall` and `xargs kill`.
2. **Never start the product outside the lease.** Running the repository's start script yourself, in your own terminal, is how a run ends up on the ports another run is already using. The script refuses without a lease and prints the command that gives it one: `python3 scripts/lease.py run -- <the start command>`.
3. **Never complete a human step by hand.** If a run cannot get past something without a person — an authorization in a browser, a click — that is a defect in the automation. Report the ticket blocked: satisfying it makes a broken automation look healthy, and the next run has no person in it.
4. **When the product cannot be reached, report the ticket blocked and stop.** Do not wait, do not build a retry loop, do not change the environment, do not touch another run.
5. **A fault in the pipeline itself is reported blocked the same way.** `verify-ticket.py`, `dispatch.sh`, an oracle script, `lease.py`, a hook, `.mmw/target.json` — a fault in one of those is not yours to route around and not a reason to keep trying. A workaround built instead hides it from every ticket after yours.

Reporting blocked, in rules 3 to 5, goes through an event, because an event on the ticket is the only thing the relay of the `dispatch` skill wakes anybody for: a plain comment carries none, and a session that ends its turn wakes nobody. A worker opens a `fault` child, as the `verify-ticket` skill's `references/sub-issues.md` says, and stops.
