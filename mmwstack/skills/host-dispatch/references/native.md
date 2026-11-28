# Codex, Claude Code, and Cursor dispatch

Read the active host's section in `~/.agents/mmwstack-models.md` (or the supplied model rule file) before spawning.

| Role | Dispatch target | Notes |
| --- | --- | --- |
| `mmw-agent` (playbook delegates) | Native `mmw-agent` | Pass the step's configured model and settings. |
| `advisor` and `comment-sicko` | Native `advisor` or `comment-sicko` | Pass the role's configured model and settings. |
| General-purpose delegates (readers, reviewers, runners, judges) | Fresh subagent | Pass the role or seat model and settings. |

Native role registration lives in `.codex/agents/` for Codex, `.claude/agents/` for Claude Code, or `.cursor/agents/` for Cursor.
