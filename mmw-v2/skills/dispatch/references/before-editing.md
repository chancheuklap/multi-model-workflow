# Before editing models.md

A row is only correct on the machine it runs on, and none of what makes it correct can
be answered from memory. Confirm the parts you are about to touch first.

## Changing a model or a thinking level

Model names are not shared between harnesses, and neither are the names of the thinking
levels — one harness's `high` is another's `xhigh`, and some have no separate level at
all. Ask the harness itself.

| Harness | Ask it this |
| --- | --- |
| Cursor | `cursor-agent models`. The effort is burned into the slug, so there is no bare `cursor-grok-4.6` — the high-effort build is its own name |
| Claude Code | `claude --help`, under `--model` |
| Grok Build | `grok --help`, under `-m` and `--reasoning-effort` |
| Codex | the model string Codex itself accepts |
| pi | a two-part `provider/model` string |

## Changing which harness a session runs on

Only the rows with launch arguments can move to another harness. Two things have to be
right, and both come from the machine:

1. **The host cell has to name an agent kind Herdr recognises.** Run `herdr agent` to
   see the list it accepts. A name that is not on it is refused and no session starts.
2. **The arguments have to be that harness's own.** A worker's arguments have to say
   four things: enter the worktree for this ticket, run without stopping to ask for
   approval, use this model, use this thinking level. Every harness spells all four
   differently, and not every harness has all four — one opens a worktree with a flag,
   another with a different flag, a third has no such flag at all. Read the new
   harness's own `--help` and write the row from that, not from the row you are
   replacing.

## Checking that a subagent row took effect

A subagent's model does not reach a harness from this table directly: it is built into
that harness's own agent definition file. After you have rebuilt, read the file for the
agent you changed and confirm the new model is in it.

| Harness | Where its agent definitions live |
| --- | --- |
| Claude Code | `~/.claude/agents/` |
| Cursor | `~/.cursor/agents/` |
| Codex | `~/.codex/agents/` |
| Grok Build | `~/.grok/agents/` for the definition and the model, `~/.grok/roles/` for read-only tools and reasoning effort |
| pi | `~/.pi/agent/agents/` |

Each of those is a link into the checkout the harnesses were installed from. If a file
there still shows the old model, the rebuild ran somewhere else.
