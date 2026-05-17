# multi-model-workflow

Claude Code plugin. Multi-model orchestration: Claude agents for coding + Codex agents for independent review. Task Pack batching, automated review loops, worktree isolation.

For Codex-native use, see the repository root:

- `.agents/skills/orchestrate-*/`
- `codex/agents/*.toml`

## What It Does

Multi-agent orchestration system with cross-model review:

- **6 specialized Claude agents** — pack-executor / complex-pack-executor (code), code-explorer / complex-code-explorer (investigation), root-cause-analyst (unknown root cause + fix), docs-worker (documentation)
- **Codex for all reviews** — every review is dispatched to Codex via `codex:codex-rescue` for independent cross-model opinion (GPT-5.4 baseline, GPT-5.5 release gate)
- **Main session as coordinator** — orchestrates all agents, fixes plan/design docs directly (full user context)
- **Task Pack batching** — groups fine-grained tasks (2-5 min each) into packs of 2-5 for efficient dispatch
- **Worktree isolation** — parallel packs execute in independent git worktrees, changes auto-merge back
- **Project-aware** — agents read CLAUDE.md engineering rules and conventions, persist learnings via memory

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- [Codex plugin](https://github.com/anthropics/claude-code-plugins) — provides `codex:codex-rescue` for cross-model review dispatch

## Install

```bash
claude plugin install multi-model-workflow@multi-model-workflow
```

## Usage

```
1. Discuss requirements with coordinator
2. orchestrate-discovery produces design document
3. orchestrate-plan-writing writes implementation plan
4. orchestrate-workflow takes over (Phase 0a onward)
```

### Phases

- **Phase 0a** — Design document review (2 parallel Codex reviews: content quality + project alignment)
- **Phase 0b** — Plan document review (3 parallel Codex reviews: coverage + compliance + cross-verification)
- **Phase A** — Task Pack execution (Claude) + pack review (Codex) per pack
- **Phase B** — Final intent verification (2 parallel Codex reviews: intent + code-level)
- **Phase C** — Business-language report

Technical issues are resolved autonomously by agents; you're only asked about business decisions.

## Agents

| Agent | Model | Role | Key Skills |
|-------|-------|------|------------|
| **pack-executor** | Sonnet | Normal TDD coding + review fix | `tdd`, `diagnose` |
| **complex-pack-executor** | Opus | High-risk coding (migrations, billing, auth, permissions) | `tdd`, `diagnose`, `improve-codebase-architecture` |
| **code-explorer** | Sonnet | Narrow-scope file/symbol investigation (read-only) | — |
| **complex-code-explorer** | Opus | Multi-module investigation (read-only) | `diagnose`, `improve-codebase-architecture`, `grill-with-docs` |
| **root-cause-analyst** | Opus | Unknown root cause investigation + fix | `diagnose`, `tdd` |
| **docs-worker** | Sonnet | Low-risk documentation cleanup | `grill-with-docs` |

All reviews are dispatched to **Codex** (GPT-5.4 for baseline, GPT-5.5 for release gate) via `codex:codex-rescue`.

## Hooks

| Hook | Trigger | Effect |
|------|---------|--------|
| SessionStart | Every session | Injects orchestrate chain rules and agent role summary |
| PreToolUse/Bash | `git push`, `git merge`, `gh pr create` | Blocks if plan has unchecked tasks |
| SubagentStop | pack-executor / complex-pack-executor | Reminds to dispatch Codex review |

## Architecture

```
plugin/
├── .claude-plugin/plugin.json
├── agents/
│   ├── pack-executor.md
│   ├── complex-pack-executor.md
│   ├── code-explorer.md
│   ├── complex-code-explorer.md
│   ├── root-cause-analyst.md
│   └── docs-worker.md
├── skills/
│   ├── orchestrate-workflow/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── dispatch-contract.md
│   │       ├── design-review.md
│   │       ├── plan-review.md
│   │       ├── implementation-review.md
│   │       ├── final-review.md
│   │       └── contract-boundary.md
│   ├── orchestrate-discovery/
│   │   ├── SKILL.md
│   │   └── references/
│   └── orchestrate-plan-writing/
│       ├── SKILL.md
│       └── references/
├── hooks/
│   ├── hooks.json
│   └── session-start.sh
└── scripts/
    └── guard-premature-push.sh
```

## License

MIT
