# multi-model-workflow

`multi-model-workflow` is the Codex source and sync repository for the
Plugin V2 shaped Orchestrate Workflow runtime.

Current Codex runtime source:

- repo-local skills: `.agents/skills/orchestrate-*`
- Codex agent templates: `codex/agents/*.toml`
- skill install scripts: `codex/skills/`
- hook install scripts: `codex/hooks/`
- external reviewer helpers: `codex/reviewers/`

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

Subscription-backed Claude review is automated through the non-`-p` runner:

```bash
bash codex/reviewers/claude-subscription-review.sh \
  --prompt-file .codex/multi-model-workflow/review-prompts/<gate>.md \
  --output .codex/multi-model-workflow/review-results/<gate>-claude.md \
  --review-name <gate>
```

The runner invokes ordinary `claude` with stdin and read-only tools; it does not
use `-p/--print`. Claude review is fixed to `claude-opus-4-7` with
`--effort high`. When an active Orchestrate budget file exists, successful
review calls are recorded in `budget_used` and the dispatch ledger.

`codex/reviewers/claude-review.sh` exists only as an explicitly authorized
Agent SDK / Extra Usage fallback and refuses to run without `--allow-extra-usage`.

## Verification

After applying runtime changes:

```bash
bash -n codex/skills/install-orchestrate-runtime.sh
bash -n codex/skills/install-orchestrate-workflow.sh
bash -n codex/agents/sync-agents.sh
bash -n codex/hooks/install-hooks.sh
bash -n codex/hooks/session-start.sh
bash -n codex/hooks/guard-premature-push.sh
bash -n codex/hooks/track-review-budget.sh
bash -n codex/reviewers/claude-subscription-review.sh
bash -n codex/reviewers/claude-review.sh
python3 -m json.tool codex/hooks/hooks.json >/dev/null
diff -qr .agents/skills/orchestrate-workflow ~/.agents/skills/orchestrate-workflow
diff -qr .agents/skills/orchestrate-discovery ~/.agents/skills/orchestrate-discovery
diff -qr .agents/skills/orchestrate-plan-writing ~/.agents/skills/orchestrate-plan-writing
diff -qr .agents/skills/orchestrate-execution ~/.agents/skills/orchestrate-execution
diff -qr .agents/skills/orchestrate-final-review ~/.agents/skills/orchestrate-final-review
diff -qr .agents/skills/orchestrate-multi-pr-merge ~/.agents/skills/orchestrate-multi-pr-merge
for f in codex/agents/*.toml; do diff -q "$f" "$HOME/.codex/agents/$(basename "$f")"; done
```

## Historical Claude Sources

`plugin-v2/` remains the Claude Code Plugin V2 source that shaped this Codex
runtime. `plugin/` is the older Claude plugin compatibility tree. Current Codex
behavior is defined by `.agents/skills/`, `codex/agents/`, and `codex/hooks/`.
