# Changing host, model, which runner this machine uses, or how many tickets a night runs at once

Read this only when the user has told you to change which host, model or reasoning effort (`effort` in `models.json`) a dispatched session uses, which runner the machine uses, or how many tickets a night runs at once. Change it only through the commands below.

## Change one role

The `models.py config set` command changes one role. Run:

```bash
python3 scripts/models.py config set <role> <host> <model> <level>
```

The roles are the rows of `roles.json`: `junior-worker`, `senior-worker`, `reviewer`, `advisor`, `researcher` and `candidate`. `<level>` is the reasoning effort, saved as the row's `effort`.

A host that carries the level inside the model instead of taking it as a setting of its own offers model-and-level pairs, each pair set per model in that host's own application; `config set` only selects among the pairs the scan returns, so a level that application has not been given for that model is unavailable until it is added there. `fast` belongs in the model name, not in `effort`. A runner that hands the host its level as a thinking option the host offers only as on or off uses the level for nothing else: `off`, or no level at all, turns thinking off, and every other level turns it on.

## Change the runner

Run:

```bash
python3 scripts/models.py config runner <runner>
```

`<runner>` is `orca`, `herdr`, `paseo` or `auto`. `auto` takes the runner the session running `dispatch.sh` sits in: Herdr when that session runs in Herdr, otherwise Orca; Paseo is chosen only by name. `MMW_RUNNER` set in the environment overrides the saved runner for that process.

Use `python3 scripts/models.py config show` to read the current saved object. The next `start` reads it again; no daemon restart or install is required.

One difference between runners outlives the command; tell the user of it when the runner changes. A runner that cannot observe the program running inside its session answers exit 4 to every `resume` and every relay wake it delivers: the text went in, whether a turn started is not known. A night runs normally on it, since every result is an event on the ticket, but nobody can tell a silent worker that read its message from one that did not. Each adapter's header records what its runner can observe.

## Change how many tickets a night runs at once

`max_workers` caps how many of one night's tickets are held at once; `advance` starts no more than that, and names each ticket left waiting. It is 3 when `models.json` does not set it. Run:

```bash
python3 scripts/models.py config set max_workers <n>
```

`<n>` is a whole number of at least 1. A session the owner starts in the day, and a ticket run outside a night, do not count against it.
