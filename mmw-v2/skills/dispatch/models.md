# Models

One row per `(agent, host)`. Every agent this pipeline sends out is here except the
orchestrator, which is the session you started yourself from the CLI.

Non-empty launch arguments mean the agent runs as its own session in a Herdr pane.
`dispatch.sh` reads the row at the moment it dispatches, so an edit to one of these rows
is in force on the very next dispatch, with nothing to rebuild and nothing to reinstall.
The host column decides which harness the session is, and it has to be one of the agent
kinds Herdr recognises; the arguments are handed to that harness untouched. `{model}`,
`{effort}` and `{n}` are replaced with the row's model, the row's effort, and the real
ticket number, so moving an agent to a different model is an edit to the model column
alone. Moving it to a different harness is an edit to the whole row: every harness
spells its models, its thinking levels and its arguments its own way.

Launch arguments of `—` mean the agent is a subagent: it runs inside the session that
dispatches it, never goes through Herdr, and `dispatch.sh` never reads its row. A
subagent takes its model and thinking level from its own definition file inside each
harness, and those files are built ahead of time by `mmw-v2/agents/assemble.py` out of
`mmw-v2/agents/<name>/agent.json`. Editing one of these rows therefore reaches no
subagent. They are here so that every agent this pipeline sends out can be read in one
place.

Read `references/before-editing.md` before you change anything here.

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
| ui-evaluator | claude | `opus` | medium | — |
| ui-evaluator | cursor | `cursor-grok-4.6` | high | — |
| ui-evaluator | codex | `gpt-5.6-sol` | medium | — |
| ui-evaluator | grok | `grok-4.6` | high | — |
| ui-evaluator | pi | `openai-codex/gpt-5.6-sol` | medium | — |
