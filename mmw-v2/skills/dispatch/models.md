# Models

One row per `(agent, host)`, with one exception: an agent that names a fallback host has a second `bypass` row on that host. The first `bypass` row for an agent is the host `start` uses; a later `bypass` row is the fallback host, tried only after `create_agent` has failed on the one before it. Two `bypass` rows for one agent cannot share a host, and an agent has at most one fallback. `install.sh` writes one Agent profile per `bypass` row: the first keeps `id` and `name` equal to the agent cell, so existing profiles and `mmw.profile` labels do not move; a later row's `id` and `name` are `{agent}@{host}`.

Every agent this pipeline sends out is here except two. The main agent is the session you started yourself. The three code-review axis subagents (`Standards` / `Spec` / `Tests`) are the general-purpose subagent of whichever host the reviewer session runs on, so they have no row and no model of their own: they run on the model of the session that starts them, and what holds them to reading is the `code-review` skill's axis door. `advisor` has one row and one door: a Paseo session a caller starts with `create_agent`, its `initialPrompt` naming the `advisor` skill; no permission mode holds it to reading either — the skill does.

The agent names ending `-worker` are the two worker grades, and each is also the label a ticket carries to say which of them it gets, so renaming one of those rows renames a label on every ticket already asking for it. A ticket carrying no such label starts on `junior-worker`.

**permissions** takes one value, `bypass`: the agent runs as its own Paseo session on the host column's host, with all permissions granted. Which permission mode that means is the host's own business, and `scripts/models.py` is where each host's spelling of it lives. **effort** is the name Paseo lists as a `thinkingOptionId` for that model, and every row needs one: the cell is passed through as written, so a `—` here reaches Paseo as a thinking level called `—`.

A `bypass` row's model is the name Paseo prints for it, which is not always the name the host's own command line takes: `paseo provider models <host> --json` is the list, and section 1 of [`references/editing-models.md`](references/editing-models.md) is how to read it.

**Before editing any row, read [`references/editing-models.md`](references/editing-models.md)**: how to confirm a host, a model or an `effort` on this machine, and what to run afterwards so the change takes effect.

| agent | host | model | effort | permissions |
| --- | --- | --- | --- | --- |
| junior-worker | cursor | `grok-4.6` | high | bypass |
| junior-worker | grok | `grok-4.6` | high | bypass |
| senior-worker | grok | `grok-4.6` | xhigh | bypass |
| reviewer | claude | `claude-opus-5` | high | bypass |
| verifier | claude | `claude-sonnet-5` | high | bypass |
| advisor | claude | `claude-fable-5-1` | medium | bypass |
