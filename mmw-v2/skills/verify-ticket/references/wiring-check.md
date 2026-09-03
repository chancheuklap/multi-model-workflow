# Wiring check

Whether a control on the running interface does what its screen-contract row says is `scripts/wiring-check.py`, next to this skill's `SKILL.md`. It puts the real backend into the row's `reach` state, opens the row's `route` on the application's own debugging port, triggers the control by role and accessible name, and reads the row's `observe` operations on the backend. The renderer is never asked anything: a control is wired when the backend can see the effect.

Interface parity ([ui-parity.md](ui-parity.md)) is the other half: it judges what the screen shows. The two run against the same application and the same backend, and a ticket that owns screen-contract rows carries both.

## What decides a row

Each `observe` line is `METHOD /path -> <expression>`. The script calls the operation, substitutes `{project_id}` and other placeholders from what earlier calls returned or the seed printed, and evaluates the expression against the JSON body with a small jq-like grammar: `.field`, `.list[0].field`, `==`, `!=`, `contains`, `exists`. Every line true is the row passed. A trigger it cannot find by role and name fails the row with `no control`, and so does an `observe` operation the backend answers with a non-2xx status.

Before every row the page is reloaded, so state a person left in the window is gone; after every row the window is returned to the address it was on.

## The seed

`--seed <command>` runs once before the rows, in the repository root, and its stdout is read as `KEY=VALUE` lines the placeholders can use (`project_id=…`). The command is the repository's own seed script for the `reach` state the rows share — the one the spec's mechanism registry names — never a mock of the backend. A criterion whose rows need different states is two criteria.

## The criterion, in one shape

Written onto the ticket, run by a shell months later with no model between; the path is literal and is the install location `install.sh` creates on every machine:

```
CHECK: uv run ~/.agents/skills/verify-ticket/scripts/wiring-check.py --contract docs/specs/<effort>/screen-contract.yaml --rows <id,id> --cdp <debugging port url> --impl <url> --backend <url> --seed "<seed command>"
EXPECT: WIRING OK <passed>/<total>
```

`--impl-title` picks the window when the application has more than one. The application and its backend must be running when the criterion runs and are left running afterwards.

## Reading what it printed

- `0`, one line `WIRING OK <passed>/<total>`: every row's `observe` held.
- `1`: one `MISS <row id> — <reason>` line per failing row: `no control <role> "<name>"`, `<operation> answered <status>`, or `<expression> was <value>`.
- `2`: the run could not start — no application on `--cdp`, no backend on `--backend`, the seed exited non-zero, a row id not in the contract, a row without `observe`.

What to fix is what the line names. A `no control` line is the accessible name: compare the running interface's tree with the row's `trigger` before touching anything else.
