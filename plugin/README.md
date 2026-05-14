# multi-model-workflow

Claude Code plugin. Task Pack batching + automated review loops + 3 specialized agents, layered on top of [Superpowers](https://github.com/obra/superpowers).

## What It Does

Replaces Superpowers' `subagent-driven-development` with a multi-agent orchestration system:

- **3 specialized agents** — pack-executor (codes), workflow-auditor (audits), root-cause-analyst (investigates)
- **Main session as coordinator** — writes plans (via writing-plans), fixes plan issues (full context), orchestrates all agents
- **Task Pack batching** — groups fine-grained tasks (2-5 min each) into packs of 2-5 for efficient dispatch, independent packs run in parallel
- **Automated review loops** — every output gets reviewed; issues auto-routed to the right agent for fixing
- **Project-aware auditing** — agents respect project-level CLAUDE.md engineering rules and conventions

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- [Superpowers plugin](https://github.com/obra/superpowers) installed

This plugin depends on Superpowers for methodology (TDD, systematic debugging, writing plans, etc.). Agents reference Superpowers skills in their instructions.

## Install

```bash
# From GitHub
claude plugin install multi-model-workflow@multi-model-workflow

# Or from local directory (development)
claude --plugin-dir /path/to/multi-model-workflow/plugin
```

## Usage

The plugin integrates into the standard Superpowers workflow:

```
1. Describe feature → superpowers:brainstorming (main session)
2. Confirm direction → main session writes design + plan (via superpowers:writing-plans)
3. Design doc produced → multi-model-workflow:orchestrate-workflow takes over (Phase 0a onward)
4. Say "merge" → superpowers:finishing-a-development-branch
```

The `orchestrate-workflow` skill spans the ENTIRE workflow from "design document produced" through code completion — it is NOT limited to the code execution phase:

- **Phase 0a** — Design document review (parallel multi-auditor: project alignment + content quality)
- **Phase 0b** — Plan document review (multi-auditor + Codex second-opinion)
- **Phase A** — Task Pack execution + combined spec/quality review per pack
- **Phase B** — Final intent verification against design doc (workflow-auditor + Codex cross-check)
- **Phase C** — Business-language report

Technical issues are resolved autonomously by sub-agents; you're only asked about business decisions.

## Agents

| Agent | Role | Tools |
|-------|------|-------|
| **pack-executor** | TDD code execution + review fix | Read, Edit, Write, Bash, Grep, Glob |
| **workflow-auditor** | Read-only multi-phase audit + issue routing | Read, Grep, Glob, Bash (no Edit/Write) |
| **root-cause-analyst** | Unknown root cause investigation | Read, Edit, Write, Bash, Grep, Glob |

Plan writing and plan fixes are handled by the main session (coordinator), which has the richest context from brainstorming and user interaction.

## Hooks

| Hook | Trigger | Effect |
|------|---------|--------|
| SessionStart | Every session | Injects behavioral override rules (writing-plans → orchestrate-workflow chain) |
| PreToolUse/Bash | `git push`, `git merge`, `gh pr create` | Blocks if plan has unchecked tasks |
| SubagentStop | pack-executor completes | Reminds to dispatch workflow-auditor |

## Architecture

```
multi-model-workflow/
├── .claude-plugin/plugin.json
├── agents/
│   ├── pack-executor.md
│   ├── root-cause-analyst.md
│   └── workflow-auditor.md
├── skills/
│   └── orchestrate-workflow/
│       ├── SKILL.md
│       ├── design-review-content-prompt.md
│       ├── design-review-alignment-prompt.md
│       ├── plan-review-coverage-prompt.md
│       ├── plan-review-compliance-prompt.md
│       ├── plan-review-codex-prompt.md
│       ├── pack-review-prompt.md
│       ├── final-intent-review-prompt.md
│       └── final-review-codex-prompt.md
├── hooks/
│   ├── hooks.json
│   └── session-start.sh
└── scripts/
    └── guard-premature-push.sh
```

## License

MIT
