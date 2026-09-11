# Changing host, model, or which runner this machine uses

Read this only when the user has told you to change which host, model or `effort` a dispatched session uses, or which runner the machine uses. The saved configuration is `MMW_HOME/models.json`; when `MMW_HOME` is unset, that means `~/.mmw/models.json`. Do not edit it by hand.

## Change one role

Resolve `scripts/models.py` from this skill's own location. Run:

```bash
python3 <absolute path to models.py> config set <role> <host> <model> <effort>
```

Allowed roles are `junior-worker`, `senior-worker`, `reviewer`, `verifier`, and `advisor`. Allowed hosts are `claude`, `codex`, `grok`, `cursor`, and `pi`, subject to what the selected runner can start. The command scans that runner's current catalog, refuses a model or effort it does not offer, takes the configuration lock, checks the saved version has not changed, increments the version, and replaces the JSON file atomically.

On Cursor, effort is set per model in the Cursor app. A level the scan does not return is unavailable until it is added there. `fast` belongs in the model name (`grok 4.6 fast`), not in `effort`. On a Paseo run, Cursor thinking is only on or off: `high` turns it on and `off` turns it off.

## Change the runner

Run:

```bash
python3 <absolute path to models.py> config runner <runner>
```

Saved runner values are `orca`, `herdr`, `paseo`, or `auto`. `start` chooses `MMW_RUNNER` first, then this saved value, then a runner detected from the current process when the saved value is `auto`, then `orca`. The command scans the catalog belonging to the proposed runner and refuses it unless every saved role can still start.

Use `config show` to read the current saved object. The next `start` reads it again; no daemon restart or install is required.
