# Models

One row per `(agent, host)`, except `advisor`, which has two rows on `claude`: a `bypass` session row and a `—` native row. Every agent this pipeline sends out is here except the main agent — the session you started yourself. This is the only place any of their models are written down. The three code-review axis subagents (`Standards` / `Spec` / `Tests`) are the `reviewer` subagent, started inside the reviewer session, so the reviewer row is read twice: `install.sh` writes a Paseo Agent profile from the `bypass` row, and `assemble.py` builds the subagent's definition file from its model and effort. The `advisor` rows are the two doors that agent has: the `bypass` row is the Paseo session a caller reaches with `create_agent`, and the `—` row is the native subagent it falls back to. Only the second is held to reading — its definition file lists the tools; a Paseo session on any host can write through a shell.

The agent names ending `-worker` are the two worker grades, and each is also the label a ticket carries to say which of them it gets, so renaming one of those rows renames a label on every ticket already asking for it. A ticket carrying no such label starts on `junior-worker`.

**permissions** `bypass`: the agent runs as its own Paseo session on the host column's host, with all permissions granted. `—`: the agent is a native subagent, started inside the session that dispatches it. Every agent with a directory under `mmw-v2/agents/` also gets a per-host subagent definition assembled by `mmw-v2/agents/assemble.py`, for the hosts this table lists. A host that burns the `effort` into the model name has `—` in the effort column.

A `bypass` row's model is the name Paseo prints for it, which is not always the name the host's own command line takes: `paseo provider models <host> --json` is the list, and section 1 of [`references/editing-models.md`](references/editing-models.md) is how to read it.

**Before editing any row, read [`references/editing-models.md`](references/editing-models.md)**: how to confirm a host, a model or an `effort` on this machine, and what to run afterwards so the change takes effect.

| agent | host | model | effort | permissions |
| --- | --- | --- | --- | --- |
| junior-worker | cursor | `grok-4.6` | high | bypass |
| senior-worker | grok | `grok-4.6` | xhigh | bypass |
| reviewer | claude | `claude-opus-5` | high | bypass |
| reviewer | codex | `gpt-5.6-terra` | high | — |
| reviewer | cursor | `cursor-grok-4.6-high` | — | — |
| reviewer | grok | `grok-4.6` | high | — |
| reviewer | pi | `openai-codex/gpt-5.6-sol` | medium | — |
| verifier | claude | `claude-sonnet-5` | high | bypass |
| advisor | claude | `claude-fable-5-1` | medium | bypass |
| advisor | claude | `claude-fable-5-1` | medium | — |
| advisor | codex | `gpt-5.6-sol` | medium | — |
| advisor | cursor | `claude-fable-5-thinking-medium` | — | — |
| advisor | grok | `grok-4.6` | xhigh | — |
| advisor | pi | `openai-codex/gpt-5.6-sol` | high | — |
| claim-checker | claude | `claude-fable-5-1` | low | — |
| claim-checker | codex | `gpt-5.6-terra` | high | — |
| claim-checker | cursor | `cursor-grok-4.6-high` | — | — |
| claim-checker | grok | `grok-4.6` | high | — |
| claim-checker | pi | `openai-codex/gpt-5.6-sol` | medium | — |
