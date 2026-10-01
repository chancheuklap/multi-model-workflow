# pstack names

For a session reading an imported pstack file that names a tool, a setting, a skill or a position this set does not have: find the name's row and read it as the row says.
**Import a component** adds the row for each such name a newly imported file uses.

| Written in a pstack file | Read it as |
| --- | --- |
| `mode: true`, `reminder` | No host here keeps a mode loaded for a whole session. The `mmw` skill takes its place, loaded by its description or by a prompt that names it. |
| **poteto-mode**, `/poteto-mode` | The `mmw` skill. |
| "your configured `<label>` model", a `<label>` row of `~/.cursor/rules/pstack-models.mdc` | A subagent started inside this session names no model and runs on this session's. For a role that needs a session of its own, the `dispatch` skill's `references/editing-models.md` says how to read which model it runs on. |
| The panel roles: `arena runners`, `architect runners`, `interrogate reviewers`, `arena cross-judge pool`, the judgment and tooling models | No counterpart yet. **Import a component** settles one when the first component that needs it is imported. |
| `Task` with `model`, `run_in_background` or `readonly` | Name no model. Whether a subagent can run in the background is your host's to offer. Read-only is one sentence of the brief, the one `references/subagent-brief.md` carries. |
| `subagent_type: "poteto-agent"`, `generalPurpose` | Your host's general-purpose subagent, briefed from `references/subagent-brief.md`. |
| "Spawn Comment Sicko" | Your host's general-purpose subagent, given that agent's brief. The brief arrives when **Import a component** imports the agent. |
| `AskQuestion` | With the user present, ask in the conversation. Unattended, do what the mode's `## Autonomy` says. |
| `/loop`, `/goal` | Your host's own loop command, where it has one. In a night the relay's wakes and the watchdog do that work. |
| cloud agent | A session of its own on this machine, started through the `dispatch` skill. |
| `agent-transcripts/`, `~/.cursor/projects/` | Your host's own session records. What another session can rely on is a `handoff` file, a pushed branch and the events on the tracker. |
| `the MCPs from the Cursor environment`, the `mcps/` directory | The MCP tools your host lists. |
| `create-skill` | The `writing-for-agents` skill. |
| `automate-me` | No counterpart yet. **Import a component** settles one when the first component that needs it is imported. |
| The control position: "the matching control skill", `control-ui`, `control-cli` | For a browser or a web UI, the `ui-acceptance` skill's oracles or a skill your host has that drives a browser; for a native window, a skill your host has that drives one; for a CLI, run the command yourself. When nothing can drive the surface, stop and say what is missing. |
| The delivery position: "Run **Opening a PR**" | Run **Deliver a change**. |
| The forge position: `gh`, `command -v origin`, `gt` | The tracker and the commands `docs/agents/issue-tracker.md` names. A `gh` command in an imported file agrees with it and stays as written. |
| The audit trail: "the **show-me-your-work** skill" | In a session bound to a ticket, the ticket's events and `Decisions I made on my own`. In any other session, your reply. |
| `/deslop` | No counterpart: write a `skip:` line for that step. |
| brain note | A Memory record, saved as the `implement` skill's `references/saving-memory.md` says. |
| "Rebase", "rebase onto clean trunk" | In a ticket's worktree, the `dispatch` skill's `bash scripts/dispatch.sh integrate <n>`: one merge, never a rebase. In any other session, as written. |
| "Binary-search the cause" | When the feedback loop is hard to build, the `diagnosing-bugs` skill. |
| The worktree convention | A worktree of your own goes under the main worktree's `.worktrees/`, under a name other than `issue-<n>`, `merge-<branch>` or `research-<n>`. A cleanup removes no worktree that carries one of those names. |
| Re-reading a playbook from trunk while a run is under way | Do not: a running session keeps the version it started with. |
