# Wiring check

Whether a control on the running interface does what its screen-contract row says is `scripts/wiring-check.py`, next to this skill's `SKILL.md`. For each row it takes the scene the row's `drive.scene` names, else the first scene of the contract the row is visible in, puts the product into that scene — its `reach` through the repository's reach script, its `route`, a reload, its `open` chain — then the row's own `drive.reach` and `drive.open` (the typing and picking that make a control actionable when no scene shows it so), triggers the control by role and accessible name, and reads the row's `observe` lines through the target's read surface. A control inside a dialog is reached the way its scene is; a row on no declared scene is driven on its own `reach` and `route`. The renderer is never asked anything.

Interface parity ([ui-parity.md](ui-parity.md)) is the other half: it judges what the screen shows. The two run over one driver against the same product, and a ticket that owns screen-contract rows carries both.

## What decides a row

Each `observe` line is one read that is held to one principle:

> A fresh read of persistent state, on a path the acting view did not produce, issued after the action completed.

On a target with a JSON read surface the line is `METHOD /path -> <expression>`: the script calls the operation, substitutes `{project_id}` and other placeholders from what the reach script printed, and evaluates the expression against the JSON body. A small built-in grammar covers `.field`, `.list[0].field`, `==`, `!=`, `contains`, `exists`; anything else is a jq program run by the `jq` on PATH, with every `KEY=VALUE` the reach script printed bound as `$KEY`, plus `$typed` (what the last `open` step typed) and `$typed_<field>` (per row, named by the row id's last segment, `-` as `_`). A `$variable` nothing supplies stops the run and names itself: it is a contract defect, not a miss. On a server-rendered page with no JSON surface the line is `GET /path -> node <role> "<name>" exists` (or `absent`): the page is read in a second tab of the same session, so the driven page stays where the action left it, and the tree is normalised the way interface parity normalises it. A target that has a JSON surface must use it — the tree form asserts only that the rebuilt view offers a control, not that a value was stored, and is acceptable only where the product has one code path from persistent state to page (see [targets/web.md](targets/web.md)).

Every line true is the row passed. A line is re-read every 250 ms of wall time until it holds, for at most 10 s: the action's own request finishes on the wall clock, not the page's, and the read has to come after it. The negative control spends the same 10 s before it reports the miss, so a write that is merely slow cannot pass as one that did not happen. A trigger it cannot find by role and name fails the row with `no control`, and so does an `observe` operation the surface answers with a non-2xx status or the wrong content type.

Before every row the product is asked whether it is ready and the page is reloaded, so state a person left in the window is gone; every row runs its own `reach` (idempotent, so a state already there is left there). When the run ends the product is given back.

## The criterion, in one shape

Written onto the ticket, run by a shell months later with no model between; the path is literal and is the install location `install.sh` creates on every machine. Nothing about the machine is on the line: how the product is reached, and the reach script, come from the repository's `.mmw/target.json` through the contract's `target.kind` ([targets/README.md](targets/README.md)).

```
CHECK: uv run ~/.agents/skills/verify-ticket/scripts/wiring-check.py --contract docs/specs/<effort>/screen-contract.yaml --rows <id,id>
EXPECT: WIRING OK <passed>/<total>
```

Rows that share a `reach` state may share a criterion; rows that need different states need not be split any more, because each row runs its own `reach`. The product must be running when the criterion runs and is left running afterwards.

## The negative control

A wiring check can be asked to prove it can fail:

```
CHECK: uv run ~/.agents/skills/verify-ticket/scripts/wiring-check.py --contract docs/specs/<effort>/screen-contract.yaml --rows <id,id> --negative
EXPECT: WIRING NEGATIVE OK <n>/<n>
```

It runs the repository's `transport_off` command, runs every row, and requires every one of them to fail **on an `observe` assertion** — a specific `MISS <row> — <expression> was …` — then runs `transport_on`. That is the property that matters, and it cannot be satisfied by narrowing: an `observe` line that goes green with nothing persisted is caught here and nowhere else. A row that still passed prints `GREEN WITHOUT TRANSPORT <row>` (exit 1). A run that failed before any `observe` was evaluated — attach needed the database too, the product stopped answering — proves nothing and is exit 2, not a pass. How the transport is broken is the seventh question every target answers; the static guard in the consuming repository is the second line behind this one.

## Reading what it printed

- `0`, one line `WIRING OK <passed>/<total>`: every row's `observe` held.
- `1`: one `MISS <row id> — <reason>` line per failing row: `no control <role> "<name>"`, `<operation> answered <status>`, `<expression> was <value>`, `not ready: <why>`; or `GREEN WITHOUT TRANSPORT <row id>` under `--negative`.
- `2`: the run could not start — no `.mmw/target.json`, the product not reachable, the reach script exited non-zero, a row id not in the contract, a row without `observe`; or, under `--negative`, no `observe` was evaluated.

What to fix is what the line names. A `no control` line is the accessible name: compare the running interface's tree with the row's `trigger` before touching anything else.
