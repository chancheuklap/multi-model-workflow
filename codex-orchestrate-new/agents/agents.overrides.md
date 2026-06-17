# agents override

- Codex agent source files in this directory are TOML role configs.
- Keep agent_type names underscore-based: `pack_executor`, `complex_pack_executor`, `plan_writer`, `codex_reviewer`, `codex_planning_reviewer`, `root_cause_analyst`, `code_explorer`, `complex_code_explorer`.
- Agent instructions must be self-contained for Codex and must not depend on parent skill context implicitly.
- Required sub-agent skills belong in each TOML via `[[skills.config]]`; developer instructions must say exactly when to call each bound skill. Do not rely on parent-thread skill context for TDD, diagnosis, architecture, Ponytail, or frontend validation behavior.
- `sync-agents.sh` is the runtime parity path for this directory; changes to TOML files must remain copyable into `${CODEX_HOME:-$HOME/.codex}/agents` and registerable through `[agents.<name>]` config entries.
- Review work is owned by Codex reviewer subagents: `codex_planning_reviewer` for Discovery / Plan Review, `codex_reviewer` for execution, final review, direct repair, bug investigation, multi-PR merge and ad-hoc review. Do not add script runners or external companion commands for review.
- Repair-capable agents must return regression evidence or an explicit manual validation gate, and must not add low-value implementation-detail tests just to satisfy review findings.
