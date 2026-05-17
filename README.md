# multi-model-workflow

`multi-model-workflow` provides a post-design development workflow for agentic coding systems.

Codex runtime:

- repo-local skills: `.agents/skills/orchestrate-workflow/`, `.agents/skills/orchestrate-plan-writing/`
- versioned Codex agent templates: `codex/agents/*.toml`
- sync and install scripts: `codex/agents/sync-agents.sh`, `codex/skills/install-orchestrate-workflow.sh`
- optional hook scripts and installer under `codex/hooks/`

## Codex Install

From this repository:

```bash
bash codex/agents/sync-agents.sh --dry-run
bash codex/agents/sync-agents.sh --apply
```

Restart Codex if updated agent instructions are not visible.

The repo-local skills are available when Codex runs from this repository or a subdirectory:

```text
.agents/skills/orchestrate-workflow/SKILL.md
.agents/skills/orchestrate-plan-writing/SKILL.md
```

To use the workflow from every project, install the skills into the user-level skills directory:

```bash
bash codex/skills/install-orchestrate-workflow.sh --user --dry-run
bash codex/skills/install-orchestrate-workflow.sh --user --apply
```

Only vendor the skills into a specific target repo when that repo should carry its own copy:

```bash
bash codex/skills/install-orchestrate-workflow.sh --target-repo /path/to/repo --dry-run
bash codex/skills/install-orchestrate-workflow.sh --target-repo /path/to/repo --apply
```

Do not keep duplicate copies of the same skill in repo-local, user-level, and plugin-installed locations at the same time. Duplicate skill names make invocation ambiguous.

## Codex Usage

Standard workflow:

```text
orchestrate-discovery
  -> design document
  -> Phase 0a design review
  -> upstream to-issues for vertical large issues and vertical small issues
  -> orchestrate-plan-writing for issue-backed implementation plan
  -> orchestrate-workflow for Phase 0b / Task Pack execution
  -> Phase B / Phase C
```

`orchestrate-workflow` starts at discovery handoff, design review, plan review, Phase A repair, existing diff review, or final business reporting. It handles:

- design handoff from `orchestrate-discovery`
- Phase 0a design review
- Phase 0b plan review
- Task Pack planning and execution
- pack review and repair loops
- final intent verification
- release-risk review when migrations, billing, permissions, runtime, deploy, rollback, or cross-service contracts are involved
- business report

Runtime review contracts live in `.agents/skills/orchestrate-workflow/references/`. They tell the parent coordinator what to include in dispatch prompts for Codex `agent_type`s.

`orchestrate-discovery` turns new features, issues, backlog items, existing PRD docs, systemic bugs, wrong states, performance regressions, UI / UX feedback, screenshots, test feedback, and product discussions into reviewable design documents. During Discovery, `grill-with-docs` is used as continuous domain alignment; diagnosis, prototype, architecture, zoom-out, and triage outputs must be written back into the design document or domain docs before Phase 0a.

`orchestrate-plan-writing` generates plans from reviewed source design and `to-issues` output. In generated plans, top-level sections map to vertical large issues, Task Packs map to vertical small issues, and fine-grained tasks live inside each pack. If large or small issues are missing, it routes back to `to-issues` instead of finalizing a plan.

External engineering skills from `mattpocock/skills` are active upstream methods. Orchestrate routes to them for domain alignment, feedback-loop diagnosis, vertical-slice TDD, prototype decisions, issue slicing, triage state, and architecture findings, then folds their outputs back into the Codex phases.

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
