# Codex Agent Templates

The Codex runtime mirrors Plugin V2's role model, with Codex-native `agent_type`
names and models.

## Install

```bash
bash codex/agents/sync-agents.sh --dry-run --update-config
bash codex/agents/sync-agents.sh --apply --update-config
```

`--apply` copies templates into `~/.codex/agents/`. `--update-config` registers
the managed `[agents.<name>]` entries in `~/.codex/config.toml`.

## Managed Agents

| agent_type | Template | Role |
| --- | --- | --- |
| `plan_writer` | `plan-writer.toml` | Write issue-backed implementation plans from reviewed designs |
| `coding_worker` | `coding-worker.toml` | Normal Task Pack execution and clear repair findings |
| `complex_coding_worker` | `complex-coding-worker.toml` | High-risk implementation, migrations, billing, permissions, runtime, shared contracts |
| `code_reviewer` | `code-reviewer.toml` | Baseline review for design, plan, pack, final, direct repair, multi-PR integration |
| `release_reviewer` | `release-reviewer.toml` | Release-risk gate, never a baseline review replacement |
| `code_explorer` | `code-explorer.toml` | Narrow read-only code lookup |
| `complex_code_explorer` | `complex-code-explorer.toml` | Multi-module read-only investigation |
| `root_cause_analyst` | `root-cause-analyst.toml` | Unknown bug, repair truncation, and systemic multi-PR conflict investigation |
| `docs_worker` | `docs-worker.toml` | Low-risk documentation cleanup and structured synthesis |

## Dispatch Contract

- Parent dispatch is self-contained: phase, source artifacts, owned files, anchors, verification, pass condition, and return format.
- Sub-agents do not rely on Orchestrate `SKILL.md` or references unless the parent provides exact paths or pasted text.
- Workers do not commit, merge, push, or open PRs.
- Reviewers and explorers are read-only by role discipline.
- `release_reviewer` only runs after a baseline review pass or when a release strategy must be decided before continuing.
