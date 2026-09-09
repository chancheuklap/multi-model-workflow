# Changing host, model, or which night this machine runs

Read this only when the user has told you to change which host, model or `effort` a dispatched session uses, or whether the night runs on Herdr or Paseo. `start` does not read this file.

## The live table

The table is `~/.mmw/models.md`. It is this machine's fact. Edit it; do not edit anything in git for tonight's reviewer.

Four columns: `agent | host | model | effort`. Everyday names: `junior-worker | cursor | grok 4.6 | high`. Allowed `agent` values: `junior-worker`, `senior-worker`, `reviewer`, `verifier`, `advisor`. The first row for an agent is the host `start` uses; a later row on a different host is the fallback. Two rows for one agent cannot share a host.

Herdr versus Paseo is not a column. Do not write `herdr` or `paseo` into `host`. Changing which night this machine runs is changing which checkout is installed, not a cell.

The next `start` reads the live file. First `install.sh` copies the defaults if the file is missing; a later `install.sh` leaves it.

## Confirm a host

The `host` cell is one of `claude`, `codex`, `grok`, `cursor`, `pi`. On Herdr, `herdr agent start --help` lists kinds. On Paseo, `paseo provider ls` lists providers whose status is `available`.

## Confirm a model or an `effort`

Ask this machine, do not guess.

| Host | Ask it this |
| --- | --- |
| Cursor | `cursor-agent models` |
| Grok Build | `grok models` |
| Claude Code | `claude --help` under `--model`, or `paseo provider models claude --json` when Paseo is on the machine |
| Codex | `~/.codex/config.toml` holds what is in use; `-m` takes a name as free text |
| pi | `pi --list-models` |

Write the everyday name in the live table (`grok 4.6`, `opus 5`, `high`). `start` asks the same lists and uses the unique match. If both an ordinary Cursor offering and a `fast` sibling would match, write `fast` only when you want the fast build.
