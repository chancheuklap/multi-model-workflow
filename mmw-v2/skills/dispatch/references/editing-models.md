# Editing models.md

A `models.md` row is only correct on the machine it runs on, and none of what makes it correct can be answered from memory. Confirm what you are about to touch, write the row, then make it take effect.

## 1. Confirm a model or an `effort`

Every row starts a Paseo session, so its name is Paseo's: `paseo provider models <host> --json`, which prints each model's id and its `thinkingOptionIds`. Write the `model` and `effort` cells from that and from nothing else. A host's own command line usually has a second set of names for the same models — Claude Code's family aliases (`fable`, `opus`, `sonnet`), Cursor's effort burned into the slug (`cursor-grok-4.6-high` rather than a bare `grok-4.6` with `thinkingOptionIds`) — and Paseo knows none of them.

A name Paseo does not know is not refused: it is passed to the host, which may well accept it. What breaks is agreement. The Paseo app then shows the row as some other model, and the table, the profile and the screen stop matching (`fable` did this: Claude Code started Fable 5.1, the app displayed Opus 5).

## 2. Confirm a host

The host cell has to name a provider Paseo will start. Run `paseo provider ls` and take a row whose status is `available`. A name that is not on that list is refused and no session starts.

## 3. Make the edit take effect

Run `install.sh` from this repository:

```bash
bash mmw-v2/install.sh
```

That command is the whole of it. It rewrites every Agent profile in `~/.paseo/config.json` from this table. The next session that starts that agent uses what you wrote.

## 4. Check that a row landed

A profile whose `notes` contain `from models.md` is one `install.sh` wrote: it is rewritten on every install and removed once its row is gone. A profile made by hand in the app keeps any other `notes` and is never touched.

## 5. What a row landed as

A row is an Agent profile in `~/.paseo/config.json`, under `daemon.agentProfiles`, carrying the row's `model` and `thinkingOptionId`. The first `bypass` row for an agent has `id` and `name` both equal to the agent cell. A later `bypass` row for the same agent is a fallback host: `id` and `name` are `{agent}@{host}` (`junior-worker@grok` for `junior-worker` on `grok`). Read that file, or run `bash mmw-v2/install.sh --check`, which compares each profile to the current row and exits 1 on drift, naming the profile id.
