# Editing models.md

A `models.md` row is only correct on the machine it runs on, and none of what makes it correct can be answered from memory. Confirm what you are about to touch, write the row, then make it take effect.

## 1. Confirm a model, an `effort`, or a `read-only` spelling

Paseo is the first place to ask: `paseo provider models <provider> --json` lists that provider's models and its `thinkingOptionIds`. The names it prints are the host's own. Write the `model` and `effort` cells from that list.

When you need to see how a host spells a name outside Paseo, ask the host itself. This table is the fallback, not the path that makes a row take effect.

A `read-only` cell is a Paseo session that is not all-permissions. Confirm the host's mode id with `paseo provider ls --json` (that listing prints labels; `inspect_provider` / `list_providers` print the ids `install.sh` writes). Confirmed spelling: claude → `modeId: plan`; grok / cursor → `featureValues: {"auto_accept": false}`; codex has no read-only mode (`auto`, `auto-review`, `full-access`) so a Codex `read-only` row uses `modeId: auto`.

| Host | Ask it this |
| --- | --- |
| Cursor | `cursor-agent models` lists them. The effort is burned into the slug, so there is no bare `cursor-grok-4.6` — the high-effort build is its own name. A subagent row's model must also be enabled in the Cursor account's model settings, or the subagent is never registered |
| pi | `pi --list-models` lists them. A name is `provider/id`, and the `effort` is the row's own column |
| Claude Code | `claude --help`, under `--model`: an alias for the newest of a family (`fable`, `opus`, `sonnet`) or a full model name |
| Grok Build | `grok --help`, under `-m` and `--reasoning-effort`. Neither enumerates its values; `grok inspect` prints the configuration Grok has right now |
| Codex | Nothing lists them. `-m` takes the name as free text, and `~/.codex/config.toml` holds the `model` and `model_reasoning_effort` in use now |

## 2. Confirm a host

The host cell has to name a provider Paseo will start. Run `paseo provider ls` and take a row whose status is `available`. A name that is not on that list is refused and no session starts.

## 3. Make the edit take effect

Run `install.sh` from this repository:

```bash
bash mmw-v2/install.sh
```

That command is the whole of it. It rewrites every Agent profile whose `permissions` cell is `bypass` or `read-only`, reassembles every native subagent (`—`) into `agents/<name>/out/`, and points the host-side links at those files. The next session that starts that agent uses what you wrote.

## 4. Check that a row landed

A profile whose `notes` contain `from models.md` is one `install.sh` wrote: it is rewritten on every install and removed once its row is gone. A profile made by hand in the app keeps any other `notes` and is never touched.

## 5. What a row landed as

**A `bypass` or `read-only` row** is an Agent profile in `~/.paseo/config.json`, under `daemon.agentProfiles`: one entry whose `id` and `name` are both the agent cell, carrying the row's `model` and `thinkingOptionId`. Read that file, or run `bash mmw-v2/install.sh --check`, which compares each profile to the current row and exits 1 on drift, naming the agent.

**A `—` row** is a native subagent. Read the definition file for the agent you changed and confirm the new model is in it.

| Host | Where its agent definitions live |
| --- | --- |
| Claude Code | `~/.claude/agents/` |
| Cursor | `~/.cursor/agents/` |
| Codex | `~/.codex/agents/` |
| Grok Build | `~/.grok/agents/` for the definition and the model, `~/.grok/roles/` for read-only tools and the `effort` |
| pi | `~/.pi/agent/agents/` |

Each of those is a link into the checkout the hosts were installed from, so following one also tells you which checkout that is. A file still showing the old model means `install.sh` ran somewhere else.
