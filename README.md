# multi-model-workflow

`multi-model-workflow` is the Codex source and sync repository for the
Plugin V2 shaped Orchestrate Workflow runtime.

Current Codex runtime source:

- repo-local skills: `.agents/skills/orchestrate-*`
- runtime source manifest: `codex/README.md`
- Codex agent templates: `codex/agents/*.toml`
- skill install scripts: `codex/skills/`
- hook install scripts: `codex/hooks/`

The previous Codex V1 source is archived in
`archive/2026-05-20-codex-v1/` and is not a runtime authority.

## Runtime Shape

The Codex system follows Plugin V2's phase split:

```text
orchestrate-workflow
  -> orchestrate-discovery
  -> orchestrate-plan-writing
  -> orchestrate-execution
  -> orchestrate-final-review
  -> orchestrate-workflow Closing
```

Route 2 handles unknown bugs through `root_cause_analyst`. Route 3 handles
multi-PR merge work through `orchestrate-multi-pr-merge`.

## Codex Install

Install or refresh the six Orchestrate skills:

```bash
bash codex/skills/install-orchestrate-runtime.sh --user --dry-run
bash codex/skills/install-orchestrate-runtime.sh --user --apply
```

Install or refresh the custom Codex agents and register managed agent types:

```bash
bash codex/agents/sync-agents.sh --dry-run --update-config
bash codex/agents/sync-agents.sh --apply --update-config
```

Install optional user-level hooks:

```bash
bash codex/hooks/install-hooks.sh --dry-run
bash codex/hooks/install-hooks.sh --apply
```

Enable hooks in `~/.codex/config.toml`:

```toml
[features]
hooks = true
```

Restart Codex if newly registered agent types are not visible in the current
session.

## Managed Agent Types

| agent_type | Role |
| --- | --- |
| `plan_writer` | Writes reviewed-design + issue-backed implementation plans |
| `coding_worker` | Normal Task Pack execution and clear repair findings |
| `complex_coding_worker` | High-risk implementation: migration, billing, permissions, runtime, shared contracts |
| `code_reviewer` | Baseline design, plan, pack, final, direct repair, and integration review |
| `release_reviewer` | Release-risk supplement; never replaces baseline review |
| `code_explorer` | Narrow read-only code lookup |
| `complex_code_explorer` | Multi-module read-only investigation |
| `root_cause_analyst` | Unknown bug, repair truncation, and systemic PR conflict investigation |
| `docs_worker` | Low-risk documentation cleanup |

## External Claude Review

Codex must not default to `claude -p` when the goal is to spend normal Claude
subscription usage. `claude -p` / Agent SDK usage is a separate credit path, not
the interactive subscription pool.

All reviews are dispatched through Codex `codex-companion.mjs` using the
four-step protocol documented in
`orchestrate-workflow/references/external-review-lanes.md`.

## Verification

After applying runtime changes:

```bash
bash -n codex/skills/install-orchestrate-runtime.sh
bash -n codex/agents/sync-agents.sh
bash -n codex/hooks/install-hooks.sh
bash -n codex/hooks/session-start.sh
bash -n codex/hooks/guard-premature-push.sh
bash -n codex/hooks/track-review-budget.sh
bash -n codex/hooks/cleanup-run-state.sh
python3 -m json.tool codex/hooks/hooks.json >/dev/null
diff -qr .agents/skills/orchestrate-workflow ~/.agents/skills/orchestrate-workflow
diff -qr .agents/skills/orchestrate-discovery ~/.agents/skills/orchestrate-discovery
diff -qr .agents/skills/orchestrate-plan-writing ~/.agents/skills/orchestrate-plan-writing
diff -qr .agents/skills/orchestrate-execution ~/.agents/skills/orchestrate-execution
diff -qr .agents/skills/orchestrate-final-review ~/.agents/skills/orchestrate-final-review
diff -qr .agents/skills/orchestrate-multi-pr-merge ~/.agents/skills/orchestrate-multi-pr-merge
for f in codex/agents/*.toml; do diff -q "$f" "$HOME/.codex/agents/$(basename "$f")"; done
diff -q codex/hooks/cleanup-run-state.sh ~/.codex/hooks/multi-model-workflow/cleanup-run-state.sh
python3 -m json.tool ~/.codex/hooks.json >/dev/null
```

## Historical Claude Sources

`plugin-v2/` remains the Claude Code Plugin V2 source that shaped this Codex
runtime. `plugin/` is the older Claude plugin compatibility tree. Current Codex
behavior is defined by `.agents/skills/`, `codex/agents/`, and `codex/hooks/`.
