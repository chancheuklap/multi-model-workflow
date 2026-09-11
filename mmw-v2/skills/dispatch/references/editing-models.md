# Changing host, model, or which runner this machine uses

Read this only when the user has told you to change which host, model or `effort` a dispatched session uses, or which runner the machine uses. The saved configuration is `MMW_HOME/models.json`; when `MMW_HOME` is unset, that means `~/.mmw/models.json`. Do not edit it by hand.

## Resolve `<models>` once

Resolve `../scripts/models.py` once from this reference file's own location. Throughout the commands below, `<models>` expands to `python3 <absolute path to that models.py>`.

## Change one role

The `models.py config set` command changes one role. Run:

```bash
<models> config set <role> <host> <model> <effort>
```

Allowed roles are `junior-worker`, `senior-worker`, `reviewer`, `verifier`, and `advisor`. Allowed hosts are `claude`, `codex`, `grok`, `cursor`, and `pi`, subject to what the selected runner can start. The command scans that runner's current catalog, refuses a model or effort it does not offer, takes the configuration lock, checks the saved version has not changed, increments the version, and replaces the JSON file atomically.

A host that carries the level inside the model instead of taking it as a setting of its own offers model-and-effort pairs, each pair set per model in that host's own application; `config set` only selects among the pairs the scan returns, so a level that application has not been given for that model is unavailable until it is added there. `fast` belongs in the model name (`grok 4.6 fast`), not in `effort`. A runner that hands the host its level as a thinking option the host offers only as on or off uses the level for nothing else: `off`, or no level at all, turns thinking off, and every other level turns it on.

## Change the runner

Run:

```bash
<models> config runner <runner>
```

Saved runner values are `orca`, `herdr`, `paseo`, or `auto`. `start` chooses `MMW_RUNNER` first, then this saved value, then a runner detected from the current process when the saved value is `auto`, then `orca`. The command scans the catalog belonging to the proposed runner and refuses it unless every saved role can still start.

Use `<models> config show` to read the current saved object. The next `start` reads it again; no daemon restart or install is required.
