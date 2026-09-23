---
name: ui-acceptance
description: Acceptance criteria that start or compare a running product, and what a repository answers so they can run. Use when filling `.mmw/target.json`, writing a story, boundary or journey criterion, reading a DIFF, MISS or JOURNEY line, giving a run its own ports, or before writing an interface ticket's code.
---

# UI acceptance

A **target** is the product a consuming repository runs under automation; the repository answers in `.mmw/` what this skill cannot know. Four **judges**, scripts a `CHECK:` names by bare name, read that answer: the **story judge** (`story-parity.py`, element parity between a product story and its design page), `boundary-check.py`, `journey.py` and `harness-guard.py`. `lease.py` gives each run its own ports and directories.

## Resolve `<scripts>` once

`<scripts>` in every command below is the `scripts/` directory next to this file. Resolve it from this file's own location. The path differs by machine and by host. Other skills that run these scripts take that directory as `--tools <scripts>`; `verify-ticket.py` puts it on the `PATH` of every `CHECK:`, so a criterion names a judge by its bare name.

## Find your moment

| You are | Run or read |
| --- | --- |
| Writing an interface ticket's code, before the first line | the `implement` skill's `references/writing-interface-code.md`, **Before the first line** |
| Building the product's story service and its story adapter (the contract ticket's, and every product component after it) | [references/story-parity.md](references/story-parity.md), **The story page the product serves** |
| Writing the criterion that compares a product story with its design page by element parity, or reading the `DIFF` line one printed | [references/story-parity.md](references/story-parity.md) |
| Writing the four-column boundary test for one screen-contract row, or reading `MISS` / `GREEN WITHOUT INTERACTION` | [references/boundary-check.md](references/boundary-check.md) |
| Writing the criterion that runs one named journey against the real product, or reading `JOURNEY FAILED`, `JOURNEY GREEN WITH BREAK` or `JOURNEY GREEN WITHOUT PRODUCT` | [references/journey.md](references/journey.md) |
| Making a repository an acceptance runtime (it has no `.mmw/target.json`, or a run refused for want of one) | `python3 <scripts>/target_config.py --check` in that repository. Fill `.mmw/target.json` until it exits 0. The reasons behind the fields are [references/product-answers.md](references/product-answers.md) |
| Checking that acceptance names are not scattered through the consuming repository | `python3 <scripts>/harness-guard.py <repository-root>` — [references/harness-guard.md](references/harness-guard.md) |
| Giving a run its own ports and directories, or reading what `lease.py` refused | `python3 <scripts>/lease.py run -- <the start command>`; every refusal names its next step |

## Five rules while the product is running

Several runs share one machine, and each gets its own ports and directories from a lease (`lease.py`). You never choose a port, start a backing service, or work out who holds what: one command — the `start` in `.mmw/target.json`, which `journey.py` runs — brings up everything a journey needs.

1. **Never end a process you did not start.** Stop your own product with the `stop` command its repository declares. Everything else on this machine belongs to another run, and another run's product looks exactly like a stuck one. Your shell refuses `kill`, `pkill`, `killall` and `xargs kill`.
2. **Never start the product outside the lease.** Running the repository's start script yourself, in your own terminal, is how a run ends up on the ports another run is already using. The script refuses without a lease and prints the command that gives it one: `python3 <scripts>/lease.py run -- <the start command>`.
3. **Never complete a human step by hand.** If a run cannot get past something without a person — an authorization in a browser, a click — that is a defect in the automation. Report the ticket blocked: the next run has no person in it.
4. **When the product cannot be reached, report the ticket blocked and stop.** Do not wait, do not build a retry loop, do not change the environment, do not touch another run.
5. **A fault in the pipeline itself is reported blocked the same way.** `verify-ticket.py`, `dispatch.sh`, a judge script (`story-parity.py`, `boundary-check.py`, `journey.py`, `harness-guard.py`), `lease.py`, a hook, `.mmw/target.json` — a fault in one of those is not yours to route around and not a reason to keep trying.

Reporting blocked, in rules 3 to 5, goes through an event, because an event on the ticket is the only thing the relay of the `dispatch` skill wakes anybody for: a plain comment carries none, and a session that ends its turn wakes nobody. Which event depends on your role:

- **A worker** opens a `fault` child, as the `implement` skill says, and stops.
- **A reviewer** never starts the product.
