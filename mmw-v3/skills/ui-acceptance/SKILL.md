---
name: ui-acceptance
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# UI acceptance

The **product under test** (the product, for short) is the application a consuming repository runs under automation; the repository answers in `.mmw/` what this skill cannot know. Four **oracles**, scripts a `CHECK:` names by bare name, read that answer: the **story oracle** (`story-parity.py`, element parity between a product story and its design page), `boundary-check.py`, `journey.py` and `harness-guard.py`. `lease.py` gives each ticket worktree its own ports and directories. `design_render.py` renders a design package's pages offline, for the story oracle, the `design-pages` skill's pull and the `write-screen-contract` skill's skeleton.

During a night these oracles are the only eyes on a UI: when every criterion is green, the ticket closes and the code lands with no person looking at the screen. So write the story, the test, the journey and the harness so that green can only mean the product is right; when an oracle is red, change the product, or open a child when the design or the screen contract is wrong, never the check.

A criterion names an oracle bare; run one by hand as `scripts/<name>`.

## What each file covers

| File | What it covers |
| --- | --- |
| [references/writing-interface-code.md](references/writing-interface-code.md) | Writing a page ticket's code, from **Before the first line** on |
| [references/story-parity.md](references/story-parity.md) | The story page the product serves (its story service and story adapter, built by the contract ticket and every product component after it); how the story oracle compares a product story with its design page by element parity; the `DIFF` line it prints |
| the `mmw-mode` skill's `references/cutting-interface-tickets.md`, **Criterion shapes** | Writing a story, boundary, journey or harness guard criterion onto a ticket |
| [references/boundary-check.md](references/boundary-check.md) | The four-column boundary test for one screen-contract row; `MISS` and `GREEN WITHOUT INTERACTION` |
| [references/journey.md](references/journey.md) | A journey script and the product's fault-injection switch; `JOURNEY FAILED`, `JOURNEY GREEN WITH BREAK` and `JOURNEY GREEN WITHOUT PRODUCT` |
| [references/product-answers.md](references/product-answers.md) | The reasons behind each field of `.mmw/target.json`. `python3 scripts/target_config.py --check` in the repository says what is missing; fill the file until it exits 0 |
| [references/harness-guard.md](references/harness-guard.md) | `python3 scripts/harness-guard.py <repository-root>`, which checks that acceptance names are not scattered through the consuming repository; `HARNESS LEAK` and `HARNESS DESIGN PAGE` |
| `scripts/lease.py` | `python3 scripts/lease.py run -- <the start command>` gives a run its own ports and directories; every refusal names its next step |

## Five rules while the product is running

Several runs share one machine, and each gets its own ports and directories from a lease (`lease.py`). You never choose a port, start a backing service, or work out who holds what: one command — the `start` in `.mmw/target.json`, which `journey.py` runs — brings up everything a journey needs.

1. **Never end a process you did not start.** Stop your own product with the `stop` command its repository declares. Everything else on this machine belongs to another run, and another run's product looks exactly like a stuck one. Your shell refuses `kill`, `pkill`, `killall` and `xargs kill`.
2. **Never start the product outside the lease.** Running the repository's start script yourself, in your own terminal, is how a run ends up on the ports another run is already using. The script refuses without a lease and prints the command that gives it one: `python3 scripts/lease.py run -- <the start command>`.
3. **Never complete a human step by hand.** If a run cannot get past something without a person — an authorization in a browser, a click — that is a defect in the automation. Report the ticket blocked: satisfying it makes a broken automation look healthy, and the next run has no person in it.
4. **When the product cannot be reached, report the ticket blocked and stop.** Do not wait, do not build a retry loop, do not change the environment, do not touch another run.
5. **A fault in the pipeline itself is reported blocked the same way.** `verify-ticket.py`, `dispatch.sh`, an oracle script, `lease.py`, a hook, `.mmw/target.json` — a fault in one of those is not yours to route around and not a reason to keep trying. A workaround built instead hides it from every ticket after yours.

Reporting blocked, in rules 3 to 5, goes through an event, because an event on the ticket is the only thing the relay of the `dispatch` skill wakes anybody for: a plain comment carries none, and a session that ends its turn wakes nobody. A worker opens a `fault` child, as the `verify-ticket` skill's `references/sub-issues.md` says, and stops.
