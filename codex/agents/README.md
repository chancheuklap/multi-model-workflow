# Codex Agent Templates

Sync templates to `~/.codex/agents/`:

```bash
bash codex/agents/sync-agents.sh --dry-run
bash codex/agents/sync-agents.sh --apply
```

## Agents

| Agent | Model | Sandbox | Role |
| --- | --- | --- | --- |
| `coding_worker` | gpt-5.3-codex | workspace-write | 普通 Task Pack / 测试修复 / 局部重构 |
| `complex_coding_worker` | gpt-5.5 | workspace-write | 高风险 Task Pack（migration / billing / auth / permission / runtime / shared contract） |
| `code_reviewer` | gpt-5.4 | read-only | Baseline review（design / plan / pack / final intent） |
| `release_reviewer` | gpt-5.5 | read-only | Release-risk gate（数据 / 权限 / 账务 / 迁移 / 部署 / 回滚） |
| `code_explorer` | gpt-5.3-codex | read-only | 窄范围文件 / 符号 / 调用链查询 |
| `complex_code_explorer` | gpt-5.4 | read-only | 多模块调查 / root-cause investigation |
| `docs_worker` | gpt-5.4 | workspace-write | 低风险文档整理 / issue 文案草稿 |

## Key Contracts

- Sub-agent 不读 Orchestrate SKILL.md 或 references。Parent dispatch prompt 必须自足。
- 所有 sub-agent 按 parent dispatch 指定的 Return Contract 和 Routing Vocabulary 返回。
- Return Contract 和 Finding Shape 的权威定义在 `orchestrate-workflow/references/dispatch-contract.md`。
