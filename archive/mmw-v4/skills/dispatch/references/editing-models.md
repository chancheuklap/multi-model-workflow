# Changing host, model, which runner this machine uses, or how many tickets a night runs at once

Read this only when the user has told you to change which host, model or reasoning effort (`effort` in `models.json`) a dispatched session uses, a subagent row, which runner the machine uses, or how many tickets a night runs at once. Change it only through the commands below.

## Change one role

The `models.py config set` command changes one role. Run:

```bash
python3 scripts/models.py config set <role> <host> <model> <level>
```

The roles are the rows of `roles.json`: `junior-worker`, `senior-worker`, `reviewer`, `advisor`, `researcher`, `candidate` and `retro-analyst`. `<level>` is the reasoning effort, saved as the row's `effort`.

A host that carries the level inside the model instead of taking it as a setting of its own offers model-and-level pairs, each pair set per model in that host's own application; `config set` only selects among the pairs the scan returns, so a level that application has not been given for that model is unavailable until it is added there. `fast` belongs in the model name, not in `effort`. A runner that hands the host its level as a thinking option the host offers only as on or off uses the level for nothing else: `off`, or no level at all, turns thinking off, and every other level turns it on.

## Change the runner

Run:

```bash
python3 scripts/models.py config runner <runner>
```

`<runner>` names an adapter under `scripts/runners/`, or `auto`. `auto` takes the runner the calling session runs in, falling back to the configured default when none is detected. `MMW_RUNNER` set in the environment overrides the saved runner for that process.

The last successful catalog and any later read failure are in `$MMW_HOME/catalog.json` (`~/.mmw/catalog.json` when `MMW_HOME` is unset); inspect the host's `failure` there for the reason.

Use `python3 scripts/models.py config show` to read the current saved object. The next `start` reads it again; no daemon restart or install is required.

One difference between runners outlives the command; tell the user of it when the runner changes. A runner that cannot observe the program running inside its session answers exit 4 to every `resume` and every relay wake it delivers: the text went in, whether a turn started is not known. A night runs normally on it, since every result is an event on the ticket, but nobody can tell a silent worker that read its message from one that did not. Each adapter's header records what its runner can observe.

## Change how many tickets a night runs at once

`max_workers` caps how many of one night's tickets are held at once; `advance` starts no more than that, and names each ticket left waiting. It is 3 when `models.json` does not set it. Run:

```bash
python3 scripts/models.py config set max_workers <n>
```

`<n>` is a whole number of at least 1. A session the owner starts in the day, and a ticket run outside a night, do not count against it.

## Change one subagent row

Run:

```bash
python3 scripts/models.py config subagent <row> <host> <model|inherit> <effort|inherit>
```

The rows are `review-axis`, `reader`, and `default` in `roles.json`'s `subagents` section. Choose the host explicitly, either `claude` or `codex`. To read its saved choice, run:

```bash
python3 scripts/models.py subagent <row> <host>
```

The query prints `model=<value> effort=<value>`. A missing section, row, or host returns `inherit` for both values. `inherit` keeps the sending session's model or effort. `config show` includes saved subagent settings. A write uses the same lock and version as a role change, and other configuration writes keep these settings.

For `claude`, model accepts `sonnet`, `opus`, `haiku`, `fable`, or `inherit`. Effort accepts `low`, `medium`, `high`, `xhigh`, `max`, or `inherit`. These model aliases are the values the subagent dispatch call accepts, not every name the session's model picker offers.

For `codex`, model accepts `inherit` or any visible model id in the `cli` → `codex` entry of `$MMW_HOME/catalog.json`. Effort accepts `inherit` or one of the selected model's efforts. With model set to `inherit`, effort accepts only `inherit` or an effort every visible model supports, because the sending session's model is not known when saving. Without that catalog, only `inherit` for both values can be saved. Click **重新扫描** on the task board or run `install.sh --check` to read the catalog first.
