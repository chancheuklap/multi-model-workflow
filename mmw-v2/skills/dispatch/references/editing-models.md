# Changing host, model, or which runner this machine uses

Read this only when the user has told you to change which host, model or reasoning effort (`effort` in `models.json`) a dispatched session uses, or which runner the machine uses. The saved configuration is `MMW_HOME/models.json`; when `MMW_HOME` is unset, that means `~/.mmw/models.json`. Change it only through the commands below.

## Resolve `<models>` once

`<models>` in every command below is `scripts/models.py` of this skill, run as `python3 <absolute path to scripts/models.py>`. Resolve it from the location of this skill's `SKILL.md`; the path differs by machine and by host.

## Change one role

The `models.py config set` command changes one role. Run:

```bash
<models> config set <role> <host> <model> <level>
```

Allowed roles are `junior-worker`, `senior-worker`, `reviewer`, and `advisor`. `<level>` is the reasoning level, saved as the row's `effort`. The command scans the selected runner's current catalog and refuses a model or level it does not offer.

A host that carries the level inside the model instead of taking it as a setting of its own offers model-and-level pairs, each pair set per model in that host's own application; `config set` only selects among the pairs the scan returns, so a level that application has not been given for that model is unavailable until it is added there. `fast` belongs in the model name, not in `effort`. A runner that hands the host its level as a thinking option the host offers only as on or off uses the level for nothing else: `off`, or no level at all, turns thinking off, and every other level turns it on.

## Change the runner

Run:

```bash
<models> config runner <runner>
```

The command scans the catalog belonging to the proposed runner and refuses it unless every saved role can still start.

Use `<models> config show` to read the current saved object. The next `start` reads it again; no daemon restart or install is required.

One difference between runners outlives the command; tell the user of it when the runner changes. A runner that cannot observe the program running inside its session answers exit 4 to every `resume` and every relay wake it delivers: the text went in, whether a turn started is not known. A night runs normally on it, since every result is an event on the ticket, but nobody can tell a silent worker that read its message from one that did not. Each adapter's header records what its runner can observe.
