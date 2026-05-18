# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A multi-model development workflow system that ships as both a **Claude Code plugin** (`plugin/`, `plugin-v2/`) and **Codex skills + agents** (`.agents/skills/`, `codex/agents/`). It orchestrates specialized sub-agents for coding, investigation, and cross-model review through a phased pipeline: Discovery → Design Review → Plan → Plan Review → Task Pack Execution → Final Intent Verification → Business Report.

The Codex runtime (`codex/agents/*.toml`, `.agents/skills/orchestrate-*/`) is the design authority. The Claude Code plugin (`plugin/`) is a compatibility layer. `plugin-v2/` is the next-generation Claude plugin under development.

## Repository Layout

```
.agents/skills/
  orchestrate-discovery/    # Codex skill: turns inputs into design documents
  orchestrate-plan-writing/ # Codex skill: generates issue-backed implementation plans
  orchestrate-workflow/     # Codex skill: main coordinator (Phase 0a → Phase C)

codex/
  agents/*.toml             # Codex custom agent definitions (7 roles)
  agents/sync-agents.sh     # Syncs agent TOMLs to ~/.codex/agents/
  hooks/                    # Codex user-level hooks (session-start, guard-premature-push)
  skills/install-orchestrate-workflow.sh  # Installs skills to user-level

plugin/                     # Claude Code plugin v1 (v0.7.0)
  .claude-plugin/plugin.json
  agents/                   # 6 agent definitions (.md files)
  hooks/                    # hooks.json + session-start.sh
  scripts/                  # guard-premature-push.sh

plugin-v2/                  # Claude Code plugin v2 (v0.8.0, in development)
  .claude-plugin/plugin.json
  agents/                   # Restructured agent definitions
  hooks/                    # Extended hooks (track-review-budget.sh)
  references/               # Shared reference docs (contract-boundary, dispatch-primitives, etc.)
  scripts/

.claude-plugin/marketplace.json  # Marketplace listing manifest
```

## Key Concepts

**Source → Runtime distinction**: `.agents/skills/` and `codex/agents/*.toml` are source. After `sync-agents.sh` and `install-orchestrate-workflow.sh`, the runtime lives at `~/.codex/agents/` and `~/.agents/skills/`. Always edit source first, then sync to runtime.

**Phases**: 0a (design review) → 0b (plan review) → A (Task Pack execution + pack review) → B (final intent verification) → C (business report). Each phase has reference docs under `references/`.

**Sub-agent isolation**: Sub-agents cannot read `SKILL.md` or `references/`. Every dispatch prompt must be self-contained with phase, source docs, anchors, verification commands, and return contract.

**Review budget**: Formal Orchestrate runs have a capped review dispatch budget (`2N + 16` where N = pack count). The 80% threshold triggers a Direction Check.

**Contract boundaries**: Cross-boundary changes (API, Pydantic, DB, JSON payload, task/sync, business catalog, external adapter, UI form) require explicit contract anchors in dispatch prompts.

## Sync Commands

After editing Codex source files:

```bash
# Sync skills to user-level
bash codex/skills/install-orchestrate-workflow.sh --user --apply

# Sync agent TOMLs
bash codex/agents/sync-agents.sh --apply

# Sync hooks
bash codex/hooks/install-hooks.sh --apply

# Verify sync (diff should be empty)
diff -qr .agents/skills/orchestrate-workflow ~/.agents/skills/orchestrate-workflow
diff -qr .agents/skills/orchestrate-discovery ~/.agents/skills/orchestrate-discovery
diff -qr .agents/skills/orchestrate-plan-writing ~/.agents/skills/orchestrate-plan-writing
```

Use `--dry-run` instead of `--apply` to preview changes.

## Agent Roles

### Codex agents (`codex/agents/*.toml`)

| Agent | Model | Role |
|-------|-------|------|
| `coding_worker` | gpt-5.3-codex | Normal Task Pack, test fix, local refactor |
| `complex_coding_worker` | gpt-5.5 | High-risk packs (migration, billing, auth, permissions) |
| `code_reviewer` | gpt-5.4 | Baseline review (all phases) |
| `release_reviewer` | gpt-5.5 | Release-risk gate only |
| `code_explorer` | gpt-5.3-codex | Narrow file/symbol lookup (read-only) |
| `complex_code_explorer` | gpt-5.4 | Multi-module investigation (read-only) |
| `docs_worker` | gpt-5.4 | Low-risk docs cleanup |

### Claude Code agents (`plugin/agents/`, `plugin-v2/agents/`)

| Agent | Model | Role |
|-------|-------|------|
| `plan-writer` | Opus 4.7 (1M) | Plan writing from design + issues |
| `pack-executor` | Sonnet | Normal TDD coding + review fix |
| `complex-pack-executor` | Opus | High-risk coding |
| `code-explorer` | Sonnet | Narrow-scope investigation (read-only) |
| `complex-code-explorer` | Opus | Multi-module investigation (read-only) |
| `root-cause-analyst` | Opus | Unknown root cause investigation + fix |
| `docs-worker` | Sonnet | Documentation cleanup |

## Editing Guidelines

- **Runtime files** (SKILL.md, references/, agent TOMLs, hooks) only contain executable instructions — no background explanations, migration history, method-name lists, or README-style intros.
- **Reference docs** are read by the coordinator at specific phases; sub-agents never see them directly.
- **Agent TOMLs** must include a self-contained return contract; never reference SKILL.md or references the agent can't access.
- After editing any source, sync to runtime and verify with `diff`.
- When modifying `plugin-v2/`, keep `agents.overrides.md` in the folder in sync.

## Common Validation

```bash
# Check for leaked references to old plugin concepts in Codex runtime
rg -n "workflow-auditor|pack-executor|root-cause-analyst|codex-rescue|SendMessage|Agent tool" .agents/skills codex/agents

# Verify no stale cross-references
rg -n "SKILL.md universal|Fill the.*SKILL.md" .agents/skills codex/agents
```

## Install (Claude Code Plugin)

```bash
claude plugin install multi-model-workflow@multi-model-workflow
# or load from local path:
claude --plugin-dir /path/to/multi-model-workflow/plugin
```

Requires the [Codex plugin](https://github.com/anthropics/claude-code-plugins) for cross-model review dispatch via `codex:codex-rescue`.
