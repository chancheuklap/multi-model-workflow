# Changing host, model, or which night this machine runs

Read this only when the user has told you to change which host, model or `effort` a dispatched session uses, or whether the night runs on Herdr or Paseo. `start` does not read this file.

## The live table

The table is `~/.mmw/models.md`. It is this machine's fact. Edit it; do not edit anything in git for tonight's reviewer.

Four columns: `agent | host | model | effort`. The `model` and `effort` cells are copied from the tables under `<!-- mmw-offerings -->` in that same file — those tables are the legal pairs for tonight. Allowed `agent` values: `junior-worker`, `senior-worker`, `reviewer`, `verifier`, `advisor`. The first row for an agent is the host `start` uses; a later row on a different host is the fallback. Two rows for one agent cannot share a host.

A `runner` row sits above those: `| runner | <name> |`. Names: `herdr`, `orca`, `paseo`, `tmux`, `lody`. Do not write those into `host`. Changing which night this machine runs is editing that row. One launch without touching the row: `MMW_RUNNER`. `lody` is only used when written in the row, in `MMW_RUNNER`, or on the ticket.

The next `start` reads the rows above `<!-- mmw-offerings -->`. First `install.sh` copies the defaults if the file is missing; a later `install.sh` leaves the rows and refreshes the copy-tables.

## Confirm a host

The `host` cell is one of `claude`, `codex`, `grok`, `cursor`, `pi`. On Herdr, `herdr agent start --help` lists kinds. On Paseo, `paseo provider ls` lists providers whose status is `available`.

## Confirm a model or an `effort`

Run `python3` on this skill's `scripts/models.py offerings` (resolve the path from this skill's `SKILL.md`, same way as `<dispatch>`). That rewrites the copy-tables under the live table. Then copy one whole row from the host's table into `model` and `effort`. `start` does not read the copy-tables; it asks tonight's catalog again and uses the unique match.

On Cursor, effort is not a free cell: it is set per model in the Cursor app, and `cursor-agent models` only lists the pairs that already exist. Copy one whole Cursor row. A level with no row is not available until you add it in the app and scan again. `fast` is its own `model` cell (`grok 4.6 fast`), never an `effort`. On a Paseo night, Cursor thinking is only on or off — `high` turns it on, `off` turns it off; copying `xhigh` does not select extra-high.
