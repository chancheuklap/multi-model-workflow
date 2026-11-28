---
status: accepted
date: 2026-11-28
issue: https://github.com/chancheuklap/multi-model-workflow/issues/1722
---

# Antigravity 1.00x default-agent dispatch and progressive host-dispatch skill

## Context

Starting in Antigravity CLI `1.5.17`, Antigravity bills custom agents (`.agents/agents/*`, `~/.gemini/config/agents/*`, plugin `agents/*` directories, and their subagents) at a higher token quota rate (`4.00x` community-measured multiplier in `google-antigravity/antigravity-cli#1890`), while default and built-in agents remain at `1.00x`.

`mmwstack` previously instructed Antigravity setups to create `.agents/agents/*.md` and invoke `scripts/agy-delegate --agent <name> --model-role <role>`. That setup incurred 4x quota billing on every delegated custom-agent trajectory and persisted `.agents/agents/` references in Antigravity's conversation SQLite metadata so resumed sessions kept drawing 4x quota.

At the same time, the earlier `mmw-mode` host-dispatch reference packed all five host platforms and 2,500 words of Herdr lifecycle internals into one 19 KB document while omitting how to pass task prompts (`<<'EOF'` stdin heredoc or `--prompt-file`) and `--issue`. Splitting separate `--agent` and `--model-role` flags alongside incomplete examples produced 34 `agy-delegate --help` calls in Home Repo logs across nine days.

## Decision

1. **Replace the monolithic `mmw-mode` host-dispatch reference with a 3-layer progressive internal skill, [host-dispatch](../../mmwstack/skills/host-dispatch/SKILL.md).**
   - Layer 1 (`SKILL.md`) holds the cross-host delegation contract and a 3-branch router table pointing one level deep to `references/agy.md`, `references/droid.md`, and `references/native.md`, instructing each agent to read only its own host reference.
   - Layer 2 (`references/agy.md`) provides an action-first daily cheat sheet with copy-pasteable `scripts/agy-delegate --role` commands (`<<'EOF'` stdin heredoc, `--prompt-file`, `--prompt`, `--add-dir`, auto-inferred `--issue`, `--resume`, `close`), the unified `--role` derivation table, rare overrides, explicit 4x custom-agent redlines, and cloud fallback via built-in `invoke_subagent(TypeName="self")` (or `research` for read-only roles) plus reading `agents/<role>.md`.
   - Layer 3 (`references/agy-lifecycle.md`) holds Herdr lifecycle classes, `--lifecycle auto` precedence, `turn_token` settlement, live-terminal `--resume` reuse (plus the legacy 4x DB fail-fast guard), explicit `close` commands, and failure cleanup internals, loaded only when debugging those paths.
2. **Route all delegating callers directly to `host-dispatch`.** `AGENTS.md`, `mmw-mode/SKILL.md#subagents`, playbooks, delegating skills, and the routing glossary link directly to `host-dispatch/SKILL.md` so direct skill calls work even when `mmw-mode` is skipped.
3. **Remove AGY custom-agent setup guidance while keeping `mmwstack/agents/*.md` canonical.** Setup docs (`01-setup.md`, `setup-mmwstack`, `mmw-help`, `mmwstack/README.md`) prohibit `.agents/agents/*.md`, `~/.gemini/config/agents/*.md`, and installing `mmwstack` as an AGY plugin exposing `mmwstack/agents/`. `scripts/agy-delegate --role` injects `mmwstack/agents/*.md` prompts on the `1.00x` default agent and enforces tool restrictions via `PreToolUse` hooks, while Codex, Claude Code, Cursor, and Factory Droid keep using `mmwstack/agents/*.md` for their native registrations.

## Consequences

- Every host session reads only its own dispatch rules (`~20` lines for the router plus `~40` lines for daily AGY calls) instead of loading 19 KB of cross-host and Herdr internals, aligning with [ADR 0001](0001-single-entry-routing-to-protect-operator-attention.md).
- Antigravity setups avoid 4x custom-agent and plugin-agent billing while keeping unified `--role` prompt injection, exact model routing, and `PreToolUse` tool boundaries.
- Changing any host's dispatch rules updates only that host's reference file under `mmwstack/skills/host-dispatch/references/`.
