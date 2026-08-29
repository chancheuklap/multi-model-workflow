# Before editing models.md

A row in `models.md` is only correct on the machine it runs on. Two things about that
machine decide whether the row works, and neither can be answered from memory. Confirm
both before you change a row.

## 1. Where this harness keeps its agent definitions

Each harness reads its subagents from its own directory. Look at what is in the one you
are about to affect, so you know which agents already exist and what their definitions
currently say.

| Harness | Where its agent definitions live |
| --- | --- |
| Claude Code | `~/.claude/agents/` |
| Cursor | `~/.cursor/agents/` |
| Codex | `~/.codex/agents/` |
| Grok Build | `~/.grok/agents/` for the definition and the model, `~/.grok/roles/` for read-only tools and reasoning effort |
| pi | `~/.pi/agent/agents/` |

## 2. How this harness spells its models and thinking levels

Model names are not shared between harnesses, and neither are the names of the thinking
levels. Ask the harness itself; do not copy a name from another row or from memory.

| Harness | Ask it this |
| --- | --- |
| Cursor | `cursor-agent models`. The effort is burned into the slug, so there is no bare `cursor-grok-4.6` — the high-effort build is its own name |
| Claude Code | `claude --help`, under `--model` |
| Grok Build | `grok --help`, under `-m` and `--reasoning-effort` |
| Codex | the model string Codex itself accepts |
| pi | a two-part `provider/model` string |

The levels themselves differ too — one harness's `high` is another's `xhigh`, and some
have no separate level at all. Ask each one for its own list rather than reusing a level
that worked elsewhere.
