---
name: ui-acceptance
description: Make a repository an automatable acceptance runtime — three judges (story, boundary, journey) and the lease, start/stop and harness they need. Use when filling `.mmw/target.json`, writing a story, boundary or journey criterion, reading a DIFF, MISS or JOURNEY line, or giving a run its own ports. Also: before writing an interface ticket's code, take the design side's values.
---

# UI acceptance

A **target** is the product a consuming repository runs under automation. What this skill cannot know on its own, the repository answers in `.mmw/`. Three judges use that answer, and the lease, `start` / `stop` / `discover` and harness guard are the runtime they need: the story judge starts the product's `stories` command, renders the design side offline, and compares both by `data-ui` id (element parity); the boundary check runs the product's own four-column boundary test twice, the second time without the click; a journey starts the real product, runs one Playwright script, and on a second pass breaks one named interface.

## Resolve `<scripts>` once

`<scripts>` in every command below is the `scripts/` directory next to this file. Resolve it from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from. Other skills that run these scripts take that directory as `--tools <scripts>`; `verify-ticket.py` puts it on the `PATH` of every `CHECK:`, so a criterion names a judge by its bare name.

## Find your moment

| You are | Run or read |
| --- | --- |
| Writing an interface ticket's code, before the first line: the design side's values | [references/story-parity.md](references/story-parity.md), **`--render-only`** |
| Building the product's story page service and its scene adapter (the contract ticket's, and every surface component after it) | [references/story-parity.md](references/story-parity.md), **The story page the product serves** |
| Writing the criterion that compares a product story with its design page by element parity, or reading the `DIFF` line one printed | [references/story-parity.md](references/story-parity.md) |
| Writing the four-column boundary test for one screen-contract row, or reading `MISS` / `GREEN WITHOUT INTERACTION` | [references/boundary-check.md](references/boundary-check.md) |
| Writing the criterion that runs one named journey against the real product, or reading `JOURNEY FAILED`, `JOURNEY GREEN WITH BREAK` or `JOURNEY GREEN WITHOUT PRODUCT` | [references/journey.md](references/journey.md); [references/product-answers.md](references/product-answers.md) names `start`, `stop`, `discover` and the journeys directory |
| Making a repository drivable (it has no `.mmw/target.json`, or a run refused for want of one) | `python3 <scripts>/target_config.py --check` in that repository. It prints every field still to answer, one sentence and one example each; fill them and run it again until it exits 0. The reasons behind the fields are [references/product-answers.md](references/product-answers.md) |
| Checking that acceptance names are not scattered through the consuming repository | `python3 <scripts>/harness-guard.py <repository-root>` — [references/harness-guard.md](references/harness-guard.md) |
| Giving a run its own ports and directories, or reading what `lease.py` refused | Run `python3 <scripts>/lease.py claim \| env \| run \| release \| list \| count \| remove-instance`. `claim` exits 4 when no slot may be taken. `release` exits 0 when it gives one back, 3 when none exists, and 2 when `--stop` cannot read `.mmw/target.json`. Its lifecycle and two limits are in [references/product-answers.md](references/product-answers.md) under **`instance`** |

## Five rules while the product is running

Several runs share one machine, and each gets its own ports and directories from a lease ([references/product-answers.md](references/product-answers.md), **instance**). You never choose a port, start a backing service, or work out who holds what: one command — the `start` in `.mmw/target.json`, which `journey.py` runs — brings up everything a journey needs.

1. **Never end a process you did not start.** Stop your own product with the `stop` command its repository declares. Everything else on this machine belongs to another run, and another run's product looks exactly like a stuck one. Your shell refuses `kill`, `pkill`, `killall` and `xargs kill` for this reason (the `dispatch` skill's `scripts/tool-guard.py`, registered in every host by `install.sh`).
2. **Never start the product outside the lease.** Running the repository's start script yourself, in your own terminal, is how a run ends up on the ports another run is already using. The script refuses without a lease and prints the command that gives it one: `python3 <scripts>/lease.py run -- <the start command>`.
3. **Never complete a human step by hand.** If a run cannot get past something without a person — an authorization in a browser, a click — that is a defect in the automation. Report the ticket blocked. Satisfying it makes a broken automation look healthy, and the next run has no person in it.
4. **When the product cannot be reached, report the ticket blocked and stop.** Do not wait, do not build a retry loop, do not change the environment, do not touch another run.
5. **A fault in the pipeline itself is reported blocked the same way.** The driver, the lease, a machine fact in `.mmw/target.json` — a fault in one of those is not yours to route around and not a reason to keep trying. A workaround built instead hides it from every ticket after yours.

Reporting blocked, in rules 3 to 5, goes through an event, because an event on the ticket is the only thing the relay of the `dispatch` skill wakes anybody for: a plain comment carries none, and a session that ends its turn wakes nobody. Which event depends on your role:

- **A worker** runs the `verify-ticket` skill's `--sub-issue fault <file>`, the file's body being exactly what you ran and what you saw, then stops. Its `child.opened` event, of kind `fault`, wakes the main agent, who fixes the cause.
- **A reviewer** never starts the product.
