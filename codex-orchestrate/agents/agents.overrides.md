# agents override

- Codex agent source files in this directory are TOML role configs, not old-host Markdown frontmatter files.
- Keep agent_type names underscore-based: `pack_executor`, `complex_pack_executor`, `plan_writer`, `root_cause_analyst`, `code_explorer`, `complex_code_explorer`, `docs_worker`.
- Agent instructions must be self-contained for Codex and must not mention old-host runtime files, old agent memory paths, old dispatch tool names, or old message-resume APIs.
- `sync-agents.sh` is the runtime parity path for this directory; changes to TOML templates must remain copyable into `${CODEX_HOME:-$HOME/.codex}/agents` and registerable through `[agents.<name>]` config entries.
