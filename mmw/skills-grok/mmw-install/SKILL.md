---
name: mmw-install
description: Install MMW on this machine and configure this repo. Use on a new machine, a new repo, when the user says set this repo up or install MMW, when `mmw` is missing, or after an MMW upgrade. Not for day-to-day work.
---

# Install

Two jobs, in this order. Install once per machine. Configure once per repo. A new machine needs both. A new repo on an already-installed machine needs only configure.

Each step is idempotent. Skip what is already done. Re-running is safe.

## 1. Install on this machine

```bash
command -v mmw && mmw --version
```

If that prints a version, go to step 2.

```bash
cd <MMW source repo>
bash mmw/install.sh
```

`install.sh` installs the CLI, skills, agents, MCP servers, and editor diagnostics for every host already on this machine. After it finishes, restart the host or open a new session.

Needs `git`, `python3`, `jq`, and `node`. `install.sh` names whatever is missing.

## 2. Configure this repo

In the target repo:

```bash
mmw init
```

This writes the repo's MMW config and commits it on the current branch. Toolchain files match the languages this repo actually uses.

## 3. Install missing tools

```bash
mmw toolchain detect
```

Each missing line ends with the install command. To have MMW run them:

```bash
mmw toolchain install          # list only
mmw toolchain install --yes    # install after the user agrees
```

Show the list. Wait for the user to agree before `--yes`. These commands install into the machine or the workspace.

Run `mmw toolchain detect` again. The pending line should be none.

## 4. Hosts that ask the user to trust hooks

If this host prompts to trust plugin hooks in an interactive session, tell the user to open one interactive session and accept once. Non-interactive runs do not prompt and do not run the hooks.

After every MMW upgrade the prompt comes back: the trust hash includes the expanded plugin path, and that path contains the version.

Do not edit the host's trusted-hash config.

## 5. Hosts that also load other agents' user-level skills

If this machine has Cursor, the user does three things. Only the user can do them:

1. In App settings, turn off Include third-party Plugins, Skills, and other configs. The main agent then loads only this host's own skills and MCP. CLI workers are isolated by `mmw-cursor-agent` and do not depend on this setting.
2. Raise `cursor.worktreeMaxCount` above the default 25. This host recycles trees under `~/.cursor/worktrees/`. A low cap deletes trees that are still in use.
3. Set the Agents Window orchestrator model to grok, matching the installed runtime. CLI worker models come from `mmw-cursor-agent --mmw-role`. Leave the user's own default model in `cli-config.json` as it is.

## Done

- Installed hosts can use MMW skills and agents.
- Saving a file reports diagnostics for that file. Installed hosts share one rules table.
- CI uses the same rules table and the same checkers.

How diagnostics and CI stay aligned, how to change the rules table, and who owns which config: run `mmw toolchain` for usage, then read the header of `config/toolchain-rules.json`.
