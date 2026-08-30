# Models

One row per `(agent, host)`. Every agent this pipeline sends out is here except the
orchestrator, which is the session you started yourself from the CLI. This is the only
place any of their models are written down.

**Launch arguments** say how the agent is started, and which of the two kinds it is.
Non-empty, and the agent runs as its own session in a Herdr pane: the host column says
which harness that session is, and the arguments are handed to that harness untouched.
`—`, and the agent is a subagent: it runs inside the session that dispatches it and
never goes through Herdr.

`{model}`, `{effort}` and `{n}` in an argument are replaced with the row's model, the
row's effort, and the real ticket number, so moving an agent to a different model is an
edit to the model column alone. Moving it to a different harness is an edit to the whole
row: every harness spells its models, its thinking levels and its arguments its own way.

Read [`references/editing-models.md`](references/editing-models.md) before you change
anything here. It also says what to do afterwards, which is not the same for both kinds
of row.

| agent | host | model | effort | launch arguments |
| --- | --- | --- | --- | --- |
| junior-worker | cursor | `cursor-grok-4.6-high` | high | `-w issue-{n} --worktree-base main --force --trust --model {model}` |
| senior-worker | grok | `grok-4.6` | xhigh | `--worktree=issue-{n} --worktree-ref main --permission-mode bypassPermissions -m {model} --reasoning-effort {effort}` |
| reviewer | claude | `opus` | — | `--permission-mode bypassPermissions --model {model} -n issue-{n}-review` |
| verifier | claude | `sonnet` | medium | — |
| verifier | cursor | `gpt-5.6-sol-high` | high | — |
| verifier | codex | `gpt-5.6-terra` | high | — |
| verifier | grok | `grok-4.5` | high | — |
| verifier | pi | `openai-codex/gpt-5.6-sol` | high | — |
| advisor | claude | `fable` | medium | — |
| advisor | cursor | `claude-fable-5` | medium | — |
| advisor | codex | `gpt-5.6-sol` | high | — |
| advisor | grok | `grok-4.6` | xhigh | — |
| advisor | pi | `openai-codex/gpt-5.6-sol` | high | — |
| claim-checker | claude | `opus` | medium | — |
| claim-checker | cursor | `cursor-grok-4.6` | high | — |
| claim-checker | codex | `gpt-5.6-sol` | medium | — |
| claim-checker | grok | `grok-4.6` | high | — |
| claim-checker | pi | `openai-codex/gpt-5.6-sol` | medium | — |
