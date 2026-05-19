# Codex Runtime Source

This directory contains only the source files that install or sync the Codex
runtime for Orchestrate Workflow.

| Path | Runtime role |
| --- | --- |
| `agents/*.toml` | Custom `agent_type` templates copied into `~/.codex/agents/`. |
| `agents/sync-agents.sh` | Installs agent templates and can register managed agent types in `~/.codex/config.toml`. |
| `skills/install-orchestrate-runtime.sh` | Installs the six Orchestrate skills from `.agents/skills/orchestrate-*`. |
| `hooks/hooks.json` | Source hook manifest. The installer rewrites commands to user-level hook paths. |
| `hooks/*.sh` | User-level hook scripts and hook helpers copied into `~/.codex/hooks/multi-model-workflow/`. |
| `reviewers/*.sh` | External reviewer runners used by Orchestrate review lanes. |
| `agents.overrides.md` and nested `agents.overrides.md` files | Directory-local maintenance rules that must stay in sync with these runtime sources. |

Archived Codex V1 source lives under `archive/2026-05-20-codex-v1/` and does
not define current runtime behavior.
