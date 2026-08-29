# Models

One row per `(agent, host)`. Every agent this pipeline sends out is here except the
orchestrator, which is the session you started yourself from the CLI.

A non-empty launch command means the agent runs as its own session in a Herdr pane, and
`dispatch.sh` starts it. `{model}`, `{effort}` and `{n}` are replaced with that row's
model, that row's effort, and the real ticket number, so changing which model an agent
runs on is an edit to the model column alone. The first word of the command names the
harness binary; `herdr` supplies that binary itself from the host column, and
`dispatch.sh` passes only the arguments after it.

A launch command of `—` means the agent is a subagent: it runs inside its caller's
session, is dispatched by whichever skill needs it, and never goes through Herdr. These
rows are the defaults `assemble.py` writes into each harness's agent definition file.

Read `references/before-editing.md` before you change anything here.

| agent | host | model | effort | launch command |
| --- | --- | --- | --- | --- |
| junior-worker | cursor | `cursor-grok-4.6-high` | high | `cursor-agent -w issue-{n} --worktree-base main --force --trust --model {model}` |
| senior-worker | grok | `grok-4.6` | xhigh | `grok --worktree=issue-{n} --worktree-ref main --permission-mode bypassPermissions -m {model} --reasoning-effort {effort}` |
| reviewer | claude | `opus` | — | `claude --permission-mode bypassPermissions --model {model} -n issue-{n}-review` |
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
