# Codex Orchestrate Migration Audit - 2026-05-25

## Scope

This audit checks whether `codex-orchestrate/` is a complete Codex-native replication of the Claude Code baseline in `plugin/`, and whether the installed Codex runtime matches the source package.

The `plugin/` directory was used as a read-only behavior baseline. No files under `plugin/` were modified.

## Replication Surface

The high-level source surface is complete for the portable workflow contract:

| Surface | Claude baseline | Codex source | Result |
| --- | ---: | ---: | --- |
| `skills/` files | 53 | 53 | Matched |
| `state-schema/` files | 4 | 4 | Matched |
| `build/templates/` files | 11 | 11 | Matched |
| `build/resolvers/` files | 11 | 11 | Matched |
| `build/tests/` files | 10 | 10 | Matched |

The intentional host-specific differences are:

| Claude baseline only | Codex-native replacement |
| --- | --- |
| `.claude-plugin/plugin.json` | `.codex-plugin/plugin.json` |
| Markdown agent files under `agents/*.md` | Codex TOML agents under `agents/*.toml` |
| `hooks/hooks.json` | root `hooks.json` declared by the Codex manifest |
| external review command hooks and companion review runner | native `codex_reviewer` subagent dispatch via `spawn_agent`, `send_input`, and `wait_agent` |
| Claude hook tests for removed command hooks | Codex hook tests for envelope parsing, SubagentStart effort tracking, SubagentStop return handling, and idempotency |

Codex-only files added by the migration are runtime wiring and verification files: `agents/sync-agents.sh`, `scripts/validate-plugin-contract.sh`, `scripts/verify-runtime-parity.sh`, `scripts/validate-review-dispatch.sh`, `scripts/record-pack-dispatch.sh`, `scripts/validate-route-worker-dispatch.sh`, and `scripts/record-route-worker-dispatch.sh`.

## Findings Fixed

### 1. Hook Manifest Validation Used A Stale Validator

The generic plugin validator rejected the official Codex `hooks` manifest field. The source verification path now uses `scripts/validate-plugin-contract.sh`, which validates `.codex-plugin/plugin.json` and the referenced root `hooks.json` directly.

Relevant source changes:

- `README.md`
- `AGENTS.md`
- `codex-orchestrate/scripts/validate-plugin-contract.sh`
- `codex-orchestrate/scripts/verify-maturity.sh`

### 2. Runtime Parity Was Not Enforced

Source changes did not prove the installed runtime had updated plugin cache, custom agent TOML, agent registrations, or hook trust records. The new `scripts/verify-runtime-parity.sh` checks all four.

Runtime repair completed:

- `codex plugin add multi-model-workflow@multi-model-workflow`
- `bash codex-orchestrate/agents/sync-agents.sh --apply --update-config`
- Added the installed `subagent_stop:0:0` hook current hash to `~/.codex/config.toml`

Current runtime result: `Runtime parity passed`.

### 3. Route 2, Route 3, And Direct Repair Worker Dispatch Were Under-Adapted

Formal execution Pack workers had `DISPATCH_ENVELOPE`, `validate-pack-dispatch.sh`, execution-state checks, durable return handling, and `agent_id` persistence. The non-execution coding worker paths did not have an equivalent Codex-native gate.

The fixed contract is:

| Worker lane | Dispatch gate | State model | Return model |
| --- | --- | --- | --- |
| Formal execution Pack | `validate-pack-dispatch.sh` | `execution-state-<run_id>.json` | run-scoped `pack-returns/<run_id>/<pack-id>.json` consumed by `SubagentStop` |
| Route worker for Bug Investigation, Direct Repair, Multi-PR conflict repair, hotfix, quickfix, spike, maintenance | `validate-route-worker-dispatch.sh` | `workflow-state-<run_id>.json` with idempotency key | `wait_agent` final message saved by Coordinator |

`record-route-worker-dispatch.sh` persists route worker `agent_id` so follow-up repair must use `send_input` to the original worker. Missing `agent_id` is now a BLOCKED condition, not a reason to create a replacement worker.

### 4. Non-Formal Review Routes Had No Model Tier

The review dispatch template only selected models for formal phases. It now routes non-formal review phases to `gpt-5.4` with `xhigh` effort:

- `bug-investigation`
- `direct-repair`
- `multi-pr-merge`
- `hotfix`
- `quickfix`
- `maintenance`

### 5. Route Budget Semantics Were Inconsistent

Route 2 and Route 3 previously said they skipped budget while still using review dispatch validation, effort tracking, and run summaries. They now use an `unlimited` workflow-state budget, while only the formal route uses the bounded `3P + 12` plan-count budget.

Direct Repair converts the existing pending formal workflow-state into `route = "direct-repair"` with `budget_status = "unlimited"` before worker/review dispatch.

## Validation Evidence

The following commands passed after the fixes:

```bash
bash codex-orchestrate/build/build.sh --check --plugin-dir codex-orchestrate
bash codex-orchestrate/scripts/validate-plugin-contract.sh codex-orchestrate
bash codex-orchestrate/scripts/run-all-tests.sh
bash codex-orchestrate/scripts/verify-maturity.sh
bash codex-orchestrate/scripts/verify-runtime-parity.sh codex-orchestrate
git diff --check
```

Observed results:

| Gate | Result |
| --- | --- |
| Build check | Passed |
| Plugin contract validation | Passed |
| Full test runner | 27 suites passed |
| Maturity verification | 106 checks passed |
| Runtime parity | Passed |
| Git whitespace check | Passed |

## Residue Classification

The remaining `Claude` / `.claude` text in `codex-orchestrate/` is intentional context, not executable residue:

| Location type | Classification |
| --- | --- |
| `README.md` and `AGENTS.md` descriptions of `plugin/` | Required because `plugin/` remains the read-only Claude Code baseline |
| `architecture-draft.md` comparison table | Required migration decision record |
| Negative phrases such as `codex-companion` / `job-id polling` | Required Codex-native prohibition |

No active Codex agent, skill, hook, script, schema, build template, or runtime-installed file still depends on Claude Code tool names, `.claude/` state paths, `CLAUDE_PLUGIN_ROOT`, external companion review runners, or `hooks/hooks.json`.

## Current State

The Codex source package and installed runtime are aligned:

- plugin cache matches `codex-orchestrate/`
- user-level agent TOML matches `codex-orchestrate/agents/`
- all managed agent types are registered in `~/.codex/config.toml`
- all plugin hooks, including `subagent_stop:0:0`, have persisted trust records

The remaining source differences from `plugin/` are either intentional Codex host replacements or Codex-only verification/runtime wiring.
