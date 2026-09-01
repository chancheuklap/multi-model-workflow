# Models

One row per `(agent, host)`. Every agent this pipeline sends out is here except the main agent — the session you started yourself. This is the only place any of their models are written down. The three code-review axis subagents (`Standards` / `Spec` / `Tests`) are the `reviewer` subagent, started inside the reviewer session, so the reviewer row is read twice: `dispatch.sh` starts the session from its launch arguments, and `assemble.py` builds the subagent's definition file from its model and effort.

The agent names ending `-worker` are the two worker grades, and each is also the label a ticket carries to say which of them it gets, so renaming one of those rows renames a label on every ticket already asking for it. A ticket carrying no such label starts on `junior-worker`.

**Launch arguments** non-empty: the agent runs as its own Herdr session on the host column's host, and `{model}`, `{effort}` and `{n}` in the arguments are replaced with the row's model, the row's effort and the ticket number. `—`: the agent is a subagent, started inside the session that dispatches it. Every agent with a directory under `mmw-v2/agents/` also gets a per-host subagent definition assembled from its rows by `mmw-v2/agents/assemble.py`, whatever its launch column says. A host that burns the `effort` into the model name has `—` in the effort column.

**Before editing any row, read [`references/editing-models.md`](references/editing-models.md)**: how to confirm a model, an `effort` or a host on this machine, and what to run afterwards so the change takes effect.

| agent | host | model | effort | launch arguments |
| --- | --- | --- | --- | --- |
| junior-worker | codex | `gpt-5.6-terra` | high | `--dangerously-bypass-approvals-and-sandbox -m {model} -c model_reasoning_effort={effort}` |
| senior-worker | grok | `grok-4.6` | xhigh | `--permission-mode bypassPermissions -m {model} --reasoning-effort {effort}` |
| reviewer | claude | `opus` | high | `--permission-mode bypassPermissions --model {model} --effort {effort} -n issue-{n}-review` |
| reviewer | codex | `gpt-5.6-terra` | high | — |
| reviewer | cursor | `cursor-grok-4.6-high` | — | — |
| reviewer | grok | `grok-4.6` | high | — |
| reviewer | pi | `openai-codex/gpt-5.6-sol` | medium | — |
| verifier | claude | `sonnet` | high | — |
| verifier | codex | `gpt-5.6-luna` | high | — |
| verifier | cursor | `cursor-grok-4.6-high` | — | — |
| verifier | grok | `grok-4.6` | high | — |
| verifier | pi | `openai-codex/gpt-5.6-sol` | high | — |
| advisor | claude | `fable` | medium | — |
| advisor | codex | `gpt-5.6-sol` | medium | — |
| advisor | cursor | `claude-fable-5-thinking-medium` | — | — |
| advisor | grok | `grok-4.6` | xhigh | — |
| advisor | pi | `openai-codex/gpt-5.6-sol` | high | — |
| claim-checker | claude | `fable` | low | — |
| claim-checker | codex | `gpt-5.6-terra` | high | — |
| claim-checker | cursor | `cursor-grok-4.6-high` | — | — |
| claim-checker | grok | `grok-4.6` | high | — |
| claim-checker | pi | `openai-codex/gpt-5.6-sol` | medium | — |
