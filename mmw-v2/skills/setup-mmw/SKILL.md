---
name: setup-mmw
description: Shows and changes the host, model and reasoning effort each pipeline role runs on and the runner that starts its sessions, checks what this machine has installed, and opens the local task board. Use when the user asks which model a role runs on, asks to change a role's host, model, reasoning effort or the runner, or asks to open the task board. Not for installing the toolbox on a machine, which the user authorises separately.
---

# Setup MMW

Every session the pipeline starts for a role runs on the host, model and reasoning effort of that role's row in `models.json`, and the runner that file names starts it. The next session started for a role runs on what is saved there, so a value written into the file by hand, or recalled instead of read, starts that session on something nobody chose. Change it only through the commands below.

Commands of the `mmw` skill's `python3 scripts/models.py` and `bash scripts/dispatch.sh` are named bare below; both files sit in the directory your host loaded the `mmw` skill from.

## Read a role's row

`models.py config get <row>` prints one saved row and changes nothing.

The row is one of `models.json`, not a role a session reports: a worker runs on the `junior-worker` or the `senior-worker` row.

- **Exit 0.** One line, `<row> <host> <model> <effort>`.
- **Exit 2.** No row was printed: `<row>` is not a row, the file has no complete row of that name, or the file cannot be read; the stderr line says which and what to run next.

## Change one row

The `models.py config set` command changes one row. Run:

```bash
models.py config set <row> <host> <model> <level>
```

Allowed rows are `junior-worker`, `senior-worker`, `reviewer`, `advisor`, and `researcher`. `<level>` is the reasoning effort, saved as the row's `effort`.

The `researcher` row is optional: a `models.json` written before the role existed lacks it, and `install.sh` never adds a row to a file that already exists. A `models.json` without that row stays valid and every other role still starts from it; only `dispatch.sh research <n>` refuses, and its refusal names the `config set` command that adds the row.

A host that carries the level inside the model instead of taking it as a setting of its own offers model-and-level pairs, each pair set per model in that host's own application; `config set` only selects among the pairs the scan returns, so a level that application has not been given for that model is unavailable until it is added there. `fast` belongs in the model name, not in `effort`. A runner that hands the host its level as a thinking option the host offers only as on or off uses the level for nothing else: `off`, or no level at all, turns thinking off, and every other level turns it on.

## Change the runner

Run:

```bash
models.py config runner <runner>
```

Use `models.py config show` to read the current saved object. The next `start` reads it again; no daemon restart or install is required.

One difference between runners outlives the command; tell the user of it when the runner changes. A runner that cannot observe the program running inside its session answers exit 4 to every `resume` and every relay wake it delivers: the text went in, whether a turn started is not known. A night runs normally on it, since every result is an event on the ticket, but nobody can tell a silent worker that read its message from one that did not. Each adapter's header records what its runner can observe.

## Check the installation

`bash "$(cat ~/.mmw/installed-root)/install.sh" --check` reads what this machine has installed and changes nothing.

Exit 0: every item is in place. Exit 1: an item is missing or stale, and a line names it. It also prints one `OPEN-WATCH` line per open watch and one `LIVE-LOCK` line per live lock, and ends with `SAFE-TO-MOVE-INSTALLED` or `NOT-SAFE-TO-MOVE-INSTALLED`; none of these changes the exit code.

A full `install.sh` changes the skills and hooks of every host on this machine, so it runs only when the user has said so; with nobody there to say so, report the `--check` lines and stop.

## Open the task board

Run `dispatch.sh board` from any checkout of the repository. Exit 0 opened the board or printed its URL for you to hand the user; exit 2 says why on stderr.

## Output

- **`config get`.** One line, `<row> <host> <model> <effort>`.
- **`config set` and `config runner`.** The saved object as one line of JSON, its `version` one higher than before.
- **`config show`.** The saved object.
- **`install.sh --check`.** A line for each item that is missing or stale, the `OPEN-WATCH` and `LIVE-LOCK` lines, the `SAFE-TO-MOVE-INSTALLED` or `NOT-SAFE-TO-MOVE-INSTALLED` line, and the exit code.
- **`board`.** The board open, or its URL for the user.
