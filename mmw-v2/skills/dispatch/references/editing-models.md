# Editing models.md

A row is only correct on the machine it runs on, and none of what makes it correct can
be answered from memory. Confirm what you are about to touch, write the row, then make
it take effect.

## 1. Confirm a model or a thinking level

Model names are not shared between harnesses, and neither are the names of the thinking
levels — one harness's `high` is another's `xhigh`, and some have no separate level at
all. Ask the harness itself.

| Harness | Ask it this |
| --- | --- |
| Cursor | `cursor-agent models` lists them. The effort is burned into the slug, so there is no bare `cursor-grok-4.6` — the high-effort build is its own name |
| pi | `pi --list-models` lists them. A name is `provider/id`, and the thinking level is the row's own column |
| Claude Code | `claude --help`, under `--model`: an alias for the newest of a family (`fable`, `opus`, `sonnet`) or a full model name |
| Grok Build | `grok --help`, under `-m` and `--reasoning-effort`. Neither enumerates its values; `grok inspect` prints the configuration Grok has right now |
| Codex | Nothing lists them. `-m` takes the name as free text, and `~/.codex/config.toml` holds the `model` and `model_reasoning_effort` in use now |

## 2. Confirm a harness

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

## 3. Make the edit take effect

Which half of the table you edited decides this.

**A row with launch arguments** runs as its own Herdr session, and `dispatch.sh` reads
the row at the moment it dispatches. You are already done: the next dispatch uses what
you wrote.

**A row with `—`** is a subagent, and a harness reads a subagent's model out of its own
agent definition file, not out of this table. Build the table into those files:

```bash
python3 mmw-v2/agents/assemble.py
```

Run it in the checkout the harnesses are installed from — section 4 says how to tell
which one that is. Then the change is live in the next session that dispatches that
subagent. That command is the whole of it: the harnesses hold links to the built files,
and the links do not move. `install.sh` is for adding a whole new agent, not for
changing one.

## 4. Check that a subagent row landed

Read the definition file for the agent you changed and confirm the new model is in it.

| Harness | Where its agent definitions live |
| --- | --- |
| Claude Code | `~/.claude/agents/` |
| Cursor | `~/.cursor/agents/` |
| Codex | `~/.codex/agents/` |
| Grok Build | `~/.grok/agents/` for the definition and the model, `~/.grok/roles/` for read-only tools and reasoning effort |
| pi | `~/.pi/agent/agents/` |

Each of those is a link into the checkout the harnesses were installed from, so
following one also tells you which checkout that is. A file still showing the old model
means the build ran somewhere else.
