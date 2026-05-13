# multi-model-workflow

Claude Code plugin. Agent specialization + Task Pack batching + automated review loops, layered on top of [Superpowers](https://github.com/obra/superpowers).

## What It Does

Replaces Superpowers' `subagent-driven-development` with a multi-agent orchestration system:

- **4 specialized agents** — architect (plans), implementer (codes), reviewer (audits), debugger (investigates)
- **Task Pack batching** — groups fine-grained tasks (2-5 min each) into packs of 2-5 for efficient dispatch, independent packs run in parallel
- **Automated review loops** — every output gets reviewed; issues auto-routed to the right agent for fixing
- **Hub-and-spoke coordination** — main session orchestrates all agents, uses SendMessage for context-preserving fix loops

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- [Superpowers plugin](https://github.com/obra/superpowers) installed

This plugin depends on Superpowers for methodology (TDD, systematic debugging, writing plans, etc.). Agents reference Superpowers skills in their instructions.

## Install

```bash
# From GitHub
claude plugin add chancheuklap/multi-model-workflow

# Or from local directory (development)
claude --plugin-dir /path/to/multi-model-workflow
```

## Usage

The plugin integrates into the standard Superpowers workflow:

```
1. Describe feature → superpowers:brainstorming (main session)
2. Confirm direction → architect writes design + plan
3. Say "execute the plan" → multi-model-workflow:execute-plan
4. Say "merge" → superpowers:finishing-a-development-branch
```

The `execute-plan` skill handles everything between plan and merge:

- **Phase 0** — Document review (grep-verifies all references)
- **Phase A** — Task Pack execution + combined spec/quality review per pack
- **Phase B** — Final intent verification against design doc
- **Phase C** — Business-language report

Technical issues are resolved autonomously. You're only asked about business decisions.

## Agents

| Agent | Role | Tools |
|-------|------|-------|
| **architect** | Design docs + implementation plans | Read, Grep, Glob, Bash, Write (no Edit) |
| **implementer** | TDD code execution + review fix | Read, Edit, Write, Bash, Grep, Glob |
| **reviewer** | Read-only audit + issue routing | Read, Grep, Glob, Bash (no Edit/Write) |
| **debugger** | Unknown root cause investigation | Read, Edit, Write, Bash, Grep, Glob |

## Hooks

| Hook | Trigger | Effect |
|------|---------|--------|
| SessionStart | Every session | Injects routing context |
| PreToolUse/Bash | `git push`, `git merge`, `gh pr create` | Blocks if plan has unchecked tasks |
| SubagentStop | implementer completes | Reminds to dispatch reviewer |

## Architecture

```
multi-model-workflow/
├── .claude-plugin/plugin.json
├── agents/
│   ├── architect.md
│   ├── implementer.md
│   ├── debugger.md
│   └── reviewer.md
├── skills/
│   └── execute-plan/
│       ├── SKILL.md
│       ├── doc-review-prompt.md
│       ├── pack-review-prompt.md
│       └── final-intent-review-prompt.md
├── hooks/
│   ├── hooks.json
│   └── routing-context.txt
└── scripts/
    └── guard-premature-push.sh
```

## License

MIT
