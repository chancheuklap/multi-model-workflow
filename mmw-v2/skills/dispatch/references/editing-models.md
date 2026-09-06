# Editing models.md

A `models.md` row is only correct on the machine it runs on, and none of what makes it correct can be answered from memory. Confirm what you are about to touch, write the row, then make it take effect.

## 1. Confirm a model or an `effort`

Which list to read depends on the row's `permissions`, and the two lists disagree.

A **`bypass`** row starts a Paseo session, so its name is Paseo's: `paseo provider models <host> --json`, which prints each model's id and its `thinkingOptionIds`. Write the `model` and `effort` cells from that. A name Paseo does not know is not refused — it is passed to the host, which may well accept it — but the Paseo app then shows the row as some other model, and the table, the profile and the screen stop agreeing (`fable` did this: Claude Code started Fable 5.1, the app displayed Opus 5).

A **`—`** row is a native subagent, so its name is the host's own command line's, and the table below is where to ask. Use the same list for both when the host has one name for both, which is what the `claude-…` ids do.

| Host | Ask it this |
| --- | --- |
| Cursor | `cursor-agent models` lists the command-line names, and the effort is burned into the slug there: no bare `cursor-grok-4.6`, the high-effort build is its own name. Paseo's list is the opposite shape — bare `grok-4.6` with `thinkingOptionIds` of its own — so a `bypass` row and a `—` row on this host never look alike. A subagent row's model must also be enabled in the Cursor account's model settings, or the subagent is never registered |
| pi | `pi --list-models` lists them. A name is `provider/id`, and the `effort` is the row's own column |
| Claude Code | `claude --help`, under `--model`: an alias for the newest of a family (`fable`, `opus`, `sonnet`) or a full model name. The aliases are Claude Code's alone — Paseo does not know them — so a `bypass` row writes the full name |
| Grok Build | `grok --help`, under `-m` and `--reasoning-effort`. Neither enumerates its values; `grok inspect` prints the configuration Grok has right now |
| Codex | Nothing lists them. `-m` takes the name as free text, and `~/.codex/config.toml` holds the `model` and `model_reasoning_effort` in use now |

## 2. Confirm a host

The host cell has to name a provider Paseo will start. Run `paseo provider ls` and take a row whose status is `available`. A name that is not on that list is refused and no session starts.

## 3. Make the edit take effect

Run `install.sh` from this repository:

```bash
bash mmw-v2/install.sh
```

That command is the whole of it. It rewrites every Agent profile whose `permissions` cell is `bypass`, reassembles every native subagent (`—`) into `agents/<name>/out/`, and points the host-side links at those files. The next session that starts that agent uses what you wrote.

## 4. Check that a row landed

A profile whose `notes` contain `from models.md` is one `install.sh` wrote: it is rewritten on every install and removed once its row is gone. A profile made by hand in the app keeps any other `notes` and is never touched.

## 5. What a row landed as

**A `bypass` row** is an Agent profile in `~/.paseo/config.json`, under `daemon.agentProfiles`: one entry whose `id` and `name` are both the agent cell, carrying the row's `model` and `thinkingOptionId`. Read that file, or run `bash mmw-v2/install.sh --check`, which compares each profile to the current row and exits 1 on drift, naming the agent.

**A `—` row** is a native subagent. Read the definition file for the agent you changed and confirm the new model is in it.

| Host | Where its agent definitions live |
| --- | --- |
| Claude Code | `~/.claude/agents/` |
| Cursor | `~/.cursor/agents/` |
| Codex | `~/.codex/agents/` |
| Grok Build | `~/.grok/agents/` for the definition and the model, `~/.grok/roles/` for read-only tools and the `effort` |
| pi | `~/.pi/agent/agents/` |

Each of those is a link into the checkout the hosts were installed from, so following one also tells you which checkout that is. A file still showing the old model means `install.sh` ran somewhere else.
