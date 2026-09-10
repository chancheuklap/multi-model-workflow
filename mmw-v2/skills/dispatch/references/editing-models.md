# Changing host, model, or which night this machine runs

Read this only when the user has told you to change which host, model or `effort` a dispatched session uses, or which runner the night runs on. `start` does not read this file.

## The live table

The table is `~/.mmw/models.md`. It is this machine's fact. Edit it; do not edit anything in git for tonight's reviewer.

Four columns: `agent | host | model | effort`. The `model` and `effort` cells are copied from the tables under `<!-- mmw-offerings -->` in that same file — those tables are the legal pairs for tonight. Allowed `agent` values: `junior-worker`, `senior-worker`, `reviewer`, `verifier`, `advisor`. One row per agent: a second row for the same agent is refused when the table is read.

A two-cell `runner` row may sit above those: `| runner | <name> |`. Names: `herdr`, `orca`, `paseo`, `tmux`, `lody`. Do not write those into `host`. `start` picks tonight's runner in this order: `MMW_RUNNER`, then this row, then the runner the calling session runs in, then `orca`. A fresh table has no runner row, so runtime detection can speak. `start` has an adapter for `herdr`, `orca` and `paseo`; naming `tmux` or `lody` is refused at `start`. A per-ticket choice has no place on the ticket yet.

Runtime detection treats `TERM_PROGRAM=Orca` as the outer signal: Herdr opened inside an Orca terminal is `herdr`. When `HERDR_ENV` and `TMUX` are both set, the code returns `tmux`; that does not say which is nested in which.

The next `start` reads the agent rows above `<!-- mmw-offerings -->`. First `install.sh` copies the defaults if the file is missing; a later `install.sh` leaves the rows and refreshes the copy-tables.

## Confirm a host

The `host` cell is one of `claude`, `codex`, `grok`, `cursor`, `pi`. On Herdr, `herdr agent start --help` lists kinds. On Paseo, `paseo provider ls` lists providers whose status is `available`.

## Confirm a model or an `effort`

Run `python3` on this skill's `scripts/models.py offerings` (resolve the path from this skill's `SKILL.md`, same way as `<dispatch>`). That rewrites the copy-tables under the live table. Then copy one whole row from the host's table into `model` and `effort`. `start` does not read the copy-tables; it asks tonight's catalog again and uses the unique match.

On Cursor, effort is not a free cell: it is set per model in the Cursor app, and `cursor-agent models` only lists the pairs that already exist. Copy one whole Cursor row. A level with no row is not available until you add it in the app and scan again. `fast` is its own `model` cell (`grok 4.6 fast`), never an `effort`. On a Paseo night, Cursor thinking is only on or off — `high` turns it on, `off` turns it off; copying `xhigh` does not select extra-high.
