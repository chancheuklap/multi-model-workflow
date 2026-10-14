# Set up MMW v4

In this chapter you install MMW v4 on a machine, check the install, learn how to go back to v3, choose a model for each role, and run a first task.

Installing is the owner's decision. Run every command below from the root of a checkout of this repository.

## Install the skills

Run:

```bash
bash mmw-v4/install.sh
```

The script points every host on the machine at this checkout's `mmw-v4/`. The hosts are Claude Code and Codex. Install puts these on the machine:

- **Skills.** Every directory under `mmw-v4/skills/` that has a `SKILL.md` gets a symbolic link in `~/.agents/skills` and in `~/.claude/skills`. Codex reads the first directory. Claude Code reads only the second.
- **Hooks.** The `dispatch` skill's `tool-guard.py` runs before each host calls a tool. In a session that works a ticket, which runs in the ticket's `issue-<n>` worktree with nobody at the screen, it refuses three things: closing the ticket by hand, putting a question on the screen, and ending a process. `turn-guard.py` runs each time a night's orchestrator ends its turn. It restarts the night's watchdog when the watchdog has stopped, so the night does not die quietly.
- **The user-level prompt.** `mmw-v4/prompt/shared.md` holds the facts about the owner that every session in every host reads. Claude Code reads it as `~/.claude/CLAUDE.md`, a link to the file. Codex reads an `AGENTS.md` that `prompt/render.py` writes.
- **A launchd task.** `com.mmw.prompt-sync` watches `shared.md` and writes the Codex copy again after each change.
- **Paseo and Orca settings.** Paseo gets its command link and its worktree root; install removes the Grok and Cursor providers an earlier install added. When Orca is present, it puts its worktrees under each repository's `.worktrees/`.
- **`~/.mmw/models.json`.** Install writes the default file, each role's `default` in `roles.json`, when none exists. In an existing file it changes only the role rows. It removes a row for a role that `roles.json` does not list, and keeps a `.bak-` copy first.

Last, install records this checkout's `mmw-v4/` in `~/.mmw/installed-root`.

If `render.py` refuses to overwrite Codex's `AGENTS.md`, the file is not one it wrote. This happens on the first install on a machine. Run `python3 mmw-v4/prompt/render.py --adopt` once. [`prompt/README.md`](../../prompt/README.md) explains the generated file.

A skill is a link, not a copy, so an edit to a `SKILL.md` reaches every host at its next call. Only the `description` in a skill's frontmatter needs a new session, because a host reads descriptions when it starts.

The header comment of [`install.sh`](../../install.sh) lists every item, and the items install leaves as v3 installed them.

## Check the install

Run:

```bash
bash mmw-v4/install.sh --check
```

The check changes nothing on disk. It exits with 0 when every item is in place, and with 1 when an item is missing or a leftover from an earlier install remains. When every hook is in place, it prints `HOOKS-INSTALLED`.

Run from a checkout other than the installed one, `--check` hands the check to the installed checkout's own `install.sh` and only reports. One frozen checkout serves the hosts, and work on MMW itself happens in other checkouts without touching it.

## Go back to v3

Run:

```bash
bash mmw-v4/install.sh --back
```

`--back` first removes or restores the items that v3 cannot recognise. For example, it brings back the `models.json` rows that v4 removed, from the `.bak-` copy. Then it runs `mmw-v3/install.sh` from the same checkout. The exit code is v3's.

Moving from v3 to v4 is the plain install, run once in the installed checkout. Skill links that v3 and v4 share move to `mmw-v4/`. A skill that only v3 has loses its link, so the two versions are never installed together; `--back` puts it back.

## Choose a model for each role

The `dispatch` skill starts sessions in six roles, listed in [`roles.json`](../../skills/dispatch/roles.json):

| Role | Sent with | Does |
| --- | --- | --- |
| `junior-worker` | a ticket | Works one ticket to closed: writes the code, runs the criteria, starts its reviewer. |
| `senior-worker` | a ticket | Works a ticket labelled `senior-worker`. |
| `reviewer` | a ticket | Reviews one ticket's diff on the `code-review` axes. |
| `researcher` | a brief | Reads one source or one angle of the code and hands back cited findings. |
| `candidate` | a brief | Designs one of several candidate answers to the same brief. |
| `advisor` | a brief | Gives a second opinion on one decision, on a stronger model. |

Each role is one row of `~/.mmw/models.json`. The row names the host (`claude` or `codex`), the model and the reasoning effort. The same file names the runner that starts the sessions.

Change the file only with `models.py config`:

```bash
python3 mmw-v4/skills/dispatch/scripts/models.py config show
python3 mmw-v4/skills/dispatch/scripts/models.py config set reviewer claude <model> high
python3 mmw-v4/skills/dispatch/scripts/models.py config runner auto
```

`config set` takes the role, the host, the model and the effort. `config runner` takes `orca`, `herdr`, `paseo` or `auto`. A change takes effect at the next session start, with no restart and no reinstall. [`editing-models.md`](../../skills/dispatch/references/editing-models.md) explains each command, how a host that puts the effort inside the model name works, and what each runner can observe.

Every role costs tokens. To spend fewer, put the roles that write code on a cheaper, faster model, and keep a strong model for `reviewer` and `advisor`.

The main session, the one you type into, is not a row. It runs on whatever model you chose in that host.

## Set up each repository

Install sets up the machine. Each repository MMW works in is set up once more, by the [setup-mmw](../../skills/setup-mmw/SKILL.md) skill. Ask a session in that repository to set it up. The skill checks the repository first and writes nothing for that check. Then it creates the pipeline's labels on GitHub, adds `.worktrees/` and `.scratch/` to `.gitignore`, gives the repository its `scripts/check`, the one command that runs its checkers and tests and that every ticket must pass before it lands, writes `TESTING.md` from the tests the repository has, commits and pushes. It stops before any of that when the repository's issues are not on GitHub. Run it again at any time as a check-up; it keeps what is already there.

## Run your first task

Open a new session in a repository, after the install. Pick something real but small, and describe it the way you would to a colleague:

```text
add a --json flag to this command. text output stays byte-identical. verify both.
```

The session reads `mmw-mode` before anything else, matches the request to a playbook, here the Feature playbook, and works through its steps.

Next: [Route work through `mmw-mode`](./02-mmw-mode.md).
