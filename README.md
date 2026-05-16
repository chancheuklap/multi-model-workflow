# multi-model-workflow

`multi-model-workflow` provides a post-design development workflow for agentic coding systems.

Codex runtime:

- repo-local skill: `.agents/skills/orchestrate-workflow/`
- versioned Codex agent templates: `codex/agents/*.toml`
- sync, install, and validation scripts: `codex/agents/sync-agents.sh`, `codex/skills/install-orchestrate-workflow.sh`, `codex/agents/validate-agents.py`
- optional hook scripts and installer under `codex/hooks/`

## Codex Install

From this repository:

```bash
python3 codex/agents/validate-agents.py
bash codex/agents/sync-agents.sh --dry-run
bash codex/agents/sync-agents.sh --apply
```

Restart Codex if updated agent instructions are not visible.

The repo-local skill is available when Codex runs from this repository or a subdirectory:

```text
.agents/skills/orchestrate-workflow/SKILL.md
```

To use the workflow from every project, install the skill into the user-level skills directory:

```bash
bash codex/skills/install-orchestrate-workflow.sh --user --dry-run
bash codex/skills/install-orchestrate-workflow.sh --user --apply
```

Only vendor the skill into a specific target repo when that repo should carry its own copy:

```bash
bash codex/skills/install-orchestrate-workflow.sh --target-repo /path/to/repo --dry-run
bash codex/skills/install-orchestrate-workflow.sh --target-repo /path/to/repo --apply
```

Do not keep duplicate copies of the same skill in repo-local, user-level, and plugin-installed locations at the same time. Duplicate skill names make invocation ambiguous.

## Codex Usage

Standard workflow:

```text
superpowers:brainstorming
  + grill-with-docs discovery capture when business context must be preserved
  -> CONTEXT.md + SPEC / design draft
  -> superpowers:writing-plans when an implementation plan is needed
  -> orchestrate-workflow
  -> superpowers:finishing-a-development-branch
```

`orchestrate-workflow` starts at discovery capture, design review, plan review, maintenance bug routing, or existing diff review. It handles:

- new-feature / systemic-bug discussion capture into `CONTEXT.md` and SPEC / design drafts
- Phase 0a design review
- Phase 0b plan review
- Task Pack planning and execution
- pack review and repair loops
- root-cause routing for maintenance bugs
- final intent verification
- release-risk review when migrations, billing, permissions, runtime, deploy, rollback, or cross-service contracts are involved
- business report

Runtime review contracts live in `.agents/skills/orchestrate-workflow/references/`. They tell the parent coordinator what to include in dispatch prompts for Codex `agent_type`s.

External engineering skills from `mattpocock/skills` are active upstream methods. Orchestrate routes to them for grill-with-docs discovery, feedback-loop diagnosis, vertical-slice TDD, prototype decisions, durable issue briefs, and architecture findings, then folds their outputs back into the Codex phases.

It does not automatically merge, push, or open PRs.

## Optional Hooks

To install them at user level:

```bash
bash codex/hooks/install-hooks.sh --dry-run
bash codex/hooks/install-hooks.sh --apply
```

Enable hooks with:

```toml
[features]
hooks = true
```

## Claude Install

The Claude Code package remains under `plugin/`.

```bash
claude --plugin-dir /path/to/multi-model-workflow/plugin
```

See `plugin/README.md` for Claude-specific agents and hooks.

## Development Checks

```bash
python3 codex/agents/validate-agents.py
bash -n codex/agents/sync-agents.sh
bash -n codex/skills/install-orchestrate-workflow.sh
bash -n codex/hooks/install-hooks.sh
python3 -m json.tool codex/hooks/hooks.json >/dev/null
find codex .agents/skills/orchestrate-workflow -type f -name '*.sh' -print -exec bash -n {} \;
UNSUPPORTED='codex:codex''-rescue|CLAUDE''_PLUGIN_ROOT|Subagent''Stop|subagent''_type:|disallowed''Tools|max''Turns|Skill'' tool'
rg -n "$UNSUPPORTED" codex .agents/skills/orchestrate-workflow
```

Pressure scenarios: `codex/smoke/method-pressure-scenarios.md`.
